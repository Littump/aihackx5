import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

from app.ml import capacity as capacity_module
from app.ml import catalog as catalog_module
from app.ml import config, langfuse_export, tracing
from app.ml import eval as eval_module
from app.ml import iteration_summary as iteration_summary_module
from app.ml import judge as judge_module
from app.ml import llm_client as llm_client_module
from app.ml import persona as persona_module
from app.ml import profiles as profiles_module
from app.ml import report as report_module
from app.ml.llm_client import ChatClient
from app.ml.schemas import EvalReport


def main() -> None:
    parser = argparse.ArgumentParser(description="ML LLM-planner module CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    catalog_cmd = sub.add_parser("gen-catalog", help="export the real X5 SKU catalog")
    catalog_cmd.add_argument("--seed", type=int, default=7)
    catalog_cmd.add_argument("--out", type=Path, default=Path("build/sku_catalog.json"))

    profiles_cmd = sub.add_parser("gen-profiles", help="generate synthetic user profiles")
    profiles_cmd.add_argument("--seed", type=int, default=7)
    profiles_cmd.add_argument("--count", type=int, default=200)
    profiles_cmd.add_argument("--out", type=Path, default=Path("build/user_profiles.json"))

    personas_cmd = sub.add_parser(
        "gen-personas", help="generate human buyer personas for profiles via the persona LLM"
    )
    personas_cmd.add_argument("--seed", type=int, default=7)
    personas_cmd.add_argument("--count", type=int, default=12)
    personas_cmd.add_argument("--concurrency", type=int, default=config.PERSONA_MAX_CONCURRENCY)
    personas_cmd.add_argument("--persona-base-url", type=str, default=None)
    personas_cmd.add_argument("--persona-model", type=str, default=None)
    personas_cmd.add_argument("--out", type=Path, default=Path("build/personas.json"))

    eval_cmd = sub.add_parser("run-eval", help="run the counterfactual eval once")
    eval_cmd.add_argument("--seed", type=int, default=7)
    eval_cmd.add_argument("--profiles", type=int, default=12)
    eval_cmd.add_argument("--horizon", type=int, default=12)
    eval_cmd.add_argument("--cut", type=int, default=6)
    eval_cmd.add_argument("--null", action="store_true")
    eval_cmd.add_argument("--no-llm", action="store_true")
    eval_cmd.add_argument("--concurrency", type=int, default=config.EVAL_MAX_CONCURRENCY)
    eval_cmd.add_argument("--planner-base-url", type=str, default=None)
    eval_cmd.add_argument("--planner-model", type=str, default=None)
    eval_cmd.add_argument("--actor-base-url", type=str, default=None)
    eval_cmd.add_argument("--actor-model", type=str, default=None)
    eval_cmd.add_argument("--actor-metrics-url", type=str, default=None)
    eval_cmd.add_argument("--actor-concurrency", type=int, default=config.ACTOR_MAX_CONCURRENCY)
    eval_cmd.add_argument(
        "--actor-occupancy-ceiling", type=float, default=config.NODE_OCCUPANCY_CEILING
    )
    eval_cmd.add_argument(
        "--precheck-max-occupancy", type=float, default=config.NODE_PRECHECK_MAX_OCCUPANCY
    )
    eval_cmd.add_argument("--no-capacity-gate", dest="capacity_gate", action="store_false")
    eval_cmd.set_defaults(capacity_gate=True)
    eval_cmd.add_argument("--out-json", type=Path, default=Path("build/eval_report.json"))
    eval_cmd.add_argument("--out-md", type=Path, default=Path("build/eval_report.md"))
    eval_cmd.add_argument("--trace-out", type=Path, default=None)
    eval_cmd.add_argument("--langfuse", dest="langfuse", action="store_true", default=None)
    eval_cmd.add_argument("--no-langfuse", dest="langfuse", action="store_false")
    eval_cmd.add_argument("--langfuse-host", type=str, default=None)
    eval_cmd.add_argument("--personas", type=Path, default=None)
    eval_cmd.add_argument("--iteration", type=str, default="adhoc")
    eval_cmd.add_argument("--profile-ids", type=str, default=None)

    judge_cmd = sub.add_parser(
        "judge-traces", help="LLM-as-judge over eval traces; scores + reasoning to langfuse"
    )
    judge_cmd.add_argument("--in", dest="trace_in", type=Path, required=True)
    judge_cmd.add_argument("--to", choices=["json", "langfuse"], default="langfuse")
    judge_cmd.add_argument("--out", type=Path, default=Path("build/judge_verdicts.json"))
    judge_cmd.add_argument("--proposals-out", type=Path, default=Path("build/judge_proposals.json"))
    judge_cmd.add_argument("--no-proposals", dest="proposals", action="store_false")
    judge_cmd.set_defaults(proposals=True)
    judge_cmd.add_argument("--judge-base-url", type=str, default=None)
    judge_cmd.add_argument("--judge-model", type=str, default=None)
    judge_cmd.add_argument("--concurrency", type=int, default=config.EVAL_MAX_CONCURRENCY)
    judge_cmd.add_argument("--judge-metrics-url", type=str, default=None)
    judge_cmd.add_argument("--node-concurrency", type=int, default=config.ACTOR_MAX_CONCURRENCY)
    judge_cmd.add_argument("--occupancy-ceiling", type=float, default=config.NODE_OCCUPANCY_CEILING)
    judge_cmd.add_argument(
        "--precheck-max-occupancy", type=float, default=config.NODE_PRECHECK_MAX_OCCUPANCY
    )
    judge_cmd.add_argument("--no-capacity-gate", dest="capacity_gate", action="store_false")
    judge_cmd.set_defaults(capacity_gate=True)
    judge_cmd.add_argument("--host", type=str, default=None)

    export_cmd = sub.add_parser("export-traces", help="export eval traces for inspection")
    export_cmd.add_argument("--in", dest="trace_in", type=Path, required=True)
    export_cmd.add_argument("--to", choices=["json", "langfuse"], default="json")
    export_cmd.add_argument("--out", type=Path, default=Path("build/langfuse_generations.json"))
    export_cmd.add_argument("--host", type=str, default="http://localhost:3000")

    args = parser.parse_args()
    if args.command == "gen-catalog":
        _run_gen_catalog(args)
    elif args.command == "gen-profiles":
        _run_gen_profiles(args)
    elif args.command == "gen-personas":
        asyncio.run(_run_gen_personas(args))
    elif args.command == "run-eval":
        asyncio.run(_run_eval(args))
    elif args.command == "judge-traces":
        asyncio.run(_run_judge(args))
    elif args.command == "export-traces":
        _run_export_traces(args)


def _run_gen_catalog(args: argparse.Namespace) -> None:
    catalog = catalog_module.build_catalog(args.seed)
    payload = [item.model_dump() for item in catalog]
    _write_json(args.out, payload)
    eligible = catalog_module.eligible_catalog(catalog)
    print(f"catalog: {len(catalog)} SKUs, {len(eligible)} eligible -> {args.out}")


def _run_gen_profiles(args: argparse.Namespace) -> None:
    people = profiles_module.build_profiles(args.seed, args.count)
    payload = [profile.model_dump() for profile in people]
    _write_json(args.out, payload)
    print(f"profiles: {len(people)} -> {args.out}")


async def _run_gen_personas(args: argparse.Namespace) -> None:
    people = profiles_module.build_profiles(args.seed, args.count)
    persona_llm = llm_client_module.persona_config(args.persona_base_url, args.persona_model)
    async with httpx.AsyncClient() as http_client:
        client = ChatClient(persona_llm, http_client)
        batch = await persona_module.generate_personas(client, people, args.seed, args.concurrency)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(batch.model_dump_json(indent=2), encoding="utf-8")
    print(
        f"personas: {batch.generated} llm + {batch.fallback} fallback "
        f"of {batch.count} ({persona_llm.model}) -> {args.out}"
    )


async def _run_eval(args: argparse.Namespace) -> None:
    planner_llm = llm_client_module.planner_config(args.planner_base_url, args.planner_model)
    actor_llm = llm_client_module.actor_config(args.actor_base_url, args.actor_model)
    profile_ids = _parse_profile_ids(args.profile_ids)
    build_count = _build_count(args.profiles, profile_ids)
    settings = eval_module.EvalSettings(
        seed=args.seed,
        profile_count=build_count,
        horizon_weeks=args.horizon,
        cut_week=args.cut,
        planner_model=planner_llm.model,
        actor_model=actor_llm.model,
        null_test=args.null,
        max_concurrency=args.concurrency,
        iteration=args.iteration,
        profile_ids=profile_ids,
    )
    recorder = _build_recorder(args, planner_llm.model, actor_llm.model)
    personas = _load_personas(args.personas)
    actor_metrics_url = args.actor_metrics_url or capacity_module.metrics_url_from_base(
        actor_llm.base_url
    )
    use_capacity_gate = args.capacity_gate and not args.null
    if args.no_llm:
        report = await eval_module.run_eval(None, settings, recorder, personas)
    else:
        async with httpx.AsyncClient() as http_client:
            if use_capacity_gate:
                await capacity_module.ensure_precheck(
                    http_client,
                    actor_metrics_url,
                    max_occupancy=args.precheck_max_occupancy,
                    on_status=lambda message: print(message, file=sys.stderr),
                )
            limiter = (
                capacity_module.CapacityLimiter(
                    http_client,
                    actor_metrics_url,
                    ceiling=args.actor_occupancy_ceiling,
                    concurrency=args.actor_concurrency,
                    on_status=lambda message: print(message, file=sys.stderr),
                )
                if use_capacity_gate
                else None
            )
            clients = eval_module.EvalClients(
                planner=ChatClient(planner_llm, http_client),
                actor=ChatClient(actor_llm, http_client, limiter=limiter),
            )
            report = await eval_module.run_eval(clients, settings, recorder, personas)
    if recorder is not None and args.trace_out is not None:
        args.trace_out.parent.mkdir(parents=True, exist_ok=True)
        args.trace_out.write_text(recorder.to_jsonl(), encoding="utf-8")
        print(f"traces -> {args.trace_out} ({len(recorder.profiles())} profiles)")
    _write_json(args.out_json, report.model_dump())
    markdown = report_module.render_markdown(report)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"json -> {args.out_json}")
    _maybe_push_langfuse(args, recorder, report)


