# Eval report (rule-based extractor graph, LLM answers (qwen/qwen3.8-27b via Groq))

Sample data, fictional. k = 5 chunks. 31 labelled questions.

## All questions

| Retriever | n | recall@5 | full@5 | MRR | fact@5 | answer_fact |
|---|---|---|---|---|---|---|
| vector | 31 | 0.839 | 0.677 | 0.901 | 0.871 | 0.935 |
| graph | 31 | 0.952 | 0.903 | 0.901 | 0.645 | 0.839 |
| hybrid | 31 | 0.887 | 0.774 | 0.901 | 0.742 | 0.903 |

## Single-hop

| Retriever | n | recall@5 | full@5 | MRR | fact@5 | answer_fact |
|---|---|---|---|---|---|---|
| vector | 12 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| graph | 12 | 1.000 | 1.000 | 1.000 | 0.750 | 0.750 |
| hybrid | 12 | 1.000 | 1.000 | 1.000 | 0.917 | 0.917 |

## Multi-hop

| Retriever | n | recall@5 | full@5 | MRR | fact@5 | answer_fact |
|---|---|---|---|---|---|---|
| vector | 19 | 0.737 | 0.474 | 0.838 | 0.789 | 0.895 |
| graph | 19 | 0.921 | 0.842 | 0.838 | 0.579 | 0.895 |
| hybrid | 19 | 0.816 | 0.632 | 0.838 | 0.632 | 0.895 |

