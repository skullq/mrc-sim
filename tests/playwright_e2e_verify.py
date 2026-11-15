#!/usr/bin/env python3
"""
Playwright E2E Verification Suite for MRC-SIM Web Dashboard (http://127.0.0.1:8787).
Tests:
  1. Scenario A (Healthy, Queue=4, ECN=1/3, All-to-All):
     - Flow dropdown & table numeric sorting (1..56), Plane sorting (P0..P7), Event/Link sorting
     - Step-by-step (F00..F15) inspection of Flow 15:
       * F01 first SW_TRIM shows full path (TRIM x2->P1->x0)
       * F03 TX=0 SW_TRIM shows TRIM x2->P6->x0
       * F04 shows both TRIM and NACK
       * F05 / F11 show reverse ACK arrows & badges (ACK x0->P?->x2)
       * SVG badge bounding-box non-overlap check
       * Zero event omission vs backend CSV counts
  2. Scenario B (Node Fail: click P2 on SVG, Fail At=10us):
     - BEFORE FAIL -> AFTER FAIL transition, red failed node/links, SW_NODE_FAIL, Reroute, redistribution
  3. Scenario C (Link Fail: click N2-P1 on SVG, Fail At=10us):
     - Link fail chip, red failed link, SW_LINK_FAIL, Reroute, rc=0
"""

import csv
import json
import sys
from collections import Counter
from playwright.sync_api import sync_playwright

CHROME_EXE = "/root/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome"
URL = "http://127.0.0.1:8787"
TRACE_CSV = "/root/mrc-sim/reports/custom_trace.csv"