def _load_personas(path: Path | None) -> dict[str, persona_module.Persona] | None:
    if path is None:
        return None
    batch = persona_module.load_persona_batch(path)
    return persona_module.persona_book(batch)


def _langfuse_credentials(args: argparse.Namespace) -> tuple[str, str, str]:
    host = args.langfuse_host or os.environ.get("LANGFUSE_HOST") or config.LANGFUSE_HOST_DEFAULT
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY") or config.LANGFUSE_PUBLIC_KEY_DEFAULT
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY") or config.LANGFUSE_SECRET_KEY_DEFAULT
    return host, public_key, secret_key


def _maybe_push_langfuse(
    args: argparse.Namespace,
    recorder: tracing.TraceRecorder | None,
    report: EvalReport | None = None,
) -> None:
    if recorder is None or args.langfuse is False:
        return
    host, public_key, secret_key = _langfuse_credentials(args)
    loaded = langfuse_export.LoadedTraces(header=recorder.header, profiles=recorder.profiles())
    try:
        sent = langfuse_export.push_to_langfuse(loaded, public_key, secret_key, host)
    except Exception as error:
        print(f"langfuse push skipped: {error}", file=sys.stderr)
        return
    print(f"langfuse <- {sent} generations at {host}")
    if report is None:
        return
    try:
        summary = iteration_summary_module.build_iteration_summary(report, loaded)
        pushed = iteration_summary_module.push_iteration_summary(
            loaded, summary, public_key, secret_key, host
        )
    except Exception as error:
        print(f"langfuse iteration summary skipped: {error}", file=sys.stderr)
        return
    print(f"langfuse <- {pushed} iteration-summary scores ({summary.iteration}) at {host}")


