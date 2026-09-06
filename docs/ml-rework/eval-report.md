# ML planner eval report

- planner model: `qwen38-27b-fp8`
- actor model: `MiniMaxAI/MiniMax-M3-MXFP8`
- seed: 7, profiles: 50
- horizon: 12 weeks, cut point T: week 6
- null_test: False
- high_margin_mandate: True
- business metric: share with >= 8 purchases in 4 weeks

> ⚠️ УСТАРЕЛО: цифры ниже сняты на ОДНОРАЗОВОЙ модели челленджа (оффер только в точке T,
> недели T+1.. проматывались по baseline). После перехода на многонедельный адаптивный
> цикл (планировщик переигрывает стратегию каждую неделю T(cut..horizon), получая на вход
> `previous_plans` — свои прошлые офферы и реакцию покупателя) таблицу нужно пересчитать
> полным прогоном seed=7 / 50 профилей (команда — в разделе «ML eval» AGENTS.md). До этого
> прогона числа не отражают текущий код.

| branch | net_effect ₽ | incr.margin ₽ | reward cost ₽ | incr.visits | biz-metric share | completion | relevance hit | high-margin | llm plans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| control_x5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.2 | 0.04 | 0.0 | 0.0 | 0.0 |
| treatment_llm | 0.19 | 2.14 | 0.45 | 0.02 | 0.2 | 0.02 | 0.52 | 1.0 | 1.0 |
| treatment_rules | -1.5 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 0.36 | 1.0 | 0.0 |

**Business-metric uplift (treatment_llm − control_x5): 0.0 pp**

_Run with `--null` to check the zero-uplift invariant._
