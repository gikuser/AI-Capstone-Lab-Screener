# Evaluation Report - Lab 7

## Quantitative Metrics (RAGAS Style)

| Metric | Average Score | Status |
| :--- | :--- | :--- |
| **Faithfulness** | 0.92 | ✅ PASS |
| **Answer Relevancy** | 0.88 | ✅ PASS |
| **Tool Call Accuracy** | 1.00 | ✅ PASS |

## Observations
- The **Faithfulness** score is high because of the RAG grounding which prevents hallucinations about corporate policy.
- **Answer Relevancy** slightly dips when the query is highly ambiguous, but still stays well above the 0.8 threshold.
- The **Researcher** agent always calls the scoring tool correctly before handing over to the Analyst.

## Evaluation Methodology
- **LLM-as-a-Judge**: Gemini-3-Flash was used as an impartial evaluator to score agent responses against the Gold Dataset.
- **Gold Dataset**: 20 pairs of query-truth mappings were used to ensure broad coverage of HR policies and edge cases.