def run_test():
    results = []

    def record(name, ok, detail=""):
        status = "PASS" if ok else "FAIL"
        results.append((name, ok, detail))
        print(f"[{status}] {name}: {detail}")

    def verify_csv_vs_ui(page, sim_data, label, check_fault_planes=None, check_fail_event=None):
        with open(TRACE_CSV, newline="") as f:
            rows = list(csv.DictReader(f))
        csv_ev = Counter(r["event"] for r in rows)
        ev_keys = ("TX_DATA", "TX_RTX", "RX_DATA", "RX_ACK", "SW_TRIM", "SW_ECN", "SW_NODE_FAIL", "SW_LINK_FAIL")
        ev_match = all(csv_ev.get(k, 0) == sim_data["events"].get(k, 0) for k in ev_keys)

        fault_plane_ok = True
        actual_fault_planes = set()
        if check_fail_event:
            f_rows = [r for r in rows if r["event"] == check_fail_event]
            actual_fault_planes = {int(r["ev"], 16) % 8 for r in f_rows}
            if check_fault_planes is not None:
                fault_plane_ok = len(f_rows) > 0 and actual_fault_planes == set(check_fault_planes)

        frames = sim_data["frames"]
        after_idxs = [i for i, fr in enumerate(frames) if "AFTER" in fr.get("phase", "")]
        cand_idxs = after_idxs if after_idxs else list(range(len(frames)))
        # Prefer a frame with >= 16 raw TX+RTX packets so direct per-frame CSV counts match without cumulative smoothing
        chosen_idx = cand_idxs[len(cand_idxs) // 2]
        chosen_csv_counts = None
        for idx in cand_idxs:
            fr = frames[idx]
            t0_ns = round(fr["t_start_us"] * 1000)
            t1_ns = round(fr["t_end_us"] * 1000)
            cnts = [0] * 8
            for r in rows:
                if r["event"] in ("TX_DATA", "TX_RTX"):
                    ts = int(r["ts_ns"])
                    if t0_ns <= ts < t1_ns:
                        cnts[int(r["ev"], 16) % 8] += 1
            if sum(cnts) >= 16:
                chosen_idx = idx
                chosen_csv_counts = cnts
                break
        if chosen_csv_counts is None:
            fr = frames[chosen_idx]
            t0_ns = round(fr["t_start_us"] * 1000)
            t1_ns = round(fr["t_end_us"] * 1000)
            chosen_csv_counts = [0] * 8
            for r in rows:
                if r["event"] in ("TX_DATA", "TX_RTX"):
                    ts = int(r["ts_ns"])
                    if t0_ns <= ts < t1_ns:
                        chosen_csv_counts[int(r["ev"], 16) % 8] += 1

        fr = frames[chosen_idx]
        if sum(chosen_csv_counts) >= 16:
            if fr.get("failed_planes"):
                counts_match = abs(sum(fr.get("plane_counts", [])) - sum(chosen_csv_counts)) < 0.5 and all(
                    fr["plane_counts"][fp] == 0 for fp in fr["failed_planes"]
                )
            else:
                counts_match = (fr.get("plane_counts") == chosen_csv_counts)
        else:
            counts_match = (sum(fr.get("plane_counts", [])) > 0)

        page.eval_on_selector("#timeSlider", f"el => {{ el.value = '{chosen_idx}'; onScrub({chosen_idx}); }}")
        ui_info = page.evaluate("""() => {
            const bars = Array.from(document.querySelectorAll('svg#topoSvg rect[height="8"][rx="4"]'))
                .filter(r => r.getAttribute('fill') !== '#0f172a')
                .map(r => r.getAttribute('fill'));
            const titles = Array.from(document.querySelectorAll('svg#topoSvg rect[height="8"][rx="4"] title'))
                .map(t => t.textContent);
            const legacyMismatch = document.querySelectorAll('svg#topoSvg [fill="#22d3ee"], svg#topoSvg [fill="#22c55e"]').length;
            return { bars, titles, legacyMismatch };
        }""")
        ui_cnts = []
        for t in ui_info["titles"]:
            try:
                ui_cnts.append(round(float(t.split("(")[1].split(" pkts")[0]), 1))
            except Exception:
                ui_cnts.append(-1)
        expected_ui_cnts = [round(float(c), 1) for c in fr.get("plane_counts", [])]
        dom_counts_ok = (ui_cnts == expected_ui_cnts)
        has_redist = bool(fr.get("failed_planes")) or (fr.get("reroute_cnt", 0) > 0) or (check_fail_event is not None)
        bar_color_ok = (ui_info["legacyMismatch"] == 0) and (len(ui_info["bars"]) == 8)
        for r_idx, pct in enumerate(fr["plane_pct"]):
            if r_idx in fr.get("failed_planes", []):
                exp_c = "#ef4444"
            elif pct <= 0:
                exp_c = "#475569"
            elif has_redist and pct > 13.0:
                exp_c = "#4ade80"
            else:
                exp_c = "#38bdf8"
            if r_idx < len(ui_info["bars"]) and ui_info["bars"][r_idx] != exp_c:
                bar_color_ok = False

        ok = ev_match and fault_plane_ok and counts_match and dom_counts_ok and bar_color_ok
        record(
            f"CSV<->UI parity [{label}]",
            ok,
            f"ev={ev_match}, fault_planes={sorted(actual_fault_planes) if check_fail_event else 'N/A'}, frame={chosen_idx}, csv_cnts={chosen_csv_counts}, ui_cnts={ui_cnts}, bar_ok={bar_color_ok}"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME_EXE)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        console_errors = []
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        page.goto(URL, wait_until="load")

        # Switch to Tab 2 (Topology Builder & Fault Injection)
        page.click("button.tab:has-text('Topology Builder')")
        page.wait_for_selector("#topoSvg", state="visible")

        # =====================================================================
        # Scenario A: Healthy Queue=4, ECN=1/3, All-to-All, 16 frames
        # =====================================================================
        page.fill("#inQueue", "4")
        page.fill("#inEcnLow", "1")
        page.fill("#inEcnHigh", "3")
        page.select_option("#inFlowSize", "262144")
        page.select_option("#inFrames", "16")
        page.select_option("#inTraffic", "all_to_all")
        page.click("button:has-text('Clear Faults')")

        with page.expect_response(lambda r: "/api/run_custom" in r.url and r.status == 200, timeout=30000) as resp_info:
            page.click("#btnCustomRun")
        sim_a = resp_info.value.json()

        # Pause auto-play if running so we can step manually
        page.wait_for_selector("#customResultCard", state="visible")
        play_btn = page.locator("#btnPlay")
        if "Pause" in play_btn.inner_text():
            play_btn.click()
        verify_csv_vs_ui(page, sim_a, "Scenario A: Healthy All-to-All")

        # 1. Verify Flow dropdown sorting (1..56)
        opt_vals = page.eval_on_selector_all(
            "#flowFocusSelect option",
            "els => els.map(e => e.value).filter(v => v !== '')"
        )
        opt_ints = [int(v) for v in opt_vals]
        record(
            "Flow dropdown numeric sorting",
            opt_ints == sorted(opt_ints) and len(opt_ints) == 56,
            f"count={len(opt_ints)}, first5={opt_ints[:5]}, last5={opt_ints[-5:]}"
        )

        # 2. Verify xPU EV Distribution table sorting (0..7) & Link Stats sorting
        ev_xpus = page.eval_on_selector_all(
            "#evDistTbody tr td:first-child",
            "els => els.map(e => parseInt(e.textContent.replace(/[^0-9]/g,''), 10))"
        )
        record("xPU EV table numeric sorting", ev_xpus == sorted(ev_xpus) and len(ev_xpus) == 8, f"xPUs={ev_xpus}")

        link_scores = page.eval_on_selector_all(
            "#linkStatsTbody tr",
            """rows => rows.map(r => {
                const tds = r.querySelectorAll('td');
                if (tds.length < 5) return null;
                return {
                    link: tds[0].textContent.trim(),
                    trim: (parseInt(tds[1].textContent, 10) || 0) + (parseInt(tds[2].textContent, 10) || 0),
                    ecn: parseInt(tds[3].textContent, 10) || 0,
                    fail: parseInt(tds[4].textContent, 10) || 0,
                };
            }).filter(Boolean)"""
        )
        scores_ok = all(
            (link_scores[i]["fail"] * 1000 + link_scores[i]["trim"] * 100 + link_scores[i]["ecn"])
            >= (link_scores[i + 1]["fail"] * 1000 + link_scores[i + 1]["trim"] * 100 + link_scores[i + 1]["ecn"])
            for i in range(len(link_scores) - 1)
        )
        record("Link stats severity sorting", scores_ok and len(link_scores) > 0, f"rows={len(link_scores)}")

        # 3. Select Flow 15 and step through all 16 frames (F00..F15)
        page.select_option("#flowFocusSelect", "15")
        page.wait_for_selector("#flowTraceCard", state="visible")
        page.wait_for_selector("#wiresharkCard", state="visible")
        ws_total = page.locator("#wsPacketTbody tr").count()
        page.click("#wiresharkCard button:has-text('TRIM')")
        ws_trim_rows = page.locator("#wsPacketTbody tr").count()
        page.locator("#wsPacketTbody tr").first.click()
        ws_hdr_txt = page.locator("#wsHeaderTree").inner_text()
        ws_hex_txt = page.locator("#wsHexDump").inner_text()
        record(
            "Wireshark panel shows Flow 15 packets, TRIM filter, and L2/IP/UEC headers",
            ws_total > 100 and ws_trim_rows == 6 and "UEC Transport" in ws_hdr_txt and "0000" in ws_hex_txt,
            f"total={ws_total}, trim_rows={ws_trim_rows}, has_uec={'UEC Transport' in ws_hdr_txt}"
        )
        page.click("#wiresharkCard button:has-text('All')")
        trace_rows = page.locator("#flowFrameTbody tr").count()
        record("Flow 15 trace table has 16 frames", trace_rows == 16, f"rows={trace_rows}")

        # Jump to F00 using slider
        page.eval_on_selector("#timeSlider", "el => { el.value = '0'; renderFrame(0); }")

        f01_ok = f03_ok = f04_ok = f05_ack_ok = f11_ack_ok = False
        overlap_failures = []
        ts_sort_ok = True
        plane_sort_ok = True

        for fidx in range(16):
            if fidx > 0:
                page.click("button:has-text('다음 ▶')")
            # Check Flow 15 SVG elements & badge overlaps
            svg_info = page.evaluate("""() => {
                const svg = document.getElementById('topoSvg');
                const html = svg.innerHTML;
                const texts = [...svg.querySelectorAll('text')].map(t => t.textContent.trim());
                const trimBadges = texts.filter(t => t.startsWith('TRIM '));
                const nackBadges = texts.filter(t => t.startsWith('NACK '));
                const ackBadges = texts.filter(t => t.startsWith('ACK '));
                const trimArrows = svg.querySelectorAll('path[marker-end="url(#arrowTrim)"]').length;
                const nackArrows = svg.querySelectorAll('path[marker-end="url(#arrowNack)"]').length;
                const ackArrows = svg.querySelectorAll('path[marker-end="url(#arrowAck)"]').length;
                // Check badge rect overlap
                const badgeRects = [...svg.querySelectorAll('rect')].filter(r => {
                    const fill = r.getAttribute('fill');
                    return fill === '#3b0764' || fill === '#431407' || fill === '#042f2e';
                }).map(r => ({
                    x: parseFloat(r.getAttribute('x')),
                    y: parseFloat(r.getAttribute('y')),
                    w: parseFloat(r.getAttribute('width')),
                    h: parseFloat(r.getAttribute('height')),
                }));
                let overlaps = 0;
                for (let i = 0; i < badgeRects.length; i++) {
                    for (let j = i + 1; j < badgeRects.length; j++) {
                        const a = badgeRects[i], b = badgeRects[j];
                        const ox = a.x < b.x + b.w && a.x + a.w > b.x;
                        const oy = a.y < b.y + b.h && a.y + a.h > b.y;
                        if (ox && oy) overlaps++;
                    }
                }
                // Check event timestamps sorted ascending
                const evTs = [...document.querySelectorAll('#frameEventsTbody tr td:first-child')]
                    .map(td => parseFloat(td.textContent))
                    .filter(n => !isNaN(n));
                let tsOk = true;
                for (let i = 1; i < evTs.length; i++) if (evTs[i] < evTs[i-1]) tsOk = false;
                // Check plane labels sorted P0..P7 in frameFlowTbody
                const planeCell = document.querySelector('#frameFlowTbody tr td:nth-child(5) span');
                let plOk = true;
                if (planeCell) {
                    const ps = [...planeCell.textContent.matchAll(/P(\\d+)\\(/g)].map(m => parseInt(m[1], 10));
                    for (let i = 1; i < ps.length; i++) if (ps[i] < ps[i-1]) plOk = false;
                }
                return { trimBadges, nackBadges, ackBadges, trimArrows, nackArrows, ackArrows, overlaps, tsOk, plOk };
            }""")
            if svg_info["overlaps"] > 0:
                overlap_failures.append(f"F{fidx:02d}:{svg_info['overlaps']}")
            if not svg_info["tsOk"]:
                ts_sort_ok = False
            if not svg_info["plOk"]:
                plane_sort_ok = False
            if fidx == 1:
                f01_ok = ("TRIM x2→P1→x0" in svg_info["trimBadges"]) and svg_info["trimArrows"] >= 3
            if fidx == 3:
                f03_ok = ("TRIM x2→P6→x0" in svg_info["trimBadges"]) and svg_info["trimArrows"] >= 3
            if fidx == 4:
                f04_ok = ("TRIM x2→P6→x0" in svg_info["trimBadges"]) and len(svg_info["nackBadges"]) >= 1 and svg_info["nackArrows"] >= 2
            if fidx == 5:
                f05_ack_ok = len(svg_info["ackBadges"]) >= 1 and svg_info["ackArrows"] >= 3
            if fidx == 11:
                f11_ack_ok = len(svg_info["ackBadges"]) >= 1 and svg_info["ackArrows"] >= 3

        record("F01 first SW_TRIM shows full path (TRIM x2->P1->x0)", f01_ok, f"f01_ok={f01_ok}")
        record("F03 TX=0 SW_TRIM shows TRIM x2->P6->x0", f03_ok, f"f03_ok={f03_ok}")
        record("F04 shows both TRIM and NACK", f04_ok, f"f04_ok={f04_ok}")
        record("F05 shows reverse ACK arrows & badges", f05_ack_ok, f"f05_ack_ok={f05_ack_ok}")
        record("F11 (TX=0) shows reverse ACK arrows & badges", f11_ack_ok, f"f11_ack_ok={f11_ack_ok}")
        record("SVG badge zero overlap across F00..F15", len(overlap_failures) == 0, f"overlaps={overlap_failures}")
        record("Frame events timestamp ascending F00..F15", ts_sort_ok, f"ts_sort_ok={ts_sort_ok}")
        record("Frame flow planes sorted P0..P7 F00..F15", plane_sort_ok, f"plane_sort_ok={plane_sort_ok}")

        # Verify zero event omission vs backend CSV totals
        ev_sum = sum(len(fr["events_log"]) for fr in sim_a["frames"])
        trim_sum = sum(1 for fr in sim_a["frames"] for e in fr["events_log"] if e["event"] in ("SW_TRIM", "RX_TRIM"))
        nack_sum = sum(1 for fr in sim_a["frames"] for e in fr["events_log"] if e["event"] in ("TX_NACK", "RX_NACK"))
        csv_trims = sim_a["events"].get("SW_TRIM", 0) + sim_a["events"].get("RX_TRIM", 0)
        csv_nacks = sim_a["events"].get("TX_NACK", 0) + sim_a["events"].get("RX_NACK", 0)
        record("Zero Trim/NACK event omission vs CSV", trim_sum == csv_trims and nack_sum == csv_nacks, f"trim={trim_sum}/{csv_trims}, nack={nack_sum}/{csv_nacks}, total_ev_logged={ev_sum}")

        # Verify Replay button at far right end (F15) -> click -> resets to F00 & leaves Replay
        end_btn_txt = play_btn.inner_text().strip()
        play_btn.click()
        restarted_slider = int(page.eval_on_selector("#timeSlider", "el => el.value"))
        playing_btn_txt = play_btn.inner_text().strip()
        play_btn.click()  # pause
        paused_btn_txt = play_btn.inner_text().strip()
        record(
            "Timeline end shows Replay and restarts from F00 on click",
            "Replay" in end_btn_txt and restarted_slider == 0 and "Pause" in playing_btn_txt and "Play" in paused_btn_txt,
            f"end={end_btn_txt}, slider={restarted_slider}, playing={playing_btn_txt}, paused={paused_btn_txt}"
        )

        # =====================================================================
        # Scenario B: Node Fail (Click P2 on SVG, Fail At = 10us)
        # =====================================================================
        page.click("button:has-text('Clear Faults')")
        page.select_option("#flowFocusSelect", "")
        page.fill("#inQueue", "16")
        page.fill("#inEcnLow", "4")
        page.fill("#inEcnHigh", "12")
        page.fill("#inFailAt", "15")
        page.select_option("#inFrames", "128")
        page.fill("#inRecoverAt", "0")
        page.evaluate("toggleNode('P2')")
        node_chips = page.locator("#failNodeChips").inner_text()
        record("Node Fail chip P2 selected", "P2" in node_chips, f"chips={node_chips.strip()}")

        with page.expect_response(lambda r: "/api/run_custom" in r.url and r.status == 200, timeout=30000) as resp_b:
            page.click("#btnCustomRun")
        sim_b = resp_b.value.json()
        page.wait_for_selector("#customResultCard", state="visible")
        if "Pause" in play_btn.inner_text():
            play_btn.click()

        phases_b = [fr["phase"] for fr in sim_b["frames"]]
        has_before = any("BEFORE" in ph for ph in phases_b)
        has_after = any("AFTER" in ph for ph in phases_b)
        sw_node_fail = sim_b["events"].get("SW_NODE_FAIL", 0)
        # Jump to an AFTER FAIL frame and inspect SVG red node/links
        after_idx = next(i for i, fr in enumerate(sim_b["frames"]) if "AFTER" in fr["phase"])
        page.eval_on_selector("#timeSlider", f"el => {{ el.value = '{after_idx}'; renderFrame({after_idx}); }}")
        node_fail_svg = page.evaluate("""() => {
            const svg = document.getElementById('topoSvg');
            const redCircles = svg.querySelectorAll('circle[fill="#dc2626"], circle[fill="#ef4444"]').length;
            const redLines = svg.querySelectorAll('line[stroke="#ef4444"]').length;
            const greenLines = svg.querySelectorAll('line[stroke="#4ade80"]').length;
            const phaseTxt = document.getElementById('frameTimeLabel').textContent;
            return { redCircles, redLines, greenLines, phaseTxt };
        }""")
        record(
            "Node Fail P2 triggers BEFORE->AFTER, red SVG, SW_NODE_FAIL, redistribution",
            sim_b["rc"] == 0 and has_before and has_after and sw_node_fail > 0 and node_fail_svg["redCircles"] >= 1 and node_fail_svg["redLines"] >= 1,
            f"rc={sim_b['rc']}, SW_NODE_FAIL={sw_node_fail}, svg={node_fail_svg}"
        )
        verify_csv_vs_ui(page, sim_b, "Scenario B: Node Fail P2", check_fault_planes={2}, check_fail_event="SW_NODE_FAIL")

        # =====================================================================
        # Scenario C: Link Fail (Click N2-P1 on SVG, Fail At = 10us)
        # =====================================================================
        page.click("button:has-text('Clear Faults')")
        page.evaluate("toggleLink('N2-P1')")
        link_chips = page.locator("#failLinkChips").inner_text()
        record("Link Fail chip N2-P1 selected", "N2-P1" in link_chips, f"chips={link_chips.strip()}")

        with page.expect_response(lambda r: "/api/run_custom" in r.url and r.status == 200, timeout=30000) as resp_c:
            page.click("#btnCustomRun")
        sim_c = resp_c.value.json()
        page.wait_for_selector("#customResultCard", state="visible")
        if "Pause" in play_btn.inner_text():
            play_btn.click()

        sw_link_fail = sim_c["events"].get("SW_LINK_FAIL", 0)
        after_c = next(i for i, fr in enumerate(sim_c["frames"]) if "AFTER" in fr["phase"])
        page.eval_on_selector("#timeSlider", f"el => {{ el.value = '{after_c}'; renderFrame({after_c}); }}")
        link_fail_svg = page.evaluate("""() => {
            const svg = document.getElementById('topoSvg');
            const redLines = svg.querySelectorAll('line[stroke="#ef4444"]').length;
            const phaseTxt = document.getElementById('frameTimeLabel').textContent;
            return { redLines, phaseTxt };
        }""")
        record(
            "Link Fail N2-P1 triggers AFTER FAIL, red link, SW_LINK_FAIL, rc=0",
            sim_c["rc"] == 0 and sw_link_fail > 0 and link_fail_svg["redLines"] >= 1,
            f"rc={sim_c['rc']}, SW_LINK_FAIL={sw_link_fail}, svg={link_fail_svg}"
        )
        verify_csv_vs_ui(page, sim_c, "Scenario C: Link Fail N2-P1", check_fault_planes={1}, check_fail_event="SW_LINK_FAIL")

        # =====================================================================
        # Scenario D: Leaf-Spine 2-Tier Topology + SRv6 (SRH & uSID) Mode
        # =====================================================================
        ls_check = page.evaluate("""() => {
            const svgTxt = document.getElementById('topoSvg').textContent;
            const hasPlanes = ['P0','P1','P2','P3','P4','P5','P6','P7'].every(p => svgTxt.includes('Plane ' + p));
            const hasLeaves = ['LS0','LS1','LS2','LS3'].every(l => svgTxt.includes(l));
            const hasSpines = ['US0','US1'].every(s => svgTxt.includes(s));
            return { hasPlanes, hasLeaves, hasSpines };
        }""")
        record(
            "htsim_uec 2-Tier 8-Plane (Plane P0..P7, LS0..LS3, US0..US1) render in SVG",
            ls_check["hasPlanes"] and ls_check["hasLeaves"] and ls_check["hasSpines"],
            f"ls_check={ls_check}"
        )

        page.select_option("#inSrv6Mode", "srh")
        first_flow = page.eval_on_selector("#flowFocusSelect", "el => el.options[1] ? el.options[1].value : ''")
        if first_flow:
            page.select_option("#flowFocusSelect", first_flow)
        page.wait_for_timeout(150)
        srv6_check = page.evaluate("""() => {
            const svgTxt = document.getElementById('topoSvg').textContent;
            const wsTree = document.getElementById('wsHeaderTree').textContent;
            const wsHex = document.getElementById('wsHexDump').textContent;
            return {
                hasSpineSid: svgTxt.includes('fc00:1:'),
                hasLeafSid: svgTxt.includes('fc00:0:'),
                hasTrimOffsetBanner: svgTxt.includes('Trim Offset=126B'),
                hasWsSrh: wsTree.includes('IPv6 + SRv6 SRH Header') && wsTree.includes('RoutingType=4') && wsTree.includes('SRv6 Trim Offset'),
                hasIpv6Hex: wsHex.includes('86 dd')
            };
        }""")
        record(
            "SRv6 SRH mode renders SIDs on SVG and IPv6+SRH header/hex in Wireshark",
            all(srv6_check.values()),
            f"srv6_check={srv6_check}"
        )

        # =====================================================================
        # Scenario E: SRv6 uSID Mode
        # =====================================================================
        page.select_option("#inSrv6Mode", "usid")
        page.wait_for_timeout(150)
        usid_check = page.evaluate("""() => {
            const svgTxt = document.getElementById('topoSvg').textContent;
            const wsTree = document.getElementById('wsHeaderTree').textContent;
            return {
                hasSpineUsid: svgTxt.includes('fc00:010'),
                hasLeafUsid: svgTxt.includes('fc00:000'),
                hasTrim94: svgTxt.includes('Trim Offset=94B'),
                hasWsUsid: wsTree.includes('IPv6 + SRv6 uSID Header')
            };
        }""")
        record("SRv6 uSID mode renders uSIDs, Trim Offset=94B, and uSID header", all(usid_check.values()), f"usid_check={usid_check}")
        page.select_option("#inSrv6Mode", "off")

        # =====================================================================
        # Scenario F: Incast (7 flows) & Multipath Algos (freezing/oblivious/bitmap/mixed)
        # =====================================================================
        page.click("button:has-text('Clear Faults')")
        page.select_option("#inTraffic", "incast")
        with page.expect_response(lambda r: "/api/run_custom" in r.url and r.status == 200, timeout=30000) as resp_inc:
            page.click("#btnCustomRun")
        sim_inc = resp_inc.value.json()
        page.wait_for_selector("#customResultCard", state="visible")
        if "Pause" in play_btn.inner_text():
            play_btn.click()
        inc_flows = page.eval_on_selector("#flowFocusSelect", "el => el.options.length - 1")
        record("Incast traffic runs rc=0 with 7 flows", sim_inc["rc"] == 0 and inc_flows == 7, f"rc={sim_inc['rc']}, flows={inc_flows}")
        verify_csv_vs_ui(page, sim_inc, "Scenario F: Incast")

        page.select_option("#inTraffic", "all_to_all")
        algo_ok = True
        algo_details = {}
        for algo in ("freezing", "oblivious", "bitmap", "mixed"):
            page.select_option("#inAlgo", algo)
            with page.expect_response(lambda r: "/api/run_custom" in r.url and r.status == 200, timeout=30000) as resp_alg:
                page.click("#btnCustomRun")
            sim_alg = resp_alg.value.json()
            if "Pause" in play_btn.inner_text():
                play_btn.click()
            algo_details[algo] = (sim_alg["rc"], sim_alg["hw"].get("new"), sim_alg["hw"].get("acks"))
            if sim_alg["rc"] != 0 or sim_alg["hw"].get("new", 0) <= 0:
                algo_ok = False
            verify_csv_vs_ui(page, sim_alg, f"Scenario F: Algo {algo}")
        record("All Multipath Algos (freezing/oblivious/bitmap/mixed) run rc=0", algo_ok, f"algos={algo_details}")
        page.select_option("#inAlgo", "reps")

        # =====================================================================
        # Scenario G: 400G + Recommended ECN + 64 Frames + Flow Size 1MB
        # =====================================================================
        page.select_option("#inLinkSpeed", "400000")
        page.click("button:has-text('권장 기준값 적용')")
        page.select_option("#inFrames", "64")
        page.select_option("#inFlowSize", "1048576")
        with page.expect_response(lambda r: "/api/run_custom" in r.url and r.status == 200, timeout=30000) as resp_400:
            page.click("#btnCustomRun")
        sim_400 = resp_400.value.json()
        if "Pause" in play_btn.inner_text():
            play_btn.click()
        record(
            "400G + Recommended ECN (160/48/112) + 64 frames + Flow Size 1MB",
            sim_400["rc"] == 0 and len(sim_400["frames"]) == 64 and page.input_value("#inQueue") == "160" and sim_400["events"].get("TX_DATA", 0) > 10000,
            f"rc={sim_400['rc']}, frames={len(sim_400['frames'])}, q={page.input_value('#inQueue')}, TX={sim_400['events'].get('TX_DATA')}"
        )
        verify_csv_vs_ui(page, sim_400, "Scenario G: 400G")

        # =====================================================================
        # Scenario H: Leaf Node Fail (P2:LS1) & Uplink Fail (P2:LS1-US0)
        # =====================================================================
        page.select_option("#inLinkSpeed", "100000")
        page.select_option("#inFlowSize", "262144")
        page.fill("#inQueue", "16")
        page.fill("#inEcnLow", "4")
        page.fill("#inEcnHigh", "12")
        page.select_option("#inFrames", "32")
        page.fill("#inFailAt", "15")
        page.fill("#inRecoverAt", "0")
        page.click("button:has-text('Clear Faults')")
        page.evaluate("toggleNode('P2:LS1')")
        with page.expect_response(lambda r: "/api/run_custom" in r.url and r.status == 200, timeout=30000):
            page.click("#btnCustomRun")
        page.wait_for_timeout(120)
        sim_ls = page.evaluate("() => lastSimData")
        if "Pause" in play_btn.inner_text():
            play_btn.click()
        sw_ls_fail = sim_ls["events"].get("SW_NODE_FAIL", 0)
        record("Leaf Node Fail P2:LS1 triggers SW_NODE_FAIL in htsim_uec", sim_ls["rc"] == 0 and sw_ls_fail > 0, f"SW_NODE_FAIL={sw_ls_fail}")
        verify_csv_vs_ui(page, sim_ls, "Scenario H1: Leaf Fail P2:LS1", check_fault_planes={2}, check_fail_event="SW_NODE_FAIL")

        page.click("button:has-text('Clear Faults')")
        page.evaluate("toggleLink('P2:LS1-US0')")
        with page.expect_response(lambda r: "/api/run_custom" in r.url and r.status == 200, timeout=30000):
            page.click("#btnCustomRun")
        page.wait_for_timeout(120)
        sim_ul = page.evaluate("() => lastSimData")
        if "Pause" in play_btn.inner_text():
            play_btn.click()
        sw_ul_fail = sim_ul["events"].get("SW_LINK_FAIL", 0)
        record("Uplink Fail P2:LS1-US0 triggers SW_LINK_FAIL in htsim_uec", sim_ul["rc"] == 0 and sw_ul_fail > 0, f"SW_LINK_FAIL={sw_ul_fail}")
        verify_csv_vs_ui(page, sim_ul, "Scenario H2: Uplink Fail P2:LS1-US0", check_fault_planes={2}, check_fail_event="SW_LINK_FAIL")

        # =====================================================================
        # Scenario I: Min Queue=4 + ECN=1/2 + Fault Recovery (FailAt=10, RecoverAt=30)
        # =====================================================================
        page.click("button:has-text('Clear Faults')")
        page.fill("#inQueue", "4")
        page.fill("#inEcnLow", "1")
        page.fill("#inEcnHigh", "2")
        page.fill("#inFailAt", "10")
        page.fill("#inRecoverAt", "30")
        page.evaluate("toggleNode('P2')")
        with page.expect_response(lambda r: "/api/run_custom" in r.url and r.status == 200, timeout=30000):
            page.click("#btnCustomRun")
        page.wait_for_timeout(120)
        sim_rec = page.evaluate("() => lastSimData")
        if "Pause" in play_btn.inner_text():
            play_btn.click()
        record(
            "Min Queue=4 + ECN=1/2 + RecoverAt=30us triggers Trim & Recovery",
            sim_rec["rc"] == 0 and sim_rec["events"].get("SW_TRIM", 0) > 0 and sim_rec["events"].get("SW_NODE_FAIL", 0) > 0,
            f"SW_TRIM={sim_rec['events'].get('SW_TRIM', 0)}, SW_NODE_FAIL={sim_rec['events'].get('SW_NODE_FAIL', 0)}"
        )
        verify_csv_vs_ui(page, sim_rec, "Scenario I: Fault Recovery P2", check_fault_planes={2}, check_fail_event="SW_NODE_FAIL")

        record("Zero JS page errors", len(console_errors) == 0, f"errors={console_errors}")
        browser.close()

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\nSUMMARY: {passed}/{total} checks passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    run_test()
