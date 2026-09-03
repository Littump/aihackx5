import argparse
import asyncio
import json
from pathlib import Path

import httpx

from app.ml import catalog as catalog_module
from app.ml import eval as eval_module
from app.ml import profiles as profiles_module
from app.ml import report as report_module
from app.ml.llm_client import LLMConfig, QwenClient


def main() -> None:
    parser = argparse.ArgumentParser(description="ML LLM-planner module CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    catalog_cmd = sub.add_parser("gen-catalog", help="generate synthetic SKU catalog")
    catalog_cmd.add_argument("--seed", type=int, default=7)
    catalog_cmd.add_argument("--out", type=Path, default=Path("build/sku_catalog.json"))

    profiles_cmd = sub.add_parser("gen-profiles", help="generate synthetic user profiles")
    profiles_cmd.add_argument("--seed", type=int, default=7)
    profiles_cmd.add_argument("--count", type=int, default=200)
    profiles_cmd.add_argument("--out", type=Path, default=Path("build/user_profiles.json"))

    eval_cmd = sub.add_parser("run-eval", help="run the counterfactual eval once")
    eval_cmd.add_argument("--seed", type=int, default=7)
    eval_cmd.add_argument("--profiles", type=int, default=12)
    eval_cmd.add_argument("--horizon", type=int, default=12)
    eval_cmd.add_argument("--cut", type=int, default=6)
    eval_cmd.add_argument("--null", action="store_true")
    eval_cmd.add_argument("--no-llm", action="store_true")
    eval_cmd.add_argument("--base-url", type=str, default=None)
    eval_cmd.add_argument("--model", type=str, default=None)
    eval_cmd.add_argument("--out-json", type=Path, default=Path("build/eval_report.json"))
    eval_cmd.add_argument("--out-md", type=Path, default=Path("build/eval_report.md"))

    args = parser.parse_args()
    if args.command == "gen-catalog":
        _run_gen_catalog(args)
    elif args.command == "gen-profiles":
        _run_gen_profiles(args)
    elif args.command == "run-eval":
        asyncio.run(_run_eval(args))


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


async def _run_eval(args: argparse.Namespace) -> None:
    llm_config = LLMConfig(base_url=args.base_url, model=args.model)
    settings = eval_module.EvalSettings(
        seed=args.seed,
        profile_count=args.profiles,
        horizon_weeks=args.horizon,
        cut_week=args.cut,
        model=llm_config.model,
        null_test=args.null,
    )
    if args.no_llm:
        report = await eval_module.run_eval(None, settings)
    else:
        async with httpx.AsyncClient() as http_client:
            client = QwenClient(llm_config, http_client)
            report = await eval_module.run_eval(client, settings)
    _write_json(args.out_json, report.model_dump())
    markdown = report_module.render_markdown(report)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"json -> {args.out_json}")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
