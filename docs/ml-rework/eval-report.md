# ML planner eval report

- model: `/opt/Qwen/Qwen3.8-27B-FP8`
- seed: 7, profiles: 16
- horizon: 12 weeks, cut point T: week 6
- null_test: False
- business metric: share with >= 8 purchases in 4 weeks

| branch | net_effect ₽ | incr.margin ₽ | reward cost ₽ | incr.visits | biz-metric share | completion | relevance hit | llm plans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| control_x5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1875 | 0.0 | 0.0 | 0.0 |
| treatment_llm | 51.38 | 55.23 | 2.34 | 0.625 | 0.3125 | 0.5 | 0.9375 | 1.0 |
| treatment_rules | 35.97 | 42.63 | 5.16 | 0.5 | 0.25 | 0.5 | 0.1875 | 0.0 |

**Business-metric uplift (treatment_llm − control_x5): 12.5 pp**

_Run with `--null` to check the zero-uplift invariant._
