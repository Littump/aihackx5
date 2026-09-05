import asyncio
from pathlib import Path

from app.ml import eval as eval_module
from app.ml import langfuse_export, tracing


def _run_with_recorder(tmp_path: Path) -> tracing.TraceRecorder:
    settings = eval_module.EvalSettings(
        seed=7,
        profile_count=4,
        horizon_weeks=12,
        cut_week=6,
        planner_model="test-planner",
        actor_model="test-actor",
        null_test=True,
    )
    header = tracing.EvalRunHeader(
        seed=7,
        profiles=4,
        horizon_weeks=12,
        cut_week=6,
        planner_model="test-planner",
        actor_model="test-actor",
        null_test=True,
        no_llm=True,
    )
    recorder = tracing.TraceRecorder(header)
    asyncio.run(eval_module.run_eval(None, settings, recorder))
    return recorder


def test_recorder_captures_one_trace_per_profile_with_three_branches(tmp_path: Path) -> None:
    recorder = _run_with_recorder(tmp_path)
    traces = recorder.profiles()
    assert len(traces) == 4
    for trace in traces:
        branches = {branch.branch for branch in trace.branches}
        assert branches == {"control_x5", "treatment_llm", "treatment_rules"}
        for branch in trace.branches:
            assert branch.decision.source == "null"
            assert branch.decision.promo_decision == "ignore"
            assert branch.decision.engaged is False


def test_traces_roundtrip_through_jsonl(tmp_path: Path) -> None:
    recorder = _run_with_recorder(tmp_path)
    path = tmp_path / "traces.jsonl"
    path.write_text(recorder.to_jsonl(), encoding="utf-8")
    loaded = langfuse_export.read_trace_file(path)
    assert loaded.header.no_llm is True
    assert len(loaded.profiles) == 4
    ids = [profile.snapshot.profile_id for profile in loaded.profiles]
    assert ids == sorted(ids)
