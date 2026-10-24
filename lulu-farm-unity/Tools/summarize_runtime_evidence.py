#!/usr/bin/env python3
"""Read a real FarmEvidence session; write a new, separate JSON/Markdown analysis.

No rendering, process control, network, interpolation, inferred zero readings, or art acceptance.
Per-frame profiler summaries and low-frequency FrameTiming samples remain separate populations.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import re
from pathlib import Path
import statistics


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        # Unity DateTime.ToString("o") emits seven fractional digits; Python 3.9
        # accepts only microseconds. Truncate sub-microsecond precision, not sample time.
        normalized = re.sub(r"(\.\d{6})\d+(?=Z|[+-]\d\d:\d\d|$)", r"\1", value)
        return datetime.fromisoformat(normalized.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def stats(values):
    valid = sorted(float(v) for v in values if number(v) is not None)
    if not valid:
        return {"status": "unavailable", "samples": 0, "mean": None, "p95": None, "minimum": None, "maximum": None}
    return {"status": "available_measured", "samples": len(valid), "mean": statistics.fmean(valid),
            "p95": valid[max(0, math.ceil(len(valid) * .95) - 1)], "minimum": valid[0], "maximum": valid[-1]}


def normalize_frame_stats(row):
    row = row if isinstance(row, dict) else {}
    n = number(row.get("sampleCount")) or 0
    valid = row.get("available") is True and n > 0
    return {"name": row.get("name"), "category": row.get("category"), "unit": row.get("unit"),
            "status": "available_measured" if valid else "unavailable", "sample_count": n,
            "unavailable_frames": row.get("unavailableFrames"),
            "unavailable_reason": None if valid else row.get("unavailableReason", "missing_final_summary"),
            "mean": number(row.get("mean")) if valid else None,
            "p95": number(row.get("p95")) if valid else None,
            "maximum": number(row.get("maximum")) if valid else None}


def summarize(session: Path, minimum_seconds: float, window_seconds: float):
    warnings = []
    sources = {}
    def read(relative, lines=False):
        path = session / relative
        if not path.is_file():
            sources[relative] = {"present": False}
            return [] if lines else {}
        data = path.read_bytes()
        sources[relative] = {"present": True, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        if lines:
            out = []
            for index, line in enumerate(data.decode("utf-8-sig").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError("record is not an object")
                    out.append(row)
                except (ValueError, json.JSONDecodeError) as error:
                    warnings.append(f"{relative}:{index}: invalid JSON record excluded ({error})")
            sources[relative]["parsed_records"] = len(out)
            return out
        try:
            row = json.loads(data.decode("utf-8-sig"))
            if not isinstance(row, dict):
                raise ValueError("document is not an object")
            return row
        except (ValueError, json.JSONDecodeError) as error:
            warnings.append(f"{relative}: unreadable JSON ({error})")
            return {}

    config = read("performance/configuration.json")
    final = read("performance/summary.json")
    perf_rows = read("performance/samples.jsonl", lines=True)
    route_rows = read("route-samples.jsonl", lines=True)
    route_final = read("performance-route.json")
    events = read("events.jsonl", lines=True)
    latest = read("runtime-latest.json")
    if not config:
        warnings.append("No performance/configuration.json: this is not a verified capture-free performance session.")
    if not final:
        warnings.append("No final performance/summary.json: a complete per-frame P95 and clean session finish cannot be reconstructed from 1Hz aggregates.")

    start_estimates = []
    for row in perf_rows:
        epoch = timestamp(row.get("utc")); elapsed = number(row.get("elapsedSeconds"))
        if epoch is not None and elapsed is not None:
            start_estimates.append(epoch - elapsed)
    start_epoch = statistics.median(start_estimates) if start_estimates else None
    clock_spread = max(start_estimates) - min(start_estimates) if start_estimates else None
    if clock_spread is not None and clock_spread > .25:
        warnings.append("Wall-clock/performance-clock alignment varies by more than 250ms; timed sample-window selection needs review.")
    warmup = number(final.get("warmupSeconds"))
    if warmup is None:
        warmup = number(config.get("warmupSeconds"))
    elapsed = number(final.get("elapsedSeconds"))
    if elapsed is None and perf_rows:
        elapsed_values = [number(r.get("elapsedSeconds")) for r in perf_rows]
        elapsed = max((x for x in elapsed_values if x is not None), default=None)
    duration = number(final.get("measurementSeconds"))
    if duration is None and elapsed is not None and warmup is not None:
        duration = max(0, elapsed - warmup)
    measured_start = start_epoch + warmup if start_epoch is not None and warmup is not None else None
    measured_end = start_epoch + elapsed if start_epoch is not None and elapsed is not None else None
    timed = [(timestamp(r.get("timestampUtc")), r) for r in route_rows]
    invalid_time_count = sum(t is None for t, _ in timed)
    if invalid_time_count:
        warnings.append(f"{invalid_time_count} diagnostics records have missing/invalid UTC timestamps and cannot be aligned.")
    timed = [(t, r) for t, r in timed if t is not None]
    timed.sort(key=lambda item: item[0])
    if measured_start is not None and measured_end is not None:
        selected = [(t, r) for t, r in timed if measured_start <= t <= measured_end]
        selection_scope = "0.5s diagnostics records within inferred post-warmup performance interval"
    else:
        selected = timed
        selection_scope = "all available diagnostics records; no complete performance interval available"
        warnings.append("Diagnostics statistics include the whole observed session because the performance measurement interval is unavailable.")
    sample_times = [t for t, _ in selected]
    gaps = [b-a for a, b in zip(sample_times, sample_times[1:])]
    sample_span = sample_times[-1] - sample_times[0] if len(sample_times) > 1 else None

    frame = normalize_frame_stats(final.get("frameTimeMs"))
    frame["population"] = "per-frame Time.unscaledDeltaTime after warmup; final summary, not 1Hz spot samples"
    frame["fps_from_mean_interval"] = 1000 / frame["mean"] if frame["mean"] and frame["mean"] > 0 else None
    perf_frame_windows = []
    for row in perf_rows:
        value = row.get("frameTimeMs")
        if isinstance(value, dict) and value.get("available") is True and (number(value.get("sampleCount")) or 0) > 0:
            perf_frame_windows.append(value)
    window_frames = sum(number(r.get("sampleCount")) or 0 for r in perf_frame_windows)
    window_seconds = float(window_seconds)
    frame_seconds = sum((number(r.get("sampleCount")) or 0) * (number(r.get("mean")) or 0) / 1000 for r in perf_frame_windows)
    frame_count_matches = frame["sample_count"] == window_frames if final else None
    if frame_count_matches is False:
        warnings.append("Final frame count differs from sum of JSONL windows; investigate incomplete/duplicate writes before reporting full coverage.")
    if duration and frame_seconds / duration < .98:
        warnings.append("Collected frame intervals cover less than 98% of the stated measurement duration.")
    counters = [normalize_frame_stats(row) for row in final.get("counters", []) if isinstance(row, dict)]
    for row in counters:
        n = row["sample_count"]
        missing = number(row["unavailable_frames"])
        row["available_fraction"] = n / (n + missing) if missing is not None and n + missing > 0 else None
        row["population"] = "per-frame ProfilerRecorder completed-frame values; native timer units converted by harness"

    def sampled_timing(name, value_key, available_key):
        values = [r.get(value_key) for _, r in selected if r.get(available_key) is True and
                  number(r.get(value_key)) is not None and r[value_key] > 0]
        result = stats(values)
        result.update(name=name, unit="ms", population="latest FrameTiming at each diagnostics sample, not every rendered frame",
                      eligible_records=len(selected), available_ratio=len(values)/len(selected) if selected else None,
                      unavailable_records=len(selected)-len(values))
        return result

    def memory(key):
        valid = [(t, r[key]) for t, r in selected if number(r.get(key)) is not None and r[key] > 0]
        result = stats([v for _, v in valid])
        first_boundary = measured_start if measured_start is not None else sample_times[0] if sample_times else None
        last_boundary = measured_end if measured_end is not None else sample_times[-1] if sample_times else None
        first = stats([v for t, v in valid if first_boundary is not None and t <= first_boundary + window_seconds])
        last = stats([v for t, v in valid if last_boundary is not None and t >= last_boundary - window_seconds])
        delta = last["mean"]-first["mean"] if first["mean"] is not None and last["mean"] is not None else None
        result.update(unit="bytes", source=key, population="sampled Unity Profiler memory API; not process RSS, GPU memory use, or device total RAM",
                      eligible_records=len(selected), unavailable_records=len(selected)-len(valid),
                      first_window=first, last_window=last, window_seconds=window_seconds,
                      windows_overlap=(last_boundary-first_boundary < 2*window_seconds) if first_boundary is not None and last_boundary is not None else None,
                      last_minus_first_mean_bytes=delta,
                      last_minus_first_mean_percent=delta/first["mean"]*100 if delta is not None and first["mean"] else None)
        return result

    def bool_anomaly(key, desired):
        observations = [r[key] for _, r in selected if isinstance(r.get(key), bool)]
        abnormal = sum(v != desired for v in observations)
        return {"observed_records": len(observations), "anomalous_records": abnormal,
                "anomalous_ratio": abnormal/len(observations) if observations else None,
                "expected_value": desired, "unavailable_records": len(selected)-len(observations)}

    classifications = Counter(r.get("performanceRunClassification", "missing") for _, r in selected)
    capture_events = [r for r in events if "screenshot_written_" in str(r.get("action", "")) or
                      str(r.get("action", "")).startswith("frame_sequence_started_")]
    route_lap_events = [r for r in events if str(r.get("action", "")).startswith("performance_route_lap_completed_")]
    normal_stop = final.get("stoppedBecause") == "application_quit" and route_final.get("status") == "performance_session_application_quit"
    completion = {
        "minimum_measurement_seconds": minimum_seconds,
        "actual_post_warmup_seconds": duration,
        "duration_meets_minimum": duration >= minimum_seconds if duration is not None else False,
        "final_summary_present": bool(final),
        "per_frame_samples": frame["sample_count"], "jsonl_window_frame_count": window_frames,
        "summary_matches_jsonl_frame_count": frame_count_matches,
        "sum_measured_frame_intervals_seconds": frame_seconds if perf_frame_windows else None,
        "frame_interval_duration_coverage": frame_seconds/duration if perf_frame_windows and duration and duration > 0 else None,
        "configuration_unchanged": final.get("configurationUnchanged"),
        "normal_quit_route_pair": normal_stop,
        "capture_written_events": len(capture_events),
        "acceptance": "measurement completeness only; no automatic performance or art approval"}
    if config.get("stage") == "mature" and config.get("activeMaturePlots") != config.get("cropPlots"):
        warnings.append("Configured mature stage does not have every recorded crop plot active as mature.")
    if capture_events:
        warnings.append("Session contains capture-written/recording events; inspect whether they overlap the measurement interval.")
    if not normal_stop and final:
        warnings.append("Final stop pair is not application_quit / performance_session_application_quit; inspect timeline rather than assuming a route collision.")
    perf_elapsed = [number(r.get("elapsedSeconds")) for r in perf_rows]
    perf_elapsed = [x for x in perf_elapsed if x is not None]
    return {
        "schema": "lulu-runtime-evidence-summary-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
        "input_session": str(session), "read_only_inputs": True, "source_files": sources,
        "acceptance": {"technical": "measured evidence requires review", "visual": "not_evaluated", "user_art": "pending",
                       "other_devices": "not_inferred", "temperature": "not_measured_no_temperature_API_data"},
        "configuration": config, "completion": completion,
        "time_alignment": {"scope": selection_scope, "performance_start_utc_epoch": start_epoch,
                           "start_estimate_spread_seconds": clock_spread, "measurement_start_utc_epoch": measured_start,
                           "measurement_end_utc_epoch": measured_end},
        "per_frame": {"frame_time_ms": frame, "profiler_counters": counters,
                      "limitations": "Main/Render Thread durations may include waits; not CPU utilization. Final summary P95 cannot be rebuilt from window P95s."},
        "sampled_diagnostics": {
            "records_total": len(route_rows), "records_in_measurement_interval": len(selected), "sample_span_seconds": sample_span,
            "sampling_intervals_seconds": stats(gaps),
            "first_sample_delay_seconds": sample_times[0]-measured_start if sample_times and measured_start is not None else None,
            "last_sample_tail_seconds": measured_end-sample_times[-1] if sample_times and measured_end is not None else None,
            "cpu_frame_timing_ms": sampled_timing("CPU FrameTiming", "cpuFrameMs", "cpuTimingAvailable"),
            "gpu_frame_timing_ms": sampled_timing("GPU FrameTiming", "gpuFrameMs", "gpuTimingAvailable"),
            "memory": {key: memory(key) for key in ("totalAllocatedBytes", "totalReservedBytes", "monoUsedBytes")},
            "viewport": bool_anomaly("targetInsideViewport", True), "cinemachine": bool_anomaly("cinemachineLive", True),
            "grounded": bool_anomaly("grounded", True), "pause": bool_anomaly("paused", False),
            "focus": bool_anomaly("applicationFocused", True), "session_classifications": dict(classifications)},
        "performance_jsonl": {"records": len(perf_rows), "sampling_intervals_seconds": stats([b-a for a,b in zip(perf_elapsed, perf_elapsed[1:])])},
        "route": {"summary_stopped_because": final.get("stoppedBecause"), "summary_route_status": final.get("routeStatus"),
                  "summary_loop_running_at_stop": final.get("routeLoopRunningAtStop"), "final_status": route_final.get("status"),
                  "completed_laps": final.get("completedLaps", route_final.get("completedLaps")),
                  "lap_event_count": len(route_lap_events), "lap_events": route_lap_events,
                  "last_waypoint": final.get("lastWaypoint", route_final.get("reachedWaypoints")),
                  "planned_waypoints": route_final.get("plannedWaypoints"),
                  "final_position": route_final.get("finalPosition"),
                  "virtual_gamepad_enabled_at_stop": route_final.get("virtualGamepadEnabled"),
                  "virtual_gamepad_background_capable": route_final.get("virtualGamepadCanRunInBackground"),
                  "latest_diagnostics_automation": latest.get("inputAutomation"),
                  "status_timing_note": "runtime-latest may be saved before performance shutdown; summary captures route before Stop, final route JSON after Stop. These labels need not match."},
        "limitations": ["No sensor temperature/thermal-throttling claim.", "Unity memory APIs are not macOS RSS or total unified GPU allocation.",
                        "CPU/GPU FrameTiming means/P95 describe valid sampled frames only, not all rendered frames.",
                        "No confidence inferred for Android/Windows/iOS or user artwork from this session.",
                        "Logging, recorder collection and periodic summary allocations are part of observed harness overhead."],
        "warnings": warnings}


def markdown(report):
    def fmt(value, digits=2):
        return "未测/不可用" if number(value) is None else f"{value:,.{digits}f}"
    def frac(value):
        return "未测/不可用" if number(value) is None else f"{value*100:.2f}%"
    completion = report["completion"]; config = report["configuration"]; per = report["per_frame"]
    sampled = report["sampled_diagnostics"]; route = report["route"]
    lines = ["# 实际运行记录汇总", "", f"输入：`{report['input_session']}`", "",
             f"配置：{config.get('platform', '未记录')} / {config.get('quality', '未记录')} / {config.get('width', '?')}×{config.get('height', '?')} / {config.get('stage', '未记录')}，成熟 {config.get('activeMaturePlots', '?')}/{config.get('cropPlots', '?')} 格。", "",
             f"有效计时 {fmt(completion['actual_post_warmup_seconds'])} 秒；要求 {fmt(completion['minimum_measurement_seconds'])} 秒；时长达标：{'是' if completion['duration_meets_minimum'] else '否或未验证'}。逐帧 {completion['per_frame_samples']:,} 样本，窗口帧数核对：{completion['summary_matches_jsonl_frame_count']}，帧间隔时长覆盖 {frac(completion['frame_interval_duration_coverage'])}。", "",
             "| 指标 | 均值 | P95 | 有效样本 |", "|---|---:|---:|---:|",
             f"| 逐帧间隔 ms | {fmt(per['frame_time_ms']['mean'])} | {fmt(per['frame_time_ms']['p95'])} | {per['frame_time_ms']['sample_count']} |"]
    for counter in per["profiler_counters"]:
        lines.append(f"| 逐帧 {counter['name']} ({counter['unit']}) | {fmt(counter['mean'])} | {fmt(counter['p95'])} | {counter['sample_count']} |")
    for key in ("cpu_frame_timing_ms", "gpu_frame_timing_ms"):
        row = sampled[key]
        lines.append(f"| 约 0.5s 抽样 {row['name']} ms | {fmt(row['mean'])} | {fmt(row['p95'])} | {row['samples']}/{row['eligible_records']} ({frac(row['available_ratio'])}) |")
    lines += ["", "逐帧统计与 CPU/GPU 抽样是不同总体；抽样 P95 不代表全部帧。Main/Render Thread 耗时也不等于 CPU 使用率。", "",
              "| Unity 内存指标 | 采样峰值 MiB | 首窗口均值 MiB | 尾窗口均值 MiB | 均值变化 MiB |", "|---|---:|---:|---:|---:|"]
    for key, row in sampled["memory"].items():
        def mib(value): return fmt(value / 1048576 if number(value) is not None else None)
        lines.append(f"| {key} | {mib(row['maximum'])} | {mib(row['first_window']['mean'])} | {mib(row['last_window']['mean'])} | {mib(row['last_minus_first_mean_bytes'])} |")
    lines += ["", "内存值来自 Unity Profiler API，不是系统 RSS 或 GPU 实际占用；首尾窗口可能因短记录重叠，见 JSON。", "",
              f"诊断采样 {sampled['records_in_measurement_interval']} 条，最大内部间隔 {fmt(sampled['sampling_intervals_seconds']['maximum'])} 秒。视口异常 {frac(sampled['viewport']['anomalous_ratio'])}，Cinemachine 非活动 {frac(sampled['cinemachine']['anomalous_ratio'])}。", "",
              f"路线 {route['completed_laps']} 圈，终点索引 {route['last_waypoint']}/{route['planned_waypoints']}。Session 停止：`{route['summary_stopped_because']}`；最终路线：`{route['final_status']}`。", "",
              "温度、其他设备、美术和用户验收均不由本报告判定通过。"]
    if report["warnings"]:
        lines += ["", "需核对：", ""] + ["- " + message for message in report["warnings"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("--output", type=Path, help="new directory outside the input session; default: sibling <session>-analysis")
    parser.add_argument("--minimum-seconds", type=float, default=900)
    parser.add_argument("--window-seconds", type=float, default=60, help="first/last memory windows")
    args = parser.parse_args()
    session = args.session.expanduser().resolve()
    if not session.is_dir(): parser.error("session must be an existing directory")
    if not math.isfinite(args.minimum_seconds) or args.minimum_seconds <= 0: parser.error("minimum-seconds must be positive and finite")
    if not math.isfinite(args.window_seconds) or args.window_seconds <= 0: parser.error("window-seconds must be positive and finite")
    output = (args.output.expanduser().resolve() if args.output else session.with_name(session.name + "-analysis"))
    if output == session or session in output.parents: parser.error("output must be outside the read-only input session")
    if output.exists(): parser.error("output already exists; choose a fresh directory to preserve previous reports")
    report = summarize(session, args.minimum_seconds, args.window_seconds)
    output.mkdir(parents=True)
    (output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output / "summary.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"json": str(output / "summary.json"), "markdown": str(output / "summary.md"), "warning_count": len(report["warnings"]),
                      "duration_meets_minimum": report["completion"]["duration_meets_minimum"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
