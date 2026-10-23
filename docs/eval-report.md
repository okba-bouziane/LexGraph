# Eval report (rule-based extractor)

Sample data, fictional. k = 5 chunks. 39 labelled questions.

## All questions

| Retriever | n | recall@5 | full@5 | MRR | fact@5 |
|---|---|---|---|---|---|
| vector | 39 | 0.859 | 0.744 | 0.912 | 0.821 |
| graph | 39 | 0.885 | 0.795 | 0.912 | 0.615 |
| hybrid | 39 | 0.885 | 0.795 | 0.912 | 0.692 |

## Single-hop

| Retriever | n | recall@5 | full@5 | MRR | fact@5 |
|---|---|---|---|---|---|
| vector | 16 | 1.000 | 1.000 | 1.000 | 1.000 |
| graph | 16 | 1.000 | 1.000 | 1.000 | 0.750 |
| hybrid | 16 | 1.000 | 1.000 | 1.000 | 0.875 |

## Multi-hop

| Retriever | n | recall@5 | full@5 | MRR | fact@5 |
|---|---|---|---|---|---|
| vector | 23 | 0.761 | 0.565 | 0.851 | 0.696 |
| graph | 23 | 0.804 | 0.652 | 0.851 | 0.522 |
| hybrid | 23 | 0.804 | 0.652 | 0.851 | 0.565 |

