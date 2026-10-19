#!/usr/bin/env python3
"""Run AI-assisted batch annotation using configurable LLM providers.

Loads unannotated positions from track_a_annotation/annotator_a/TRACK_A_ANNOTATOR_A.jsonl,
generates structured relevance adjudications using LLM providers (Groq, NVIDIA, Gemini, Cloudflare),
stores AI recommendations in track_a_annotation/ai_assisted/AI_RECOMMENDATIONS_V1.jsonl,
generates a researcher review report, and logs session configuration with prompt hashes.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import sys
import time
from typing import Any
import uuid

import httpx

# Ensure repo root and script directory are accessible
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.annotation.common import (
    DEFAULT_AI_DIR,
    DEFAULT_ANNOTATOR_FILE,
    DEFAULT_RECOMMENDATIONS_FILE,
    DEFAULT_REVIEW_REPORT_FILE,
    DEFAULT_SESSION_CONFIG_FILE,
    LABEL_TO_GRADE,
    PROVENANCE_AI_RECOMMENDATION,
    PROVIDER_CONFIGS,
    VALID_LABELS,
    compute_sha256,
    extract_json_from_llm,
    load_jsonl,
    load_prompts_and_hashes,
    normalize_label,
    verify_span_substring,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run AI-assisted annotation runner for Pharmacological RAG evidence positions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--provider",
        choices=list(PROVIDER_CONFIGS.keys()),
        default="groq",
        help="LLM provider to use for adjudication.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name (defaults to provider's recommended model if not set).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of positions to process in each batch.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of unannotated positions to process (useful for testing).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration, credentials, and dataset without making LLM API calls.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Skip positions that already exist in the recommendations output file.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_false",
        dest="resume",
        help="Do not skip existing positions; re-process all target unannotated positions.",
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default=str(DEFAULT_ANNOTATOR_FILE),
        help="Path to source annotator JSONL file.",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=str(DEFAULT_RECOMMENDATIONS_FILE),
        help="Path to output AI recommendations JSONL file.",
    )
    parser.add_argument(
        "--report-file",
        type=str,
        default=str(DEFAULT_REVIEW_REPORT_FILE),
        help="Path to output Markdown researcher review report.",
    )
    parser.add_argument(
        "--session-config-file",
        type=str,
        default=str(DEFAULT_SESSION_CONFIG_FILE),
        help="Path to output session configuration JSON file.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="LLM generation temperature (0.0 for deterministic output).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic generation seed.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="API request timeout in seconds.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts on transient network or rate limit failures.",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Custom API base URL override.",
    )
    return parser.parse_args()


def resolve_api_credentials(provider: str) -> tuple[str, str, str | None]:
    """Resolve API key and base URL for provider from environment variables."""
    cfg = PROVIDER_CONFIGS.get(provider, {})
    env_key = cfg.get("env_key", f"{provider.upper()}_API_KEY")
    api_key = os.environ.get(env_key, "").strip()

    if not api_key:
        for fallback_key in cfg.get("fallback_env_keys", []):
            candidate = os.environ.get(fallback_key, "").strip()
            if candidate:
                api_key = candidate
                break

    base_url = cfg.get("base_url", "")
    if provider == "cloudflare":
        account_id = os.environ.get(cfg.get("account_env_key", "CLOUDFLARE_ACCOUNT_ID"), "").strip()
        template = cfg.get("base_url_template", "")
        base_url = template.format(account_id=account_id or "MISSING_ACCOUNT_ID")
        return api_key, base_url, account_id

    return api_key, base_url, None


def call_llm_adjudicator(
    client: httpx.Client,
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
    seed: int = 42,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Call LLM provider with exponential backoff and rate limit handling."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "seed": seed,
        "response_format": {"type": "json_object"},
    }

    last_error: Exception | None = None
    use_json_object_mode = True

    for attempt in range(max_retries + 1):
        try:
            current_payload = payload.copy()
            if not use_json_object_mode and "response_format" in current_payload:
                del current_payload["response_format"]

            resp = client.post(base_url, headers=headers, json=current_payload)

            if resp.status_code == 400 and use_json_object_mode:
                # Some endpoints do not support response_format: json_object
                use_json_object_mode = False
                continue

            if resp.status_code == 429:
                retry_after_str = resp.headers.get("Retry-After")
                jitter = secrets.randbelow(400) / 1000.0 + 0.1
                delay = float(retry_after_str) if retry_after_str else (1.5**attempt + jitter)
                if attempt < max_retries:
                    time.sleep(delay)
                    continue
                resp.raise_for_status()

            if resp.status_code >= 500:
                jitter = secrets.randbelow(400) / 1000.0 + 0.1
                delay = (2**attempt) + jitter
                if attempt < max_retries:
                    time.sleep(delay)
                    continue
                resp.raise_for_status()

            resp.raise_for_status()
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            parsed = extract_json_from_llm(raw_text)
            return {
                "success": True,
                "parsed": parsed,
                "raw_text": raw_text,
                "raw_sha256": compute_sha256(raw_text),
                "error": None,
            }

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            last_error = e
            if attempt < max_retries:
                jitter = secrets.randbelow(400) / 1000.0 + 0.1
                time.sleep((2**attempt) + jitter)
                continue
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                jitter = secrets.randbelow(400) / 1000.0 + 0.1
                time.sleep((2**attempt) + jitter)
                continue

    return {
        "success": False,
        "parsed": None,
        "raw_text": None,
        "raw_sha256": None,
        "error": str(last_error) if last_error else "Max retries exceeded",
    }


def process_adjudication_result(
    position: dict[str, Any],
    llm_result: dict[str, Any],
    model: str,
    provider: str,
    prompt_hash: str,
) -> dict[str, Any]:
    """Structure and validate LLM output against pharmacological annotation rules."""
    query_id = position.get("query_id", "")
    query_text = position.get("query_text", query_id)
    evidence_text = position.get("retrieved_evidence", "")
    pid = position.get("position_id", "")

    now_iso = datetime.now(timezone.utc).isoformat()

    if not llm_result["success"] or not llm_result["parsed"]:
        # Fallback record on unrecoverable LLM failure
        return {
            "position_id": pid,
            "query_id": query_id,
            "query_text": query_text,
            "chunk_id": position.get("chunk_id", ""),
            "document_id": position.get("document_id", ""),
            "retrieved_evidence": evidence_text,
            "recommended_label": "AMBIGUOUS",
            "recommended_grade": None,
            "confidence": "LOW",
            "recommended_rationale": f"LLM adjudication failed: {llm_result.get('error')}",
            "recommended_evidence_span": "",
            "alternative_label": None,
            "detailed_adjudication": {"error": llm_result.get("error")},
            "provenance": PROVENANCE_AI_RECOMMENDATION,
            "model": model,
            "provider": provider,
            "prompt_hash": prompt_hash,
            "timestamp": now_iso,
            "status": "PENDING_REVIEW",
            "label": "AMBIGUOUS",
            "relevance_grade": None,
            "rationale": f"LLM adjudication failed: {llm_result.get('error')}",
            "evidence_span": "",
        }

    parsed = llm_result["parsed"]

    raw_label = parsed.get("proposed_label") or parsed.get("label") or "AMBIGUOUS"
    norm_label = normalize_label(raw_label) or "AMBIGUOUS"
    if norm_label not in VALID_LABELS:
        norm_label = "AMBIGUOUS"

    expected_grade = LABEL_TO_GRADE.get(norm_label)
    proposed_grade = parsed.get("proposed_grade")
    grade = expected_grade if expected_grade is not None else proposed_grade

    rationale = (
        parsed.get("proposed_rationale")
        or parsed.get("rationale")
        or "AI generated pharmacological relevance recommendation."
    )
    confidence = (
        parsed.get("confidence", "MEDIUM").upper()
        if parsed.get("confidence")
        else "MEDIUM"
    )
    if confidence not in {"HIGH", "MEDIUM", "LOW"}:
        confidence = "MEDIUM"

    raw_span = parsed.get("best_supporting_span") or parsed.get("evidence_span") or ""
    best_span = ""
    if norm_label in {"RELEVANT", "PARTIALLY_RELEVANT"}:
        is_valid, matched_span = verify_span_substring(raw_span, evidence_text)
        if is_valid and matched_span:
            best_span = matched_span
        else:
            # If LLM didn't return an exact span for relevant label, flag confidence
            confidence = "LOW"
            best_span = raw_span[:200] if raw_span else ""
    else:
        best_span = ""

    alt_label = parsed.get("alternative_label_considered")
    if alt_label:
        alt_label = normalize_label(alt_label)

    return {
        "position_id": pid,
        "query_id": query_id,
        "query_text": query_text,
        "chunk_id": position.get("chunk_id", ""),
        "document_id": position.get("document_id", ""),
        "retrieved_evidence": evidence_text,
        "recommended_label": norm_label,
        "recommended_grade": grade,
        "confidence": confidence,
        "recommended_rationale": rationale,
        "recommended_evidence_span": best_span,
        "alternative_label": alt_label,
        "detailed_adjudication": parsed,
        "provenance": PROVENANCE_AI_RECOMMENDATION,
        "model": model,
        "provider": provider,
        "prompt_hash": prompt_hash,
        "timestamp": now_iso,
        "status": "PENDING_REVIEW",
        # Convenience aliases for schema compatibility
        "label": norm_label,
        "relevance_grade": grade,
        "rationale": rationale,
        "evidence_span": best_span,
    }


def generate_review_report(
    recommendations: list[dict[str, Any]],
    output_path: Path | str,
    session_config: dict[str, Any],
) -> None:
    """Generate Markdown review report for researchers."""
    total = len(recommendations)
    labels_count: dict[str, int] = {}
    confidence_count: dict[str, int] = {}
    high_priority_items: list[dict[str, Any]] = []

    for r in recommendations:
        lbl = r.get("recommended_label", "UNKNOWN")
        labels_count[lbl] = labels_count.get(lbl, 0) + 1

        conf = r.get("confidence", "UNKNOWN")
        confidence_count[conf] = confidence_count.get(conf, 0) + 1

        if conf == "LOW" or lbl == "AMBIGUOUS" or r.get("alternative_label"):
            high_priority_items.append(r)

    md = [
        "# Track A AI-Assisted Annotation Review Report (V1)",
        "",
        f"**Generated At**: {datetime.now(timezone.utc).isoformat()}",
        f"**Session ID**: `{session_config.get('session_id', 'N/A')}`",
        f"**Provider**: `{session_config.get('provider')}` | **Model**: `{session_config.get('model')}`",
        f"**Total Recommendations Generated**: {total}",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Positions Processed**: {total}",
        f"- **High Confidence**: {confidence_count.get('HIGH', 0)} ({((confidence_count.get('HIGH', 0) / total) * 100):.1f}% if total else 0%)",
        f"- **Medium Confidence**: {confidence_count.get('MEDIUM', 0)} ({((confidence_count.get('MEDIUM', 0) / total) * 100):.1f}% if total else 0%)",
        f"- **Low Confidence / Ambiguous**: {len(high_priority_items)} ({((len(high_priority_items) / total) * 100):.1f}% if total else 0%)",
        "",
        "## 2. Label Distribution",
        "",
        "| Label | Grade | Count | Percentage |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for lbl in ["RELEVANT", "PARTIALLY_RELEVANT", "IRRELEVANT", "INSUFFICIENT_INFORMATION", "AMBIGUOUS"]:
        cnt = labels_count.get(lbl, 0)
        pct = (cnt / total * 100) if total else 0.0
        grd = LABEL_TO_GRADE.get(lbl)
        grd_str = str(grd) if grd is not None else "null"
        md.append(f"| **{lbl}** | {grd_str} | {cnt} | {pct:.1f}% |")

    md.extend([
        "",
        "## 3. High-Priority Items for Researcher Attention",
        "",
        "The following positions require specific human evaluation due to low confidence, ambiguous evidence, or viable alternative labels:",
        "",
        "| Position ID | Query | Recommendation | Confidence | Alternative Label | Reason |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    if high_priority_items:
        for item in high_priority_items[:50]:  # Cap to top 50 in summary
            q_short = item.get("query_text", "")[:35]
            pid = item.get("position_id")
            rec_lbl = item.get("recommended_label")
            conf = item.get("confidence")
            alt = item.get("alternative_label") or "-"
            rat_short = item.get("recommended_rationale", "")[:45].replace("|", "/")
            md.append(f"| `{pid}` | {q_short}... | **{rec_lbl}** | {conf} | {alt} | {rat_short}... |")
    else:
        md.append("| None | All recommendations generated with medium or high confidence | - | - | - | - |")

    md.extend([
        "",
        "## 4. Next Steps for Researcher Review",
        "",
        "To review and approve/override these recommendations, run the interactive review CLI:",
        "```bash",
        "uv run python scripts/annotation/review_recommendations.py",
        "```",
        "",
        "Or review only low/medium confidence cases first:",
        "```bash",
        "uv run python scripts/annotation/review_recommendations.py --filter-confidence LOW",
        "```",
        "",
    ])

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text("\n".join(md), encoding="utf-8")


def main() -> None:
    args = parse_args()
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    start_time = time.time()
    start_iso = datetime.now(timezone.utc).isoformat()

    print("=================================================================")
    print("    Pharmacological RAG: AI-Assisted Annotation Runner          ")
    print("=================================================================")
    print(f"Session ID : {session_id}")
    print(f"Provider   : {args.provider}")

    model = args.model or PROVIDER_CONFIGS[args.provider]["default_model"]
    print(f"Model      : {model}")
    print(f"Batch Size : {args.batch_size}")
    if args.limit:
        print(f"Limit      : {args.limit}")
    print(f"Dry Run    : {args.dry_run}")
    print(f"Resume     : {args.resume}")

    # Ensure output directory exists
    DEFAULT_AI_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load prompts and schema
    prompts_data = load_prompts_and_hashes()
    system_prompt = prompts_data["system_prompt"]
    prompt_template = prompts_data["adjudication_prompt_template"]
    prompt_hashes = prompts_data["hashes"]
    adj_prompt_hash = prompt_hashes["adjudication_prompt_sha256"]

    print(f"Prompt SHA256: {adj_prompt_hash[:16]}...")

    # 2. Resolve credentials
    api_key, default_base_url, _ = resolve_api_credentials(args.provider)
    base_url = args.base_url or default_base_url

    if not api_key and not args.dry_run:
        env_key = PROVIDER_CONFIGS[args.provider].get("env_key", f"{args.provider.upper()}_API_KEY")
        print(f"\n[ERROR] Missing API key for provider '{args.provider}'.")
        print(f"Please set the environment variable '{env_key}'.")
        sys.exit(1)

    # 3. Load positions
    input_records = load_jsonl(args.input_file)
    unannotated_positions = [
        r
        for r in input_records
        if r.get("annotation_status") == "UNANNOTATED" or r.get("label") is None
    ]
    print(f"Loaded {len(input_records)} total records from {args.input_file}")
    print(f"Found {len(unannotated_positions)} unannotated positions")

    # 4. Check resume state
    output_path = Path(args.output_file)
    existing_recs = load_jsonl(output_path) if output_path.is_file() else []
    existing_pids = {r.get("position_id") for r in existing_recs if r.get("position_id")}

    if args.resume and existing_pids:
        positions_to_process = [
            p for p in unannotated_positions if p.get("position_id") not in existing_pids
        ]
        print(f"Resuming: {len(existing_pids)} already have recommendations; {len(positions_to_process)} remaining.")
    else:
        positions_to_process = unannotated_positions

    if args.limit:
        positions_to_process = positions_to_process[: args.limit]
        print(f"Applied limit: processing {len(positions_to_process)} positions.")

    # DRY RUN HANDLING
    if args.dry_run:
        print("\n--- DRY RUN VALIDATION SUMMARY ---")
        print(f"Provider: {args.provider}")
        print(f"Model: {model}")
        print(f"Base URL: {base_url}")
        print(f"API Key Configured: {'YES' if api_key else 'NO (Required for live run)'}")
        print(f"System Prompt Length: {len(system_prompt)} chars")
        print(f"Adjudication Template Length: {len(prompt_template)} chars")
        print(f"Unannotated Positions Eligible: {len(positions_to_process)}")
        print("Dry run validation successful! No API calls were made.")

        dry_run_config = {
            "session_id": session_id,
            "status": "DRY_RUN",
            "provider": args.provider,
            "model": model,
            "base_url": base_url,
            "batch_size": args.batch_size,
            "limit": args.limit,
            "temperature": args.temperature,
            "seed": args.seed,
            "prompt_hashes": prompt_hashes,
            "unannotated_count": len(unannotated_positions),
            "target_count": len(positions_to_process),
            "start_timestamp": start_iso,
            "end_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        Path(args.session_config_file).write_text(json.dumps(dry_run_config, indent=2), encoding="utf-8")
        return

    # LIVE BATCH EXECUTION
    new_recommendations: list[dict[str, Any]] = []
    total_to_process = len(positions_to_process)
    success_count = 0
    fail_count = 0

    print(f"\nBeginning execution for {total_to_process} positions in batches of {args.batch_size}...")

    try:
        with httpx.Client(timeout=args.timeout) as client:
            for idx, pos in enumerate(positions_to_process, 1):
                pid = pos.get("position_id")
                q_text = pos.get("query_text", pos.get("query_id", ""))
                ev_text = pos.get("retrieved_evidence", "")

                formatted_user_prompt = prompt_template.format(query=q_text, evidence=ev_text)

                print(f"[{idx}/{total_to_process}] Adjudicating {pid} ({q_text[:40]}...)...", end="", flush=True)

                llm_res = call_llm_adjudicator(
                    client=client,
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=formatted_user_prompt,
                    temperature=args.temperature,
                    seed=args.seed,
                    max_retries=args.max_retries,
                )

                rec = process_adjudication_result(
                    position=pos,
                    llm_result=llm_res,
                    model=model,
                    provider=args.provider,
                    prompt_hash=adj_prompt_hash,
                )

                # Persist immediately to disk for interruption safety
                with output_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()

                new_recommendations.append(rec)
                if rec["recommended_label"] != "AMBIGUOUS" and llm_res["success"]:
                    success_count += 1
                    print(f" Done. -> {rec['recommended_label']} ({rec['confidence']})")
                else:
                    fail_count += 1
                    print(f" Warning. -> {rec['recommended_label']}")

                # Batch pause between batches if applicable
                if idx % args.batch_size == 0 and idx < total_to_process:
                    time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n[NOTICE] Execution interrupted by user! Gracefully saving progress...")

    finally:
        end_time = time.time()
        duration = end_time - start_time
        all_current_recs = load_jsonl(output_path)

        # Generate review report
        generate_review_report(all_current_recs, args.report_file, {
            "session_id": session_id,
            "provider": args.provider,
            "model": model,
        })
        print(f"Generated Review Report at: {args.report_file}")

        # Save session config
        session_config = {
            "session_id": session_id,
            "provider": args.provider,
            "model": model,
            "base_url": base_url,
            "temperature": args.temperature,
            "seed": args.seed,
            "batch_size": args.batch_size,
            "limit": args.limit,
            "start_timestamp": start_iso,
            "end_timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            "prompt_hashes": prompt_hashes,
            "total_unannotated_loaded": len(unannotated_positions),
            "total_positions_processed_this_run": len(new_recommendations),
            "total_recommendations_on_disk": len(all_current_recs),
            "successful_in_run": success_count,
            "failed_or_ambiguous_in_run": fail_count,
            "status": "COMPLETED" if len(new_recommendations) == total_to_process else "PARTIAL",
        }
        Path(args.session_config_file).write_text(json.dumps(session_config, indent=2), encoding="utf-8")
        print(f"Logged Session Config at  : {args.session_config_file}")
        print(f"All AI Recommendations at : {output_path}")


if __name__ == "__main__":
    main()
