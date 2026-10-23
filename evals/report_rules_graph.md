# Eval report (rule-based extractor)

Sample data, fictional. k = 5 chunks. 39 labelled questions.

## All questions

| Retriever | n | recall@5 | full@5 | MRR | fact@5 |
|---|---|---|---|---|---|
| vector | 39 | 0.833 | 0.692 | 0.889 | 0.846 |
| graph | 39 | 0.923 | 0.846 | 0.894 | 0.615 |
| hybrid | 39 | 0.885 | 0.769 | 0.894 | 0.692 |

## Single-hop

| Retriever | n | recall@5 | full@5 | MRR | fact@5 |
|---|---|---|---|---|---|
| vector | 16 | 1.000 | 1.000 | 1.000 | 1.000 |
| graph | 16 | 1.000 | 1.000 | 1.000 | 0.688 |
| hybrid | 16 | 1.000 | 1.000 | 1.000 | 0.875 |

## Multi-hop

| Retriever | n | recall@5 | full@5 | MRR | fact@5 |
|---|---|---|---|---|---|
| vector | 23 | 0.717 | 0.478 | 0.812 | 0.739 |
| graph | 23 | 0.870 | 0.739 | 0.820 | 0.565 |
| hybrid | 23 | 0.804 | 0.609 | 0.820 | 0.565 |

