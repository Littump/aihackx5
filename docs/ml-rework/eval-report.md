# ML planner eval report

- model: `/opt/Qwen/Qwen3.8-27B-FP8`
- seed: 7, profiles: 50
- horizon: 12 weeks, cut point T: week 6
- null_test: False
- business metric: share with >= 8 purchases in 4 weeks

| branch | net_effect ₽ | incr.margin ₽ | reward cost ₽ | incr.visits | biz-metric share | completion | relevance hit | llm plans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| control_x5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.26 | 0.0 | 0.0 | 0.0 |
| treatment_llm | 50.39 | 55.19 | 3.3 | 0.62 | 0.38 | 0.4 | 0.94 | 1.0 |
| treatment_rules | 35.18 | 42.98 | 6.3 | 0.5 | 0.32 | 0.48 | 0.28 | 0.0 |

**Business-metric uplift (treatment_llm − control_x5): 12.0 pp**

_Run with `--null` to check the zero-uplift invariant._