def _parse_profile_ids(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    ids = [item.strip() for item in raw.split(",") if item.strip()]
    return ids or None


def _build_count(requested: int, profile_ids: list[str] | None) -> int:
    if not profile_ids:
        return requested
    indices = [int(pid.lstrip("P")) for pid in profile_ids]
    return max(requested, max(indices) + 1)


def _build_recorder(
    args: argparse.Namespace, planner_model: str, actor_model: str
) -> tracing.TraceRecorder | None:
    if args.trace_out is None:
        return None
    profile_ids = _parse_profile_ids(args.profile_ids)
    header = tracing.EvalRunHeader(
        seed=args.seed,
        profiles=_build_count(args.profiles, profile_ids),
        horizon_weeks=args.horizon,
        cut_week=args.cut,
        planner_model=planner_model,
        actor_model=actor_model,
        null_test=args.null,
        no_llm=args.no_llm,
        iteration=args.iteration,
        profile_ids=profile_ids or [],
    )
    return tracing.TraceRecorder(header)


async def _run_judge(args: argparse.Namespace) -> None:
    loaded = langfuse_export.read_trace_file(args.trace_in)
    judge_llm = llm_client_module.actor_config(args.judge_base_url, args.judge_model)
    judge_metrics_url = args.judge_metrics_url or capacity_module.metrics_url_from_base(
        judge_llm.base_url
    )
    async with httpx.AsyncClient() as http_client:
        if args.capacity_gate:
            await capacity_module.ensure_precheck(
                http_client,
                judge_metrics_url,
                max_occupancy=args.precheck_max_occupancy,
                on_status=lambda message: print(message, file=sys.stderr),
            )
        limiter = (
            capacity_module.CapacityLimiter(
                http_client,
                judge_metrics_url,
                ceiling=args.occupancy_ceiling,
                concurrency=args.node_concurrency,
                on_status=lambda message: print(message, file=sys.stderr),
            )
            if args.capacity_gate
            else None
        )
        client = ChatClient(judge_llm, http_client, limiter=limiter)
        turns = await judge_module.judge_traces(client, loaded, args.concurrency)
        proposals_turn = (
            await judge_module.synthesize_proposals(
                client, loaded, turns, config.JUDGE_MIN_EVIDENCE_PROFILES
            )
            if args.proposals
            else judge_module.ProposalsTurn(proposals=None, call=None)
        )
    scored = judge_module.judgements(turns)
    proposals = proposals_turn.proposals
    print(f"judged {len(turns)} profiles ({len(scored)} parsed) with {judge_llm.model}")
    for turn in turns:
        if turn.verdict is None:
            print(f"  {turn.profile_id}: parse failed")
            continue
        verdict = turn.verdict
        print(
            f"  {turn.profile_id} [{turn.segment}] -> {verdict.verdict} "
            f"(strategy {verdict.strategy_fit} mechanic {verdict.mechanic_choice} "
            f"reward {verdict.reward_fit} honesty {verdict.rationale_honesty} "
            f"persona {verdict.persona_consistency} coop {verdict.actor_cooperation})"
        )
    if proposals is not None:
        print(f"proposals: {len(proposals.proposals)} systemic patterns (>=2 traces each)")
        for proposal in proposals.proposals:
            profiles = ", ".join(item.profile_id for item in proposal.evidence)
            print(f"  [{proposal.severity}] {proposal.dimension}: {proposal.title} ({profiles})")
    elif args.proposals:
        print("proposals: none (no parsed verdicts or synthesis failed)")
    if args.to == "json":
        count = judge_module.write_judgements_json(turns, args.out)
        print(f"verdicts -> {args.out} ({count} profiles)")
        if args.proposals:
            pcount = judge_module.write_proposals_json(proposals, args.proposals_out)
            print(f"proposals -> {args.proposals_out} ({pcount} patterns)")
        return
    host = args.host or os.environ.get("LANGFUSE_HOST") or config.LANGFUSE_HOST_DEFAULT
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY") or config.LANGFUSE_PUBLIC_KEY_DEFAULT
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY") or config.LANGFUSE_SECRET_KEY_DEFAULT
    sent = judge_module.push_scores_to_langfuse(loaded, turns, public_key, secret_key, host)
    print(f"langfuse <- {sent} scores at {host}")
    agg_sent = judge_module.push_judge_summary_to_langfuse(
        loaded, turns, public_key, secret_key, host
    )
    print(f"langfuse <- {agg_sent} judge-summary scores ({loaded.header.iteration}) at {host}")
    if proposals is not None and proposals.proposals:
        pushed = judge_module.push_proposals_to_langfuse(
            loaded, proposals, public_key, secret_key, host
        )
        print(f"langfuse <- {pushed} proposals on judge run summary trace")


def _run_export_traces(args: argparse.Namespace) -> None:
    loaded = langfuse_export.read_trace_file(args.trace_in)
    if args.to == "json":
        count = langfuse_export.write_generations_json(loaded, args.out)
        print(f"trace stories -> {args.out} ({count} profiles)")
        return
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY") or config.LANGFUSE_PUBLIC_KEY_DEFAULT
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY") or config.LANGFUSE_SECRET_KEY_DEFAULT
    host = os.environ.get("LANGFUSE_HOST") or args.host
    sent = langfuse_export.push_to_langfuse(loaded, public_key, secret_key, host)
    print(f"pushed {sent} generations to langfuse at {host}")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
