#!/usr/bin/env python3
"""
run_all_tests.py
Automated Test Runner for MRC Simulation Suite (TC-01 ~ TC-10)
Implements SPEC.md Sections 5, 6, 7, 8.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/root/mrc-sim")
BIN_UEC = ROOT / "htsim/htsim/sim/datacenter/htsim_uec"
TRAFFIC_DIR = ROOT / "configs/traffic"
REPORTS_DIR = ROOT / "reports"

sys.path.insert(0, str(ROOT / "scripts"))
from inspect_packets import summarize_trace
from export_hw_vectors import export_vectors


LIVE_STATUS_PATH = REPORTS_DIR / "live_status.json"

TEST_CATALOG = [
    ("TC-01", "0-RTT Ephemeral PDC & REPS Lifecycle", "tc01"),
    ("TC-02", "8:1 Incast Trimming, NACK & REPS Reroute", "tc02"),
    ("TC-03", "RTX-of-RTX & Tail/EOM Recovery", "tc03"),
    ("TC-04", "4-Algo Multipath Comparison", "tc04_reps"),
    ("TC-05", "Blackhole + REPS Freezing + PFLD/Sleek", "tc05"),
    ("TC-06", "RCCC Receiver-Driven Pull Pacing", "tc06"),
    ("TC-07", "SMaRTT ECN+Delay / QuickAdapt / FastIncrease", "tc07"),
    ("TC-08", "Full-Stack Hybrid All-to-All (240 flows, -failed 1)", None),
    ("TC-09", "SONiC/SAI Corner Cases & Switch-Centric (ARS/BTS)", "tc09a"),
    ("TC-10", "P4/RTL Bit-Exact .pcap & AXI512 .tv Golden Vectors", "tc02"),
]


class LiveStatusTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self.state = {
            "suite_status": "RUNNING",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "current_test": None,
            "heartbeat": None,
            "logs": [],
            "tests": {
                tid: {
                    "id": tid,
                    "scenario": desc,
                    "wire_view": wv,
                    "status": "PENDING",
                    "detail": "",
                    "duration_sec": None,
                }
                for tid, desc, wv in TEST_CATALOG
            },
        }
        self._flush()

    def _flush(self):
        du = shutil.disk_usage("/")
        self.state["disk"] = {
            "total_gb": round(du.total / (1024**3), 1),
            "used_gb": round(du.used / (1024**3), 1),
            "free_gb": round(du.free / (1024**3), 1),
            "used_pct": round(du.used * 100.0 / du.total, 1),
        }
        tmp = LIVE_STATUS_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2))
        os.replace(tmp, LIVE_STATUS_PATH)

    def start_test(self, tid: str):
        with self._lock:
            self.state["current_test"] = tid
            self.state["heartbeat"] = None
            self.state["tests"][tid]["status"] = "RUNNING"
            self.state["tests"][tid]["_t0"] = time.monotonic()
            self.state["logs"].append(f"[{tid}] Started")
            self.state["logs"] = self.state["logs"][-100:]
            self._flush()

    def update_heartbeat(self, sub_name: str, line: str):
        with self._lock:
            self.state["logs"].append(f"[{sub_name}] {line}")
            self.state["logs"] = self.state["logs"][-100:]
            m = re.search(
                r"sim_us=([\d.]+)/(\d+)\s+new=(\d+)\s+rtx=(\d+)\s+acks=(\d+)\s+sleek=(\d+)\s+trace_events=(\d+)\s+trace_bytes=(\d+)",
                line,
            )
            if m:
                self.state["heartbeat"] = {
                    "sub_name": sub_name,
                    "sim_us": float(m.group(1)),
                    "end_us": int(m.group(2)),
                    "new": int(m.group(3)),
                    "rtx": int(m.group(4)),
                    "acks": int(m.group(5)),
                    "sleek": int(m.group(6)),
                    "trace_events": int(m.group(7)),
                    "trace_bytes": int(m.group(8)),
                }
            self._flush()

    def finish_test(self, tid: str, passed: bool, detail: str, timed_out: bool = False):
        with self._lock:
            t = self.state["tests"][tid]
            t0 = t.pop("_t0", None)
            t["duration_sec"] = round(time.monotonic() - t0, 2) if t0 else None
            t["status"] = "TIMEOUT" if timed_out else ("PASS" if passed else "FAIL")
            t["detail"] = detail
            self.state["logs"].append(f"[{tid}] {t['status']} ({t['duration_sec']}s): {detail}")
            self.state["logs"] = self.state["logs"][-100:]
            self._flush()

    def finish_suite(self, all_pass: bool):
        with self._lock:
            self.state["suite_status"] = "PASS" if all_pass else "FAIL"
            self.state["current_test"] = None
            self.state["heartbeat"] = None
            self.state["finished_at"] = datetime.now(timezone.utc).isoformat()
            self._flush()


TRACKER: LiveStatusTracker | None = None


def _tail_lines(path: Path, n: int = 10) -> list[str]:
    if not path.exists():
        return []
    try:
        with path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 8192))
            lines = f.read().decode("utf-8", errors="replace").splitlines()
            return lines[-n:]
    except OSError:
        return []


def run_htsim(
    name: str,
    args: list[str],
    extra_env: dict[str, str] | None = None,
    trace: bool = True,
    timeout_sec: int = 30,
) -> dict:
    trace_file = REPORTS_DIR / f"{name}_trace.csv"
    out_dat = REPORTS_DIR / f"{name}_out.dat"
    env = os.environ.copy()
    if trace:
        env["MRC_TRACE_FILE"] = str(trace_file)
    else:
        env.pop("MRC_TRACE_FILE", None)
    if extra_env:
        env.update(extra_env)

    cmd = [str(BIN_UEC), "-o", str(out_dat)] + args
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    def _read_stream(stream, chunks, is_err=False):
        for line in stream:
            chunks.append(line)
            if is_err and ("[HEARTBEAT]" in line or "[FAIL_FAST]" in line or "[MrcTracer]" in line):
                msg = line.rstrip()
                print(f"[{name}] {msg}", flush=True)
                if TRACKER is not None:
                    TRACKER.update_heartbeat(name, msg)

    t_out = threading.Thread(target=_read_stream, args=(proc.stdout, stdout_chunks, False), daemon=True)
    t_err = threading.Thread(target=_read_stream, args=(proc.stderr, stderr_chunks, True), daemon=True)
    t_out.start()
    t_err.start()

    timed_out = False
    start_t = time.monotonic()
    while proc.poll() is None:
        if time.monotonic() - start_t > timeout_sec:
            timed_out = True
            proc.kill()
            print(f"[{name}] [FAIL_FAST] Exceeded timeout ({timeout_sec}s). Killed process.", file=sys.stderr, flush=True)
            tail = _tail_lines(trace_file, 5)
            if tail:
                print(f"[{name}] Last trace lines:\n  " + "\n  ".join(tail), file=sys.stderr, flush=True)
            break
        time.sleep(0.2)

    proc.wait()
    t_out.join(timeout=2)
    t_err.join(timeout=2)
    stdout = "".join(stdout_chunks) + "\n" + "".join(stderr_chunks)
    rc = -1 if timed_out else proc.returncode

    # Parse summary line: New: X Rtx: Y RTS: Z Bounced: B ACKs: A NACKs: N Pulls: P sleek_pkts: S
    m = re.search(
        r"New:\s*(\d+)\s+Rtx:\s*(\d+)\s+RTS:\s*(\d+)\s+Bounced:\s*(\d+)\s+ACKs:\s*(\d+)\s+NACKs:\s*(\d+)\s+Pulls:\s*(\d+)\s+sleek_pkts:\s*(\d+)",
        stdout,
    )
    hw_stats = {}
    if m:
        hw_stats = {
            "new": int(m.group(1)),
            "rtx": int(m.group(2)),
            "rts": int(m.group(3)),
            "bounced": int(m.group(4)),
            "acks": int(m.group(5)),
            "nacks": int(m.group(6)),
            "pulls": int(m.group(7)),
            "sleek": int(m.group(8)),
        }

    trace_stats = {}
    if trace and trace_file.exists():
        trace_stats = summarize_trace(trace_file, REPORTS_DIR / f"{name}_wire_view.md")

    return {
        "rc": rc,
        "hw": hw_stats,
        "trace": trace_stats,
        "trace_file": trace_file,
    }


def main():
    global TRACKER
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    TRACKER = LiveStatusTracker()
    results = []

    def record(tid: str, desc: str, ok: bool, detail: str):
        results.append((tid, desc, ok, detail))
        TRACKER.finish_test(tid, ok, detail)

    # TC-01: 0-RTT Ephemeral PDC + REPS + EOM
    TRACKER.start_test("TC-01")
    r1 = run_htsim("tc01", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc01_pdc_reps.cm"),
        "-sender_cc_only", "-sender_cc_algo", "nscc", "-load_balancing_algo", "reps",
        "-queue_type", "composite_ecn", "-q", "100", "-ecn", "20", "80",
        "-cwnd", "20", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "1000"
    ])
    c1 = r1["trace"].get("counts", {})
    p1 = (r1["rc"] == 0 and r1["trace"].get("syn_seen") and r1["trace"].get("eom_seen")
          and r1["trace"].get("unique_evs", 0) >= 4 and r1["hw"].get("new", 0) >= 64)
    record("TC-01", "0-RTT Ephemeral PDC & REPS Lifecycle", p1,
           f"New={r1['hw'].get('new')}, UniqueEVs={r1['trace'].get('unique_evs')}, SYN={r1['trace'].get('syn_seen')}, EOM={r1['trace'].get('eom_seen')}")

    # TC-02: 8:1 Incast Packet Trimming + NACK + REPS + QuickAdapt
    TRACKER.start_test("TC-02")
    r2 = run_htsim("tc02", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc02_incast_trim_nack.cm"),
        "-sender_cc_only", "-sender_cc_algo", "nscc", "-load_balancing_algo", "reps",
        "-queue_type", "composite_ecn", "-q", "16", "-ecn", "4", "12",
        "-cwnd", "40", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "2000"
    ])
    c2 = r2["trace"].get("counts", {})
    p2 = (r2["rc"] == 0 and c2.get("SW_TRIM", 0) > 0 and c2.get("TX_NACK", 0) > 0 and c2.get("TX_RTX", 0) > 0)
    record("TC-02", "8:1 Incast Trimming, NACK & REPS Reroute", p2,
           f"SW_TRIM={c2.get('SW_TRIM',0)}, TX_NACK={c2.get('TX_NACK',0)}, TX_RTX={c2.get('TX_RTX',0)}")

    # TC-03: RTX-of-RTX & Tail/EOM Loss Recovery
    TRACKER.start_test("TC-03")
    r3 = run_htsim("tc03", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc03_rtx_of_rtx_tail.cm"),
        "-sender_cc_only", "-sender_cc_algo", "nscc", "-load_balancing_algo", "reps",
        "-queue_type", "composite_ecn", "-q", "10", "-ecn", "3", "8",
        "-cwnd", "50", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "10000"
    ])
    c3 = r3["trace"].get("counts", {})
    p3 = (r3["rc"] == 0 and c3.get("TX_RTX", 0) > 0 and r3["trace"].get("eom_seen", False))
    record("TC-03", "RTX-of-RTX & Tail/EOM Recovery", p3,
           f"SW_TRIM={c3.get('SW_TRIM',0)}, TX_RTX={c3.get('TX_RTX',0)}, EOM={r3['trace'].get('eom_seen')}")

    # TC-04: 4 Multipath Algorithms Comparison (oblivious, bitmap, reps, mixed)
    TRACKER.start_test("TC-04")
    mp_summary = []
    p4 = True
    for algo in ["oblivious", "bitmap", "reps", "mixed"]:
        rmp = run_htsim(f"tc04_{algo}", [
            "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc04_mp_compare.cm"),
            "-sender_cc_only", "-sender_cc_algo", "nscc", "-load_balancing_algo", algo,
            "-queue_type", "composite_ecn", "-q", "24", "-ecn", "6", "18",
            "-cwnd", "30", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "2000"
        ], trace=(algo == "reps"))
        p4 = p4 and (rmp["rc"] == 0 and rmp["hw"].get("new", 0) > 0)
        mp_summary.append(f"{algo}:Rtx={rmp['hw'].get('rtx',0)}")
    record("TC-04", "4-Algo Multipath Comparison", p4, ", ".join(mp_summary))

    # TC-05: Link Failure (Blackhole) + REPS Freezing + PFLD/Sleek
    TRACKER.start_test("TC-05")
    r5 = run_htsim("tc05", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc05_blackhole_pfld.cm"),
        "-sender_cc_only", "-sender_cc_algo", "nscc", "-load_balancing_algo", "freezing",
        "-sleek", "-failed", "1",
        "-queue_type", "composite_ecn", "-q", "32", "-ecn", "8", "24",
        "-cwnd", "30", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "5000"
    ], extra_env={"MRC_BLACKHOLE_EV": "3"})
    c5 = r5["trace"].get("counts", {})
    p5 = (r5["rc"] == 0 and (r5["hw"].get("sleek", 0) > 0 or c5.get("TX_PROBE", 0) > 0 or r5["hw"].get("rtx", 0) > 0))
    record("TC-05", "Blackhole + REPS Freezing + PFLD/Sleek", p5,
           f"TX_PROBE={c5.get('TX_PROBE',0)}, sleek_pkts={r5['hw'].get('sleek',0)}, Rtx={r5['hw'].get('rtx',0)}")

    # TC-06: RCCC Receiver-Driven Pull Pacing
    TRACKER.start_test("TC-06")
    r6 = run_htsim("tc06", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc06_rccc_pull.cm"),
        "-receiver_cc_only", "-load_balancing_algo", "reps",
        "-queue_type", "composite", "-q", "24", "-ecn", "6", "18",
        "-cwnd", "8", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "5000"
    ])
    c6 = r6["trace"].get("counts", {})
    p6 = (r6["rc"] == 0 and r6["hw"].get("pulls", 0) > 0 and c6.get("RX_PULL", 0) > 0)
    record("TC-06", "RCCC Receiver-Driven Pull Pacing", p6,
           f"Pulls={r6['hw'].get('pulls',0)}, SW_TRIM={c6.get('SW_TRIM',0)}")

    # TC-07: SMaRTT ECN+Delay, QuickAdapt, FastIncrease
    TRACKER.start_test("TC-07")
    r7 = run_htsim("tc07", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc07_smartt_signals.cm"),
        "-sender_cc_only", "-sender_cc_algo", "nscc", "-load_balancing_algo", "reps",
        "-queue_type", "composite_ecn", "-q", "32", "-ecn", "6", "20",
        "-cwnd", "30", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "2000"
    ])
    c7 = r7["trace"].get("counts", {})
    p7 = (r7["rc"] == 0 and c7.get("SW_ECN", 0) > 0 and c7.get("RX_ACK", 0) > 0)
    record("TC-07", "SMaRTT ECN+Delay / QuickAdapt / FastIncrease", p7,
           f"SW_ECN={c7.get('SW_ECN',0)}, SW_TRIM={c7.get('SW_TRIM',0)}, ACKs={r7['hw'].get('acks',0)}")

    # TC-08: UEC Full-Stack Hybrid All-to-All Stress Test
    TRACKER.start_test("TC-08")
    r8 = run_htsim("tc08", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc08_full_hybrid_a2a.cm"),
        "-sender_cc", "-receiver_cc", "-sender_cc_algo", "nscc",
        "-load_balancing_algo", "reps", "-sleek", "-failed", "1",
        "-queue_type", "composite_ecn", "-q", "32", "-ecn", "8", "24",
        "-cwnd", "20", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "5000"
    ], trace=False)
    p8 = (r8["rc"] == 0 and r8["hw"].get("new", 0) >= 240 * 16)
    record("TC-08", "Full-Stack Hybrid All-to-All (240 flows, -failed 1)", p8,
           f"New={r8['hw'].get('new',0)}, Rtx={r8['hw'].get('rtx',0)}, Pulls={r8['hw'].get('pulls',0)}")

    # TC-09: SONiC/SAI Corner Cases & Switch-Centric ARS / BTS
    TRACKER.start_test("TC-09")
    r9a = run_htsim("tc09a", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc09a_dropdtt.cm"),
        "-sender_cc_only", "-sender_cc_algo", "nscc", "-load_balancing_algo", "reps", "-sleek",
        "-queue_type", "composite_ecn", "-q", "4", "-ecn", "2", "3",
        "-cwnd", "60", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "3000"
    ], extra_env={"MRC_TRIM_QUEUE_MAXSIZE": "64"})
    c9a = r9a["trace"].get("counts", {})

    r9b = run_htsim("tc09b", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc09b_double_trim_short.cm"),
        "-sender_cc_only", "-sender_cc_algo", "nscc", "-load_balancing_algo", "reps",
        "-queue_type", "composite_ecn", "-q", "16", "-ecn", "4", "12",
        "-cwnd", "40", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "2000"
    ])
    c9b = r9b["trace"].get("counts", {})

    r9c = run_htsim("tc09c_ars", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc02_incast_trim_nack.cm"),
        "-sender_cc_only", "-sender_cc_algo", "nscc", "-load_balancing_algo", "oblivious",
        "-strat", "ecmp_ar", "-ar_granularity", "packet", "-ar_method", "queue",
        "-queue_type", "composite_ecn", "-q", "16", "-ecn", "4", "12",
        "-cwnd", "40", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "2000"
    ])

    r9d = run_htsim("tc09d_bts", [
        "-nodes", "16", "-tiers", "3", "-tm", str(TRAFFIC_DIR / "tc09a_dropdtt.cm"),
        "-sender_cc_only", "-sender_cc_algo", "nscc", "-load_balancing_algo", "reps",
        "-queue_type", "composite_ecn", "-q", "4", "-ecn", "2", "3",
        "-cwnd", "60", "-mtu", "4096", "-paths", "16", "-linkspeed", "100000", "-end", "3000"
    ], extra_env={"MRC_ENABLE_BTS": "1", "MRC_BTS_ON_TRIM": "1"})
    c9d = r9d["trace"].get("counts", {})

    p9 = (r9a["rc"] == 0 and r9b["rc"] == 0 and r9c["rc"] == 0 and r9d["rc"] == 0
          and c9a.get("SW_DROPDTT", 0) > 0 and c9b.get("SW_TRIM", 0) > 0 and c9d.get("SW_BTS", 0) > 0)
    record("TC-09", "SONiC/SAI Corner Cases & Switch-Centric (ARS/BTS)", p9,
           f"9a_DROPDTT={c9a.get('SW_DROPDTT',0)}, 9b_TRIM={c9b.get('SW_TRIM',0)}, 9c_ARS_Rtx={r9c['hw'].get('rtx',0)}, 9d_BTS={c9d.get('SW_BTS',0)}/Bounced={r9d['hw'].get('bounced',0)}")

    # TC-10: Bit-Exact .pcap & AXI-Stream .tv Golden Vector Export & Verification
    TRACKER.start_test("TC-10")
    exp_stats = export_vectors(r2["trace_file"], REPORTS_DIR / "tc02")
    export_vectors(r1["trace_file"], REPORTS_DIR / "tc01")
    export_vectors(r5["trace_file"], REPORTS_DIR / "tc05")
    p10 = (exp_stats["full_count"] > 0 and exp_stats["trimmed_64b_verified"] > 0 and exp_stats["axi512_beats"] > 0)
    record("TC-10", "P4/RTL Bit-Exact .pcap & AXI512 .tv Golden Vectors", p10,
           f"tc02_full={exp_stats['full_count']} pkts, 64B_trimmed_verified={exp_stats['trimmed_64b_verified']}, axi512_beats={exp_stats['axi512_beats']}")

    # Write SUMMARY_REPORT.md
    lines = [
        "# MRC Simulation Verification Summary (`TC-01 ~ TC-10`)",
        "",
        "| Test ID | Scenario | Status | Key Metrics |",
        "| :--- | :--- | :---: | :--- |",
    ]
    all_pass = True
    for tid, desc, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        lines.append(f"| **{tid}** | {desc} | **{status}** | {detail} |")

    summary_path = REPORTS_DIR / "SUMMARY_REPORT.md"
    summary_path.write_text("\n".join(lines) + "\n")
    TRACKER.finish_suite(all_pass)
    print(summary_path.read_text())
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
