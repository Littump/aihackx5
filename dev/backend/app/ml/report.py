from app.ml.schemas import EvalReport

_BRANCH_ORDER = ("control_x5", "treatment_llm", "treatment_rules")


def render_markdown(report: EvalReport) -> str:
    lines: list[str] = []
    lines.append("# ML planner eval report")
    lines.append("")
    lines.append(f"- planner model: `{report.planner_model}`")
    lines.append(f"- actor model: `{report.actor_model}`")
    lines.append(f"- seed: {report.seed}, profiles: {report.profiles}")
    lines.append(f"- horizon: {report.horizon_weeks} weeks, cut point T: week {report.cut_week}")
    lines.append(f"- null_test: {report.null_test}")
    lines.append(
        f"- business metric: share with >= {report.business_metric_purchases} purchases "
        f"in {report.business_metric_window_weeks} weeks"
    )
    lines.append("")
    lines.append(
        "| branch | net_effect ₽ | incr.margin ₽ | reward cost ₽ | incr.visits | "
        "biz-metric share | completion | relevance hit | llm plans |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for name in _BRANCH_ORDER:
        row = report.aggregates[name]
        lines.append(
            f"| {name} | {row.avg_net_effect_rub} | {row.avg_incremental_margin_rub} | "
            f"{row.avg_reward_cost_rub} | {row.avg_incremental_visits} | "
            f"{row.business_metric_share} | {row.completion_rate} | "
            f"{row.relevance_hit_rate} | {row.plan_source_llm_share} |"
        )
    lines.append("")
    lines.append(
        f"**Business-metric uplift (treatment_llm − control_x5): "
        f"{report.business_metric_uplift_pp} pp**"
    )
    lines.append("")
    lines.append(_null_test_line(report))
    return "\n".join(lines) + "\n"


def _null_test_line(report: EvalReport) -> str:
    if not report.null_test:
        return "_Run with `--null` to check the zero-uplift invariant._"
    treatment = report.aggregates["treatment_llm"]
    control = report.aggregates["control_x5"]
    tails_equal = treatment.avg_incremental_visits == 0 and control.avg_incremental_visits == 0
    net_non_positive = treatment.avg_net_effect_rub <= 0 and control.avg_net_effect_rub <= 0
    verdict = "PASS" if tails_equal and net_non_positive else "FAIL"
    return f"**Null test {verdict}**: incremental visits = 0 across branches and net_effect <= 0."
