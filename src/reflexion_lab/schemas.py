from __future__ import annotations
from typing import Literal, Optional, TypedDict
from pydantic import BaseModel, Field

class ContextChunk(BaseModel):
    title: str
    text: str

class QAExample(BaseModel):
    qid: str
    difficulty: Literal["easy", "medium", "hard"]
    question: str
    gold_answer: str
    context: list[ContextChunk]

class JudgeResult(BaseModel):
    score: int = Field(description="Đánh giá 1 nếu đúng, 0 nếu sai")
    reason: str = Field(description="Giải thích lý do tại sao đúng hoặc sai")
    missing_evidence: list[str] = Field(default_factory=list, description="Các thông tin còn thiếu từ ngữ cảnh")
    spurious_claims: list[str] = Field(default_factory=list, description="Các thông tin sai lệch hoặc không có trong ngữ cảnh")

class ReflectionEntry(BaseModel):
    attempt_id: int = Field(description="Thứ tự của lần thử")
    failure_reason: str = Field(description="Lý do thất bại của lần thử trước")
    lesson: str = Field(description="Bài học rút ra từ lỗi sai")
    next_strategy: str = Field(description="Chiến thuật cho lần thử tiếp theo")

class AttemptTrace(BaseModel):
    attempt_id: int
    answer: str
    score: int
    reason: str
    reflection: Optional[ReflectionEntry] = None
    token_estimate: int = 0
    latency_ms: float = 0.0

class RunRecord(BaseModel):
    qid: str
    question: str
    gold_answer: str
    agent_type: Literal["react", "reflexion"]
    predicted_answer: str
    is_correct: bool
    attempts: int
    token_estimate: int
    latency_ms: float
    failure_mode: Literal["none", "entity_drift", "incomplete_multi_hop", "wrong_final_answer", "looping", "reflection_overfit"]
    reflections: list[ReflectionEntry] = Field(default_factory=list)
    traces: list[AttemptTrace] = Field(default_factory=list)

class ReportPayload(BaseModel):
    meta: dict
    summary: dict
    failure_modes: dict
    examples: list[dict]
    extensions: list[str]
    discussion: str

class ReflexionState(TypedDict):
    question: str
    context: list[str]
    trajectory: list[str]
    reflection_memory: list[str]
    attempt_count: int
    success: bool
    final_answer: str
