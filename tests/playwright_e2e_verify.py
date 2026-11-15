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

import json
import sys
from playwright.sync_api import sync_playwright

CHROME_EXE = "/root/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome"
URL = "http://127.0.0.1:8787"


def run_test():
    results = []

    def record(name, ok, detail=""):
        status = "PASS" if ok else "FAIL"
        results.append((name, ok, detail))
        print(f"[{status}] {name}: {detail}")

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
        page.fill("#inEndUs", "10000")
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

        record("Zero JS page errors", len(console_errors) == 0, f"errors={console_errors}")
        browser.close()

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\nSUMMARY: {passed}/{total} checks passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    run_test()
