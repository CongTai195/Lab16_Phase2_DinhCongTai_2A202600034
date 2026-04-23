from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord, JudgeResult
from .llm import LLMClient
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    model: str = "llama3"
    max_attempts: int = 1
    
    def __post_init__(self):
        self.llm = LLMClient(model=self.model)

    def _get_actor_answer(self, example: QAExample, reflection_memory: list[str]) -> tuple[str, int, float]:
        context_str = "\n\n".join([f"Source: {c.title}\nContent: {c.text}" for c in example.context])
        prompt = f"Context:\n{context_str}\n\nQuestion: {example.question}"
        
        if reflection_memory:
            reflections = "\n".join([f"- {r}" for r in reflection_memory])
            prompt += f"\n\nPrevious Reflections:\n{reflections}"
            
        messages = [
            {"role": "system", "content": ACTOR_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        return self.llm.chat(messages)

    def _evaluate(self, example: QAExample, answer: str) -> tuple[JudgeResult, int, float]:
        prompt = f"Question: {example.question}\nGold Answer: {example.gold_answer}\nPredicted Answer: {answer}"
        messages = [
            {"role": "system", "content": EVALUATOR_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        return self.llm.structured_chat(messages, JudgeResult)

    def _reflect(self, example: QAExample, attempt_id: int, answer: str, judge: JudgeResult) -> tuple[ReflectionEntry, int, float]:
        prompt = f"Question: {example.question}\nContext: {example.context}\nFailed Answer: {answer}\nFailure Reason: {judge.reason}"
        messages = [
            {"role": "system", "content": REFLECTOR_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        reflection_data, tokens, latency = self.llm.structured_chat(messages, ReflectionEntry)
        reflection_data.attempt_id = attempt_id
        return reflection_data, tokens, latency

    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        total_tokens = 0
        total_latency = 0

        for attempt_id in range(1, self.max_attempts + 1):
            # 1. Actor generate answer
            answer, tokens_act, lat_act = self._get_actor_answer(example, reflection_memory)
            total_tokens += tokens_act
            total_latency += lat_act
            
            # 2. Evaluator judge answer
            judge, tokens_eval, lat_eval = self._evaluate(example, answer)
            total_tokens += tokens_eval
            total_latency += lat_eval
            
            final_answer = answer
            final_score = judge.score
            
            trace = AttemptTrace(
                attempt_id=attempt_id,
                answer=answer,
                score=judge.score,
                reason=judge.reason,
                token_estimate=tokens_act + tokens_eval,
                latency_ms=lat_act + lat_eval
            )
            
            if judge.score == 1:
                traces.append(trace)
                break
            
            # 3. Reflector (only if reflexion and not last attempt)
            if self.agent_type == "reflexion" and attempt_id < self.max_attempts:
                reflection, tokens_ref, lat_ref = self._reflect(example, attempt_id, answer, judge)
                total_tokens += tokens_ref
                total_latency += lat_ref
                
                reflections.append(reflection)
                reflection_memory.append(f"Lesson: {reflection.lesson}. Strategy: {reflection.next_strategy}")
                trace.reflection = reflection
                trace.token_estimate += tokens_ref
                trace.latency_ms += lat_ref

            traces.append(trace)

        failure_mode = "none" if final_score == 1 else "wrong_final_answer"
        # Optional: heuristic for other failure modes
        if final_score == 0 and self.agent_type == "reflexion" and len(traces) == self.max_attempts:
            failure_mode = "reflection_overfit" # simplified

        return RunRecord(
            qid=example.qid,
            question=example.question,
            gold_answer=example.gold_answer,
            agent_type=self.agent_type,
            predicted_answer=final_answer,
            is_correct=bool(final_score),
            attempts=len(traces),
            token_estimate=total_tokens,
            latency_ms=total_latency,
            failure_mode=failure_mode,
            reflections=reflections,
            traces=traces
        )

class ReActAgent(BaseAgent):
    def __init__(self, model: str = "llama3") -> None:
        super().__init__(agent_type="react", model=model, max_attempts=1)

class ReflexionAgent(BaseAgent):
    def __init__(self, model: str = "llama3", max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", model=model, max_attempts=max_attempts)
