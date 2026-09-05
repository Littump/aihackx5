# ML planner eval report

- planner model: `qwen38-27b-fp8`
- actor model: `deepseek-v4-flash`
- seed: 7, profiles: 50
- horizon: 12 weeks, cut point T: week 6
- null_test: False
- business metric: share with >= 8 purchases in 4 weeks

| branch | net_effect ₽ | incr.margin ₽ | reward cost ₽ | incr.visits | biz-metric share | completion | relevance hit | llm plans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| control_x5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 0.0 | 0.0 |
| treatment_llm | 3.14 | 5.69 | 1.05 | 0.08 | 0.2 | 0.18 | 0.98 | 1.0 |
| treatment_rules | -0.24 | 1.41 | 0.15 | 0.02 | 0.2 | 0.02 | 0.26 | 0.0 |

**Business-metric uplift (treatment_llm − control_x5): 0.0 pp**

_Run with `--null` to check the zero-uplift invariant._
