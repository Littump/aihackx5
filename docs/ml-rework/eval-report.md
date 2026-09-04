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
| treatment_llm | 66.77 | 75.62 | 7.35 | 0.86 | 0.36 | 0.84 | 0.64 | 0.44 |
| treatment_rules | 76.68 | 88.68 | 10.5 | 1.0 | 0.4 | 0.98 | 0.28 | 0.0 |

**Business-metric uplift (treatment_llm − control_x5): 10.0 pp**

_Run with `--null` to check the zero-uplift invariant._
