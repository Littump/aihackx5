import asyncio

from app.ml import eval as eval_module


def _run_null() -> eval_module.EvalReport:
    settings = eval_module.EvalSettings(
        seed=7,
        profile_count=10,
        horizon_weeks=12,
        cut_week=6,
        model="test",
        null_test=True,
    )
    return asyncio.run(eval_module.run_eval(None, settings))


def test_null_test_tails_are_identical_across_branches() -> None:
    report = _run_null()
    for result in report.results:
        tails = {branch.tail_visits for branch in result.branches.values()}
        incrementals = {branch.incremental_visits for branch in result.branches.values()}
        assert incrementals == {0}
        assert len(tails) == 1


def test_null_test_net_effect_non_positive() -> None:
    report = _run_null()
    for aggregate in report.aggregates.values():
        assert aggregate.avg_net_effect_rub <= 0
    assert report.business_metric_uplift_pp == 0.0
