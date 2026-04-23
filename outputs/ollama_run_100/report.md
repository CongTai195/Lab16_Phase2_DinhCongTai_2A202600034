# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json
- Mode: llama3
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.83 | 0.94 | 0.11 |
| Avg attempts | 1 | 1.23 | 0.23 |
| Avg token estimate | 1816.8 | 2651.89 | 835.09 |
| Avg latency (ms) | 18881.64 | 25418.44 | 6536.8 |

## Failure modes
```json
{
  "react": {
    "none": 83,
    "wrong_final_answer": 17
  },
  "reflexion": {
    "none": 94,
    "reflection_overfit": 6
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
Reflexion helps when the first attempt stops after the first hop or drifts to a wrong second-hop entity. The tradeoff is higher attempts, token cost, and latency. In a real report, students should explain when the reflection memory was useful, which failure modes remained, and whether evaluator quality limited gains.
