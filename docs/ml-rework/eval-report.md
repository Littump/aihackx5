# ML planner eval report

- planner model: `qwen38-27b-fp8`
- actor model: `deepseek-v4-flash`
- seed: 7, profiles: 50
- horizon: 12 weeks, cut point T: week 6
- null_test: False
- business metric: share with >= 8 purchases in 4 weeks

| branch | net_effect ₽ | incr.margin ₽ | reward cost ₽ | incr.visits | biz-metric share | completion | relevance hit | llm plans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| control_x5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.26 | 0.0 | 0.0 | 0.0 |
| treatment_llm | 53.86 | 61.51 | 6.15 | 0.72 | 0.38 | 0.68 | 0.92 | 0.98 |
| treatment_rules | 75.4 | 87.1 | 10.2 | 0.98 | 0.38 | 0.96 | 0.28 | 0.0 |

**Business-metric uplift (treatment_llm − control_x5): 12.0 pp**

_Run with `--null` to check the zero-uplift invariant._
