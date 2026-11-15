#!/usr/bin/env python3
"""
web_dashboard.py
Real-time Web Dashboard + Interactive Fat-Tree Topology & Fault-Injection UI
for MRC Simulation Suite (TC-01 ~ TC-10 & Custom Topology Runs).
"""

import argparse
import csv
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path("/root/mrc-sim")
REPORTS_DIR = ROOT / "reports"
LIVE_STATUS_PATH = REPORTS_DIR / "live_status.json"
RUNNER_SCRIPT = ROOT / "scripts/run_all_tests.py"
BIN_UEC = ROOT / "htsim/htsim/sim/datacenter/htsim_uec"

_PROC_LOCK = threading.Lock()
_RUNNER_PROC: subprocess.Popen | None = None

HTML_PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>MRC-SIM Real-Time Test & Topology Dashboard</title>
<style>
  :root {
    --bg: #0f172a; --card: #1e293b; --border: #334155;
    --text: #f1f5f9; --muted: #94a3b8;
    --pass: #22c55e; --fail: #ef4444; --run: #38bdf8; --pend: #64748b; --warn: #f59e0b;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: var(--bg); color: var(--text); padding: 20px; }
  .container { max-width: 1320px; margin: 0 auto; }
  header { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 18px; }
  h1 { margin: 0; font-size: 1.4rem; }
  h2 { margin: 0 0 12px 0; font-size: 1.1rem; }
  .controls { display: flex; gap: 10px; align-items: center; }
  button { padding: 8px 14px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 0.88rem; }
  .btn-run { background: #2563eb; color: #fff; }
  .btn-run:disabled { background: #334155; color: var(--muted); cursor: not-allowed; }
  .btn-stop { background: #dc2626; color: #fff; }
  .btn-stop:disabled { background: #334155; color: var(--muted); cursor: not-allowed; }
  .btn-view { background: #334155; color: #e2e8f0; padding: 5px 10px; font-size: 0.8rem; }
  .tabs { display: flex; gap: 8px; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
  .tab { background: var(--card); color: var(--muted); border: 1px solid var(--border); }
  .tab.active { background: #2563eb; color: #fff; border-color: #2563eb; }
  .panel { display: none; }
  .panel.active { display: block; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin-bottom: 16px; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; }
  .label { font-size: 0.76rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
  .val { font-size: 1.35rem; font-weight: 700; margin-top: 4px; }
  .progress-wrap { background: #0b1220; border-radius: 999px; height: 12px; overflow: hidden; margin-top: 8px; border: 1px solid var(--border); }
  .progress-bar { height: 100%; background: linear-gradient(90deg, #38bdf8, #22c55e); transition: width 0.3s ease; width: 0%; }
  .hb-box { background: #0c1a2e; border: 1px solid #0284c7; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; display: none; }
  .hb-box.active { display: block; }
  .hb-metrics { display: flex; flex-wrap: wrap; gap: 18px; margin-top: 6px; font-family: ui-monospace, monospace; font-size: 0.88rem; }
  table { width: 100%; border-collapse: collapse; background: var(--card); border-radius: 10px; overflow: hidden; border: 1px solid var(--border); }
  th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.88rem; }
  th { background: #162032; color: var(--muted); font-size: 0.76rem; text-transform: uppercase; }
  tr:last-child td { border-bottom: none; }
  .badge { display: inline-block; padding: 3px 9px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }
  .PASS { background: rgba(34,197,94,0.18); color: var(--pass); }
  .FAIL, .TIMEOUT { background: rgba(239,68,68,0.18); color: var(--fail); }
  .RUNNING { background: rgba(56,189,248,0.18); color: var(--run); }
  .PENDING { background: rgba(100,116,139,0.2); color: var(--muted); }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.82rem; }
  .logs { margin-top: 16px; background: #0b1220; border: 1px solid var(--border); border-radius: 10px; padding: 12px;
          height: 190px; overflow-y: auto; font-family: ui-monospace, monospace; font-size: 0.8rem; color: #cbd5e1; }
  .form-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; margin-bottom: 14px; }
  .field { display: flex; flex-direction: column; gap: 4px; }
  .field label { font-size: 0.78rem; color: var(--muted); }
  .field input, .field select { background: #0b1220; border: 1px solid var(--border); color: var(--text);
                                padding: 7px 10px; border-radius: 6px; font-size: 0.88rem; min-width: 110px; }
  .topo-wrap { background: #0b1220; border: 1px solid var(--border); border-radius: 10px; padding: 12px; overflow-x: auto; }
  @keyframes flowDash { to { stroke-dashoffset: -24; } }
  .flow-anim { animation: flowDash 0.9s linear infinite; }
  .chip-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
  .chip { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid #ef4444; border-radius: 999px;
          padding: 3px 10px; font-size: 0.78rem; font-family: ui-monospace, monospace; cursor: pointer; }
  .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); align-items: center; justify-content: center; padding: 20px; z-index: 50; }
  .modal.open { display: flex; }
  .modal-body { background: var(--card); border: 1px solid var(--border); border-radius: 10px; max-width: 960px; width: 100%;
                max-height: 85vh; display: flex; flex-direction: column; }
  .modal-head { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid var(--border); }
  .modal-pre { padding: 16px; overflow: auto; margin: 0; font-family: ui-monospace, monospace; font-size: 0.82rem; white-space: pre-wrap; color: #e2e8f0; }
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>MRC-SIM Real-Time Verification &amp; Topology Studio</h1>
      <div class="label" id="suiteMeta">Loading status...</div>
    </div>
  </header>

  <div class="tabs">
    <button class="tab active" onclick="switchTab('topo', this)">Topology Builder &amp; Fault Injection</button>
    <button class="tab" onclick="switchTab('suite', this)">Test Suite (TC-01 ~ TC-10)</button>
  </div>

  <!-- TAB 1: Suite -->
  <div id="tab-suite" class="panel">
    <div class="controls" style="justify-content:flex-end; margin-bottom:12px">
      <button class="btn-run" id="btnRun" onclick="runSuite()">Run All Tests</button>
      <button class="btn-stop" id="btnStop" onclick="stopSuite()" disabled>Stop</button>
    </div>
    <div class="grid">
      <div class="card">
        <div class="label">Suite Status</div>
        <div class="val" id="suiteStatus">-</div>
        <div class="progress-wrap"><div class="progress-bar" id="progressBar"></div></div>
      </div>
      <div class="card">
        <div class="label">Passed / Failed</div>
        <div class="val"><span id="passCnt" style="color:var(--pass)">0</span> / <span id="failCnt" style="color:var(--fail)">0</span> <span class="label" id="doneCnt">(0/10)</span></div>
      </div>
      <div class="card">
        <div class="label">Current Test</div>
        <div class="val" id="curTest">-</div>
      </div>
      <div class="card">
        <div class="label">Disk Free (/)</div>
        <div class="val" id="diskInfo">-</div>
      </div>
    </div>

    <div class="hb-box" id="hbBox">
      <div class="label">Live Simulator Heartbeat (<span id="hbName"></span>)</div>
      <div class="hb-metrics" id="hbMetrics"></div>
    </div>

    <table>
      <thead>
        <tr>
          <th style="width:85px">Test ID</th>
          <th>Scenario</th>
          <th style="width:95px">Status</th>
          <th style="width:80px">Time</th>
          <th>Key Metrics</th>
          <th style="width:100px">Inspect</th>
        </tr>
      </thead>
      <tbody id="testRows"></tbody>
    </table>

    <div class="logs" id="logBox"></div>
  </div>

  <!-- TAB 2: Topology Builder & Fault Injection -->
  <div id="tab-topo" class="panel active">
    <div class="card" style="margin-bottom:14px">
      <h2>1. Auto-Calculate Fat-Tree Topology</h2>
      <div class="form-row">
        <div class="field">
          <label>xPUs (Nodes)</label>
          <input type="number" id="inNodes" value="8" min="8" max="8" readonly style="opacity:0.75;cursor:not-allowed" />
        </div>
        <div class="field">
          <label>Ports / xPU (Planes)</label>
          <input type="number" id="inXpusPerNode" value="8" min="8" max="8" readonly style="opacity:0.75;cursor:not-allowed" />
        </div>
        <div class="field">
          <label>Wiring Mode (Fixed)</label>
          <select id="inMode" disabled style="opacity:0.75;cursor:not-allowed">
            <option value="rail" selected>Rail-Optimized (1 xPU = 8×100G → 8 Planes, -planes 8)</option>
          </select>
        </div>
        <div class="field">
          <label>Tiers (Fixed)</label>
          <select id="inTiers" disabled style="opacity:0.75;cursor:not-allowed">
            <option value="2" selected>2-Tier Leaf-Spine (ToR-Spine)</option>
          </select>
        </div>
        <div class="field">
          <label>Traffic Pattern</label>
          <select id="inTraffic" onchange="drawTopo()">
            <option value="all_to_all" selected>All-to-All (모든 xPU 간 8-Plane 분산)</option>
            <option value="incast">Incast (All-to-Last xPU)</option>
          </select>
        </div>
        <div class="field">
          <label>Multipath Algo</label>
          <select id="inAlgo">
            <option value="reps" selected>REPS</option>
            <option value="freezing">REPS + Freezing</option>
            <option value="oblivious">Oblivious</option>
            <option value="bitmap">Bitmap</option>
            <option value="mixed">Mixed</option>
          </select>
        </div>
        <div class="field">
          <label>Fail At (us)</label>
          <input type="number" id="inFailAt" value="20" min="0" max="100000" />
        </div>
        <div class="field">
          <label>Recover At (us, 0=perm)</label>
          <input type="number" id="inRecoverAt" value="0" min="0" max="100000" />
        </div>
        <div class="field">
          <label>Max Test Time (us)</label>
          <input type="number" id="inEndUs" value="10000" min="100" max="100000" style="min-width:95px" />
        </div>
        <div class="field">
          <label>Timeline Frames</label>
          <select id="inFrames" style="min-width:85px">
            <option value="16" selected>16</option>
            <option value="32">32</option>
            <option value="64">64</option>
            <option value="128">128</option>
          </select>
        </div>
        <div class="field">
          <label>Link Speed</label>
          <select id="inLinkSpeed" onchange="onSpeedChange()">
            <option value="100000" selected>100G (100Gbps)</option>
            <option value="400000">400G (400Gbps)</option>
          </select>
        </div>
        <div class="field">
          <label>Queue Size (pkts, min 4)</label>
          <input type="number" id="inQueue" value="16" min="4" max="512" style="min-width:85px" onchange="if(parseInt(this.value||'4',10)<4)this.value=4" onblur="if(!this.value||parseInt(this.value,10)<4)this.value=4" />
        </div>
        <div class="field">
          <label>ECN Low (pkts)</label>
          <input type="number" id="inEcnLow" value="4" min="1" max="511" style="min-width:85px" />
        </div>
        <div class="field">
          <label>ECN High (pkts)</label>
          <input type="number" id="inEcnHigh" value="12" min="2" max="512" style="min-width:85px" />
        </div>
        <button class="btn-view" onclick="applyRecommendedEcn()" title="속도별 권장 Queue/ECN 기준값 자동 입력">권장 기준값 적용</button>
        <button class="btn-run" id="btnCustomRun" onclick="runCustomTopo()">Run Custom Topology Test</button>
        <button class="btn-view" onclick="clearFaults()">Clear Faults</button>
      </div>
      <div class="mono" id="topoSummary" style="color:#93c5fd"></div>
    </div>

    <div class="grid" style="grid-template-columns: 1fr 1fr; margin-bottom:14px">
      <div class="card">
        <div class="label">Selected Failed Nodes (Click switches on diagram to toggle)</div>
        <div class="chip-list" id="failNodeChips"><span class="label">None</span></div>
      </div>
      <div class="card">
        <div class="label">Selected Failed Links (Click links on diagram to toggle)</div>
        <div class="chip-list" id="failLinkChips"><span class="label">None</span></div>
      </div>
    </div>

    <div class="topo-wrap">
      <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px">
        <div class="label">Interactive Topology Diagram (Click any Plane or Link to fail/unfail; shows All-to-All 64-GPU traffic &amp; redistribution)</div>
        <div class="mono" style="display:flex; flex-wrap:wrap; gap:12px; font-size:0.78rem; color:#cbd5e1">
          <span><span style="color:#38bdf8">━━</span> 정상</span>
          <span><span style="color:#4ade80">━━</span> 재분배 증가(+Δ%)</span>
          <span><span style="color:#facc15">━━</span> ECN 혼잡</span>
          <span><span style="color:#e879f9">━━▶</span> Trim (스위치→xPU)</span>
          <span><span style="color:#fb923c">◀╌╌</span> NACK (xPU→스위치)</span>
          <span><span style="color:#2dd4bf">◀╌╌</span> ACK (역방향, 단일 Flow 선택 시)</span>
          <span><span style="color:#ef4444">╌╌</span> 장애(Fail)</span>
        </div>
      </div>
      <svg id="topoSvg" width="1220" height="460" viewBox="0 0 1220 460"></svg>
    </div>

    <div class="card" id="customResultCard" style="margin-top:14px; display:none">
      <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:10px; margin-bottom:10px">
        <h2 style="margin:0">실시간 변화 타임라인 &amp; 장애 전/후(Before vs After) 비교</h2>
        <div style="display:flex; gap:8px; align-items:center">
          <button class="btn-view" onclick="stepFrame(-1)" title="이전 타임라인 구간">◀ 이전</button>
          <button class="btn-run" id="btnPlay" onclick="togglePlay()">▶ Play</button>
          <button class="btn-view" onclick="stepFrame(1)" title="다음 타임라인 구간">다음 ▶</button>
          <button class="btn-view" id="btnLoop" onclick="toggleLoop()">🔁 Loop: OFF</button>
          <span class="mono" id="frameTimeLabel">0 us</span>
        </div>
      </div>
      <input type="range" id="timeSlider" min="0" max="0" value="0" oninput="onScrub(this.value)" style="width:100%; margin-bottom:10px" />
      <div class="mono" id="customMetrics" style="margin-bottom:12px"></div>
      <div style="display:flex; flex-wrap:wrap; align-items:center; gap:10px; margin-bottom:12px; padding:10px 12px; background:#0b1220; border:1px solid #334155; border-radius:8px">
        <span class="label" style="color:#93c5fd">🔍 단일 Flow 집중 트래킹:</span>
        <select id="flowFocusSelect" onchange="onSelectFocusFlow(this.value)" style="background:#0f172a; color:#f1f5f9; border:1px solid #475569; border-radius:6px; padding:5px 10px; font-size:0.84rem; min-width:280px">
          <option value="">전체 Flow 보기 (All Flows)</option>
        </select>
        <button class="btn-view" onclick="onSelectFocusFlow('')">전체로 돌아가기</button>
        <span class="mono" id="flowFocusHint" style="font-size:0.78rem; color:#94a3b8">※ 아래 표에서 Flow 행을 클릭해도 해당 Flow만 추적할 수 있습니다.</span>
      </div>

      <div class="card" id="flowTraceCard" style="background:#0c1a2e; border-color:#2563eb; margin-bottom:12px; display:none">
        <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px">
          <div class="label" id="flowTraceTitle" style="color:#93c5fd">선택 Flow 생애주기 (Trim → NACK → Slow Down → Reroute)</div>
          <div class="mono" id="flowTraceStats" style="font-size:0.8rem; color:#e2e8f0"></div>
        </div>
        <div style="overflow-x:auto; max-height:260px; overflow-y:auto">
          <table>
            <thead>
              <tr>
                <th>타임라인 구간 (클릭 시 이동)</th>
                <th>구간 전송량 (Slow Down 확인)</th>
                <th>Trim</th>
                <th>NACK</th>
                <th>사용 Plane</th>
                <th>EV Reroute (어디서 → 어디로)</th>
              </tr>
            </thead>
            <tbody id="flowFrameTbody"></tbody>
          </table>
        </div>
      </div>

      <div class="card" id="wiresharkCard" style="background:#08101e; border-color:#0ea5e9; margin-bottom:12px; display:none">
        <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px">
          <div class="label" id="wsTitle" style="color:#38bdf8">🦈 Wireshark 패킷 &amp; 헤더 분석기</div>
          <div class="mono" id="wsCountBadge" style="font-size:0.78rem; color:#94a3b8"></div>
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin-bottom:8px">
          <input type="text" id="wsFilter" placeholder="Display Filter (예: TRIM, NACK, ACK, PSN=8, P6, ECN)" oninput="renderWireshark()" style="flex:1; min-width:220px; background:#0f172a; color:#f1f5f9; border:1px solid #334155; border-radius:6px; padding:5px 10px; font-family:monospace; font-size:0.8rem" />
          <button class="btn-view" onclick="setWsQuickFilter('')">All</button>
          <button class="btn-view" onclick="setWsQuickFilter('DATA')">DATA</button>
          <button class="btn-view" onclick="setWsQuickFilter('TRIM')" style="color:#e879f9">TRIM</button>
          <button class="btn-view" onclick="setWsQuickFilter('NACK')" style="color:#fb923c">NACK</button>
          <button class="btn-view" onclick="setWsQuickFilter('ACK')" style="color:#2dd4bf">ACK</button>
          <button class="btn-view" onclick="setWsQuickFilter('ECN')" style="color:#facc15">ECN</button>
          <button class="btn-view" onclick="setWsQuickFilter('RTX')" style="color:#38bdf8">RTX/FAIL</button>
        </div>
        <div style="overflow-x:auto; max-height:240px; overflow-y:auto; border:1px solid #1e293b; border-radius:6px; margin-bottom:10px">
          <table style="font-size:0.78rem">
            <thead style="position:sticky; top:0; z-index:1">
              <tr>
                <th>No.</th>
                <th>Time (us)</th>
                <th>Frame</th>
                <th>Source</th>
                <th>Destination</th>
                <th>Protocol / Event</th>
                <th>Length</th>
                <th>PSN</th>
                <th>EV / Plane</th>
                <th>Info</th>
              </tr>
            </thead>
            <tbody id="wsPacketTbody"></tbody>
          </table>
        </div>
        <div class="grid" style="grid-template-columns: 1.25fr 1fr; gap:10px; margin-bottom:0">
          <div style="background:#0b1220; border:1px solid #1e293b; border-radius:6px; padding:10px; max-height:260px; overflow-y:auto">
            <div class="label" style="margin-bottom:6px; color:#93c5fd">Packet Details (L2 Rail / IP-ECN / UEC Transport Header)</div>
            <div id="wsHeaderTree" class="mono" style="font-size:0.77rem; line-height:1.45; color:#e2e8f0">패킷을 클릭하면 계층별 헤더가 표시됩니다.</div>
          </div>
          <div style="background:#0b1220; border:1px solid #1e293b; border-radius:6px; padding:10px; max-height:260px; overflow-y:auto">
            <div class="label" style="margin-bottom:6px; color:#93c5fd">Header Bytes (Hex / ASCII)</div>
            <pre id="wsHexDump" class="mono" style="margin:0; font-size:0.74rem; line-height:1.45; color:#cbd5e1; white-space:pre"></pre>
          </div>
        </div>
      </div>

      <div class="grid" id="stageFlowBox" style="grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); margin-bottom:12px"></div>

      <div class="card" style="background:#0b1220; margin-bottom:12px">
        <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px">
          <div class="label">1. 현재 타임라인 구간 PSN &amp; 트래픽 플로우 경로</div>
          <div class="mono" id="frameFlowSummary" style="color:#38bdf8; font-size:0.8rem"></div>
        </div>
        <div style="overflow-x:auto; max-height:240px; overflow-y:auto">
          <table>
            <thead>
              <tr>
                <th>Flow</th>
                <th>트래픽 경로 (Src → Dst)</th>
                <th>현재 PSN 범위</th>
                <th>패킷 (TX / RTX / ACK)</th>
                <th>흐름 EV &amp; Plane (어디로 흐르는가)</th>
              </tr>
            </thead>
            <tbody id="frameFlowTbody"></tbody>
          </table>
        </div>
      </div>

      <div class="card" style="background:#0b1220; margin-bottom:12px">
        <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px">
          <div class="label">2. 타임라인 이벤트 로그 (TRIM 발생 위치 · NACK 전달 경로 · 장애/ECN)</div>
          <div style="display:flex; gap:8px; align-items:center">
            <span class="mono" id="frameEcnBadge" style="font-size:0.78rem; color:#f59e0b"></span>
            <button class="btn-view" id="btnEventScope" onclick="toggleEventScope()">보기: 현재 구간</button>
          </div>
        </div>
        <div style="overflow-x:auto; max-height:260px; overflow-y:auto">
          <table>
            <thead>
              <tr>
                <th>시각 (us)</th>
                <th>이벤트</th>
                <th>발생 위치 / 전달 경로 (From → To)</th>
                <th>Flow / PSN</th>
                <th>EV / Plane</th>
                <th>상세 동작</th>
              </tr>
            </thead>
            <tbody id="frameEventsTbody"></tbody>
          </table>
        </div>
      </div>

      <div class="card" style="background:#0b1220; margin-bottom:12px">
        <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px">
          <div class="label">3. EV 재분배 (Reroute) 추적 — 어디에서 어디로 우회했는가</div>
          <div class="mono" id="rerouteSummaryBadge" style="font-size:0.78rem; color:#22c55e"></div>
        </div>
        <div style="overflow-x:auto; max-height:240px; overflow-y:auto">
          <table>
            <thead>
              <tr>
                <th>시각 (us)</th>
                <th>Flow (xPU)</th>
                <th>PSN</th>
                <th>기존 경로 (Old EV / Plane)</th>
                <th>변경 경로 (New EV / Plane)</th>
                <th>전환 사유</th>
              </tr>
            </thead>
            <tbody id="rerouteTbody"></tbody>
          </table>
        </div>
      </div>

      <div class="grid" style="grid-template-columns: 1fr 1fr">
        <div class="card" style="background:#0b1220">
          <div class="label" style="margin-bottom:8px">4-A. xPU별 EV 분산 비교 (Before Fail vs After Fail)</div>
          <div style="overflow-x:auto; max-height:220px; overflow-y:auto">
            <table>
              <thead>
                <tr>
                  <th>xPU (Src)</th>
                  <th>Before Fail 주요 EV</th>
                  <th>After Fail 주요 EV</th>
                </tr>
              </thead>
              <tbody id="evDistTbody"></tbody>
            </table>
          </div>
        </div>
        <div class="card" style="background:#0b1220">
          <div class="label" style="margin-bottom:8px">4-B. 스위치 링크별 Trim · ECN · Fail 집계</div>
          <div style="overflow-x:auto; max-height:220px; overflow-y:auto">
            <table>
              <thead>
                <tr>
                  <th>링크</th>
                  <th>Before Trim</th>
                  <th>After Trim</th>
                  <th>총 ECN</th>
                  <th>총 Fail</th>
                </tr>
              </thead>
              <tbody id="linkStatsTbody"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="modal" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal-body">
    <div class="modal-head">
      <strong id="modalTitle">Wire View</strong>
      <button class="btn-view" onclick="closeModal()">Close</button>
    </div>
    <pre class="modal-pre" id="modalPre"></pre>
  </div>
</div>

<script>
let failNodes = new Set();
let failLinks = new Set();
let lastLinkHeat = {};
let lastFrameData = null;
let topoModel = null;
let customFrames = [];
let customFrameIdx = 0;
let playTimer = null;
let playLoop = false;

function switchTab(name, btn) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
  if (name === 'topo') recalcTopo();
}

function fmtBytes(b) {
  if (b > 1048576) return (b / 1048576).toFixed(1) + ' MB';
  if (b > 1024) return (b / 1024).toFixed(1) + ' KB';
  return b + ' B';
}

async function runSuite() { await fetch('api/run', { method: 'POST' }); poll(); }
async function stopSuite() { await fetch('api/stop', { method: 'POST' }); poll(); }

async function openWireView(tc) {
  const res = await fetch('api/wire_view?tc=' + encodeURIComponent(tc));
  document.getElementById('modalTitle').textContent = tc + '_wire_view.md';
  document.getElementById('modalPre').textContent = await res.text();
  document.getElementById('modal').classList.add('open');
}
function closeModal() { document.getElementById('modal').classList.remove('open'); }

function calcFatTree(reqXpus, tiers) {
  let K = 2;
  if (tiers === 3) {
    while ((K * K * K) / 4 < reqXpus) K += 2;
    const ntor = (K * K) / 2, nagg = (K * K) / 2, ncore = (K * K) / 4;
    return {
      tiers: 3, K, nsrv: (K * K * K) / 4, npod: K,
      ntor, nagg, ncore, torPerPod: K / 2, aggPerPod: K / 2, hostsPerPod: (K * K) / 4
    };
  } else {
    while ((K * K) / 2 < reqXpus) K += 2;
    const ntor = K, nagg = K / 2;
    return {
      tiers: 2, K, nsrv: (K * K) / 2, npod: 1,
      ntor, nagg, ncore: 0, torPerPod: K, aggPerPod: K / 2, hostsPerPod: (K * K) / 2
    };
  }
}

function clearFaults() {
  failNodes.clear();
  failLinks.clear();
  lastLinkHeat = {};
  lastFrameData = null;
  renderFaultChips();
  drawTopo();
}

function toggleNode(name) {
  if (failNodes.has(name)) failNodes.delete(name); else failNodes.add(name);
  renderFaultChips();
  drawTopo();
}

function toggleLink(name) {
  if (failLinks.has(name)) failLinks.delete(name); else failLinks.add(name);
  renderFaultChips();
  drawTopo();
}

function renderFaultChips() {
  const fn = document.getElementById('failNodeChips');
  fn.innerHTML = failNodes.size ? [...failNodes].map(n => `<span class="chip" onclick="toggleNode('${n}')">${n} ✕</span>`).join('') : '<span class="label">None</span>';
  const fl = document.getElementById('failLinkChips');
  fl.innerHTML = failLinks.size ? [...failLinks].map(l => `<span class="chip" onclick="toggleLink('${l}')">${l} ✕</span>`).join('') : '<span class="label">None</span>';
}

function recalcTopo() {
  const nodes = Math.max(1, parseInt(document.getElementById('inNodes').value || '8', 10));
  const perNode = Math.max(1, Math.min(8, parseInt(document.getElementById('inXpusPerNode').value || '8', 10)));
  const mode = document.getElementById('inMode').value;
  const tiers = parseInt(document.getElementById('inTiers').value || '2', 10);

  if (mode === 'rail') {
    const perPlane = calcFatTree(nodes, tiers);
    const planes = perNode;
    const totalXpus = perPlane.nsrv * planes;
    const swPerPlane = perPlane.ntor + perPlane.nagg + perPlane.ncore;
    const totalSw = swPerPlane * planes;
    topoModel = {
      ...perPlane,
      mode: 'rail',
      planes,
      nodesPerPlane: perPlane.nsrv,
      totalXpus,
      totalSw,
    };
    document.getElementById('topoSummary').textContent =
      `Rail-Optimized: ${nodes} xPUs × ${perNode} Ports/xPU (${totalXpus} Total Ports)  →  ` +
      `Planes=${planes} (-nodes ${perPlane.nsrv} -planes ${planes} -tiers ${tiers}, K=${perPlane.K}), ` +
      `Total Switches=${totalSw} (${planes} × [ToR=${perPlane.ntor}, Agg/Spine=${perPlane.nagg}, Core=${perPlane.ncore}])`;
  } else {
    const reqXpus = nodes * perNode;
    const ft = calcFatTree(reqXpus, tiers);
    const totalSw = ft.ntor + ft.nagg + ft.ncore;
    topoModel = {
      ...ft,
      mode: 'shared',
      planes: 1,
      nodesPerPlane: ft.nsrv,
      totalXpus: ft.nsrv,
      totalSw,
    };
    document.getElementById('topoSummary').textContent =
      `Shared ToR: ${nodes} × ${perNode} = ${reqXpus} xPUs  →  Fat-Tree K=${ft.K}, Tiers=${tiers}, ` +
      `NSRV=${ft.nsrv} xPUs, NPOD=${ft.npod}, Switches=${totalSw} (ToR=${ft.ntor}, Agg=${ft.nagg}, Core=${ft.ncore})`;
  }
  drawTopo();
}

function drawTopo() {
  const svg = document.getElementById('topoSvg');
  if (!topoModel) return;
  const m = topoModel;
  const W = 1220, H = 430;
  let out = `<defs>
    <marker id="arrowTrim" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#e879f9" />
    </marker>
    <marker id="arrowNack" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#fb923c" />
    </marker>
    <marker id="arrowAck" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2dd4bf" />
    </marker>
    <marker id="arrowFwd" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
    </marker>
    <marker id="arrowReroute" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#4ade80" />
    </marker>
  </defs>`;

  const placeRow = (count, y) => {
    const pts = [];
    const pad = 55;
    const span = W - pad * 2;
    for (let i = 0; i < count; i++) {
      const x = count === 1 ? W / 2 : pad + (i * span) / (count - 1);
      pts.push({ x, y });
    }
    return pts;
  };

  if (m.mode === 'rail') {
    svg.setAttribute('width', '1220');
    svg.setAttribute('height', '460');
    svg.setAttribute('viewBox', '0 0 1220 460');
    const trafficMode = (document.getElementById('inTraffic') && document.getElementById('inTraffic').value) || 'all_to_all';
    const fr = lastFrameData;
    const isAfterFail = fr && fr.phase === 'AFTER FAIL';

    // Compute per-plane live load % (either from simulation frame or live preview based on selected faults)
    const activeFailedPlanes = new Set();
    for (let r = 0; r < m.planes; r++) {
      if ((failNodes.has(`P${r}`) || failNodes.has(`US${r}`)) && (!fr || isAfterFail)) activeFailedPlanes.add(r);
    }
    if (fr && fr.failed_planes) {
      fr.failed_planes.forEach(r => activeFailedPlanes.add(r));
    }

    // Single-Flow Focus state (when user selects 1 Flow to track)
    const isFocus = Boolean(selectedFlowId);
    const focusCat = isFocus ? (lastSimData && lastSimData.flow_catalog || []).find(c => String(c.flow_id) === String(selectedFlowId)) : null;
    const focusSrc = focusCat ? parseInt(focusCat.src, 10) : -1;
    const focusDst = focusCat ? parseInt(focusCat.dst, 10) : -1;
    const focusFlowFrame = (isFocus && fr && fr.flow_stats) ? fr.flow_stats.find(f => String(f.flow_id) === String(selectedFlowId)) : null;
    const focusPlanes = new Set();
    if (focusFlowFrame && focusFlowFrame.planes) {
      Object.keys(focusFlowFrame.planes).forEach(k => {
        const idx = parseInt(String(k).replace('P', ''), 10);
        if (!isNaN(idx)) focusPlanes.add(idx);
      });
    }
    const focusReroutes = (isFocus && fr && fr.reroutes) ? fr.reroutes.filter(r => String(r.flow_id) === String(selectedFlowId)) : [];
    const focusNewPlanes = new Set(focusReroutes.map(r => parseInt(String(r.new_plane).replace('P', ''), 10)));
    const focusTrims = (isFocus && fr && fr.trim_flows) ? fr.trim_flows.filter(x => String(x.flow_id) === String(selectedFlowId)) : [];
    const focusNacks = (isFocus && fr && fr.nack_flows) ? fr.nack_flows.filter(x => String(x.flow_id) === String(selectedFlowId)) : [];
    const focusAcks = (isFocus && fr && fr.ack_flows) ? fr.ack_flows.filter(x => String(x.flow_id) === String(selectedFlowId)) : [];
    const focusTrimPlanes = new Set(focusTrims.map(x => parseInt(x.plane, 10)));
    const focusNackPlanes = new Set(focusNacks.map(x => parseInt(x.plane, 10)));
    const focusAckPlanes = new Set(focusAcks.map(x => parseInt(x.plane, 10)));

    let planePct = [];
    if (isFocus) {
      const counts = new Array(m.planes).fill(0);
      let tot = 0;
      if (focusFlowFrame && focusFlowFrame.planes) {
        Object.entries(focusFlowFrame.planes).forEach(([k, v]) => {
          const idx = parseInt(String(k).replace('P', ''), 10);
          if (!isNaN(idx) && idx < m.planes) { counts[idx] += v; tot += v; }
        });
      }
      planePct = counts.map(c => tot > 0 ? (c * 100.0) / tot : 0);
    } else if (fr && fr.plane_pct && fr.plane_pct.length === m.planes) {
      planePct = fr.plane_pct;
    } else {
      const healthyCount = Math.max(1, m.planes - activeFailedPlanes.size);
      for (let r = 0; r < m.planes; r++) {
        planePct.push(activeFailedPlanes.has(r) ? 0 : (100 / healthyCount));
      }
    }
    const basePct = 100 / m.planes;

    const railPts = placeRow(m.planes, 95);
    const srvCount = Math.min(m.nodesPerPlane, 16);
    const srvPts = placeRow(srvCount, 305);

    const drawNode = (pt, label, planeIdx, fill, r = 18) => {
      const isFail = failNodes.has(label) || failNodes.has(`US${planeIdx}`) || activeFailedPlanes.has(planeIdx);
      const f = isFail ? '#dc2626' : fill;
      const stroke = isFail ? '#fecaca' : '#94a3b8';
      out += `<g style="cursor:pointer" onclick="toggleNode('${label}')">
        <circle cx="${pt.x}" cy="${pt.y}" r="${r}" fill="${f}" stroke="${stroke}" stroke-width="${isFail ? 2.5 : 1.4}" />
        <text x="${pt.x}" y="${pt.y + 4}" fill="#f8fafc" text-anchor="middle" font-size="10.5" font-weight="bold" font-family="monospace">${label}</text>
      </g>`;
    };

    const drawLink = (p1, p2, label, planeIdx, nodeIdx) => {
      const tor = Math.floor(nodeIdx / 2), sp = planeIdx % 2;
      const pPrefix = `P${planeIdx}:`;
      const simKey = `LS${tor}->US${sp}`;
      const revKey1 = `US${sp}->LS_${tor}`;
      const revKey2 = `US${sp}->LS${tor}`;
      const dstKey = `LS${tor}->DST${nodeIdx}`;
      const isFail = failLinks.has(label) || activeFailedPlanes.has(planeIdx);
      const h0 = lastLinkHeat[label] || {};
      const h1 = lastLinkHeat[pPrefix + simKey] || {};
      const h2 = lastLinkHeat[pPrefix + revKey1] || {};
      const h3 = lastLinkHeat[pPrefix + revKey2] || {};
      const h4 = lastLinkHeat[pPrefix + dstKey] || {};
      const heat = {
        ecn: (h0.ecn||0) + (h1.ecn||0) + (h2.ecn||0) + (h3.ecn||0) + (h4.ecn||0),
        trim: (h0.trim||0) + (h1.trim||0) + (h2.trim||0) + (h3.trim||0) + (h4.trim||0),
        fail: isFail ? ((h0.fail||0) + (h1.fail||0) + (h2.fail||0) + (h3.fail||0) + (h4.fail||0)) : 0,
      };
      const pct = planePct[planeIdx] || 0;
      const hasAnyFault = activeFailedPlanes.size > 0 || failLinks.size > 0;
      const hasRedistribution = hasAnyFault || (fr && (fr.reroute_cnt || 0) > 0);
      const boosted = hasRedistribution && !isFail && pct > basePct + 0.5;

      let stroke = '#38bdf8', width = 1.6, dash = '6,4', cls = 'flow-anim', op = 0.72;
      if (isFocus) {
        const isFlowNode = (nodeIdx === focusSrc || nodeIdx === focusDst);
        const isFlowPlane = focusPlanes.has(planeIdx) || focusTrimPlanes.has(planeIdx) || focusNackPlanes.has(planeIdx) || focusAckPlanes.has(planeIdx) || focusNewPlanes.has(planeIdx);
        if (!isFlowNode || !isFlowPlane) {
          stroke = '#334155'; width = 0.8; dash = ''; cls = ''; op = 0.08;
        } else if (isFail) {
          stroke = '#ef4444'; width = 3.0; dash = '5,4'; cls = ''; op = 0.95;
        } else if (focusTrimPlanes.has(planeIdx)) {
          stroke = '#e879f9'; width = 3.4; dash = '7,3'; cls = 'flow-anim'; op = 0.98;
        } else if (focusNewPlanes.has(planeIdx)) {
          stroke = '#4ade80'; width = 3.4; dash = '8,4'; cls = 'flow-anim'; op = 0.98;
        } else {
          stroke = '#38bdf8'; width = 2.6; dash = '6,4'; cls = 'flow-anim'; op = 0.95;
        }
      } else if (isFail) {
        stroke = '#ef4444'; width = 2.8; dash = '5,4'; cls = ''; op = 0.95;
      } else if ((heat.fail || 0) > 0) {
        stroke = '#ef4444'; width = 2.8; dash = '5,4'; cls = ''; op = 0.95;
      } else if ((heat.trim || 0) > 0) {
        stroke = '#e879f9'; width = 3.4; dash = '7,3'; cls = 'flow-anim'; op = 0.98;
      } else if ((heat.ecn || 0) > 0) {
        stroke = '#facc15'; width = 2.6; dash = '6,4'; cls = 'flow-anim'; op = 0.92;
      } else if (boosted) {
        stroke = '#4ade80'; width = Math.min(3.8, 1.9 + (pct - basePct) * 0.25); dash = '8,4'; cls = 'flow-anim'; op = 0.95;
      } else if (fr && pct <= 0) {
        stroke = '#475569'; width = 1.2; dash = ''; cls = ''; op = 0.35;
      } else {
        width = 1.6;
      }
      out += `<line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" class="${cls}" stroke="${stroke}" stroke-width="${width}" stroke-opacity="${op}" stroke-dasharray="${dash}" style="cursor:pointer" onclick="toggleLink('${label}')"><title>${label} (Plane ${planeIdx} load=${pct.toFixed(1)}%, ECN=${heat.ecn||0}, TRIM=${heat.trim||0}, FAIL=${heat.fail||0})</title></line>`;
      if (isFocus && (nodeIdx === focusSrc || nodeIdx === focusDst) && (focusPlanes.has(planeIdx) || focusNewPlanes.has(planeIdx)) && !isFail) {
        const sx = nodeIdx === focusSrc ? p1.x : p2.x, sy = nodeIdx === focusSrc ? p1.y : p2.y;
        const ex = nodeIdx === focusSrc ? p2.x : p1.x, ey = nodeIdx === focusSrc ? p2.y : p1.y;
        const t = nodeIdx === focusSrc ? 0.35 : 0.65;
        const ax = sx + (ex - sx) * t, ay = sy + (ey - sy) * t;
        const mk = focusNewPlanes.has(planeIdx) ? 'arrowReroute' : 'arrowFwd';
        out += `<path d="M ${sx} ${sy} L ${ax} ${ay}" fill="none" stroke="${stroke}" stroke-width="${width}" marker-end="url(#${mk})" opacity="0.95" />`;
      }
    };

    // Draw All-to-All inter-node mesh arcs at bottom (or ONLY the selected Flow arc when in Focus mode)
    if (isFocus && focusSrc >= 0 && focusDst >= 0 && focusSrc < srvCount && focusDst < srvCount) {
      const x1 = srvPts[focusSrc].x, x2 = srvPts[focusDst].x, y0 = 352;
      const depth = 28 + Math.abs(focusDst - focusSrc) * 7;
      const labelY = Math.min(426, y0 + depth * 0.55 + 14);
      out += `<path d="M ${x1} ${y0} Q ${(x1 + x2) / 2} ${y0 + depth} ${x2} ${y0}" fill="none" stroke="#38bdf8" stroke-opacity="0.9" stroke-width="2.6" stroke-dasharray="6,4" class="flow-anim" marker-end="url(#arrowFwd)" />`;
      out += `<text x="${(x1 + x2) / 2}" y="${labelY}" fill="#93c5fd" text-anchor="middle" font-size="10.5" font-weight="bold" font-family="monospace">Flow ${selectedFlowId}: 출발 xPU ${focusSrc} → 목적지 xPU ${focusDst}</text>`;
    } else if (trafficMode === 'all_to_all') {
      for (let a = 0; a < srvCount; a++) {
        for (let b = a + 1; b < srvCount; b++) {
          const x1 = srvPts[a].x, x2 = srvPts[b].x, y0 = 352;
          const depth = 18 + (b - a) * 9;
          out += `<path d="M ${x1} ${y0} Q ${(x1 + x2) / 2} ${y0 + depth} ${x2} ${y0}" fill="none" stroke="#38bdf8" stroke-opacity="0.24" stroke-width="1.3" stroke-dasharray="5,4" class="flow-anim" />`;
        }
      }
    } else {
      const dstPt = srvPts[srvCount - 1];
      for (let a = 0; a < srvCount - 1; a++) {
        const x1 = srvPts[a].x, x2 = dstPt.x, y0 = 352;
        const depth = 20 + (srvCount - 1 - a) * 8;
        out += `<path d="M ${x1} ${y0} Q ${(x1 + x2) / 2} ${y0 + depth} ${x2} ${y0}" fill="none" stroke="#f59e0b" stroke-opacity="0.35" stroke-width="1.5" stroke-dasharray="5,4" class="flow-anim" />`;
      }
    }

    // Draw 64 xPU-Port-to-Plane links (dim non-selected xPUs when in Focus mode)
    const linkSpdG = Math.round(parseInt(document.getElementById('inLinkSpeed')?.value || '100000', 10) / 1000);
    const xpuAggG = linkSpdG * m.planes;
    const xpuAggLabel = xpuAggG >= 1000 ? `${(xpuAggG/1000).toFixed(1)}T` : `${xpuAggG}G`;
    for (let s = 0; s < srvCount; s++) {
      const boxW = Math.max(96, m.planes * 12 + 12);
      const x0 = srvPts[s].x - boxW / 2;
      const isSrcOrDst = !isFocus || s === focusSrc || s === focusDst;
      const boxStroke = (isFocus && s === focusSrc) ? '#38bdf8' : ((isFocus && s === focusDst) ? '#22c55e' : '#475569');
      const boxSw = (isFocus && isSrcOrDst) ? 2.4 : 1.3;
      const boxOp = isSrcOrDst ? 1.0 : 0.22;
      const roleTag = (isFocus && s === focusSrc) ? ' [출발 SRC]' : ((isFocus && s === focusDst) ? ' [목적 DST]' : '');
      out += `<rect x="${x0}" y="275" width="${boxW}" height="74" rx="8" fill="#1e293b" stroke="${boxStroke}" stroke-width="${boxSw}" opacity="${boxOp}"/>`;
      if (isFocus && (s === focusSrc || s === focusDst)) {
        const pillBg = s === focusSrc ? '#1d4ed8' : '#15803d';
        const pillTxt = s === focusSrc ? '출발 (SRC)' : '목적지 (DST)';
        out += `<rect x="${srvPts[s].x - 36}" y="261" width="72" height="15" rx="4" fill="${pillBg}" /><text x="${srvPts[s].x}" y="272" fill="#fff" text-anchor="middle" font-size="8.5" font-weight="bold" font-family="monospace">${pillTxt}</text>`;
      }
      out += `<text x="${srvPts[s].x}" y="341" fill="#e2e8f0" opacity="${boxOp}" text-anchor="middle" font-size="10.5" font-weight="bold" font-family="monospace">xPU ${s}${roleTag || ' (' + xpuAggLabel + ')'}</text>`;
      for (let r = 0; r < m.planes; r++) {
        const xpuX = x0 + 11 + r * ((boxW - 22) / Math.max(1, m.planes - 1));
        const xpuPt = { x: m.planes === 1 ? srvPts[s].x : xpuX, y: 296 };
        const linkLabel = `N${s}-P${r}`;
        drawLink(xpuPt, railPts[r], linkLabel, r, s);
        const linkDown = failLinks.has(linkLabel) || activeFailedPlanes.has(r);
        out += `<circle cx="${xpuPt.x}" cy="${xpuPt.y}" r="4.5" fill="${linkDown ? '#ef4444' : '#38bdf8'}" opacity="${boxOp}" />`;
        out += `<text x="${xpuPt.x}" y="314" fill="#94a3b8" opacity="${boxOp}" text-anchor="middle" font-size="7.5" font-family="monospace">P${r}</text>`;
      }
    }

    const getPortPt = (s, r) => {
      const boxW = Math.max(96, m.planes * 12 + 12);
      const x0 = srvPts[s].x - boxW / 2;
      const xpuX = m.planes === 1 ? srvPts[s].x : (x0 + 11 + r * ((boxW - 22) / Math.max(1, m.planes - 1)));
      return { x: xpuX, y: 296 };
    };

    // Draw Trim (Switch Plane -> Dst xPU) & NACK (Dst xPU -> Switch Plane -> Src xPU) with non-overlapping badges
    const placedBadges = [];
    const placeBadge = (bx, by, w, h) => {
      let y = by;
      for (let attempt = 0; attempt < 5; attempt++) {
        const clash = placedBadges.some(b => Math.abs(b.x - bx) < (b.w + w) * 0.5 && Math.abs(b.y - y) < (b.h + h) * 0.5 + 2);
        if (!clash) break;
        y += (attempt % 2 === 0 ? 16 : -16);
      }
      placedBadges.push({ x: bx, y, w, h });
      return y;
    };

    if (fr && fr.trim_flows && fr.trim_flows.length) {
      const tList = selectedFlowId ? fr.trim_flows.filter(x => String(x.flow_id) === String(selectedFlowId)) : fr.trim_flows;
      tList.forEach((tf, idx) => {
        const s = parseInt(tf.src, 10), d = parseInt(tf.dst, 10), r = parseInt(tf.plane, 10);
        if (isNaN(d) || isNaN(r) || d >= srvCount || r >= m.planes) return;
        const pPlane = railPts[r], pDst = getPortPt(d, r);
        const mid = { x: pPlane.x + (pDst.x - pPlane.x) * 0.30, y: pPlane.y + (pDst.y - pPlane.y) * 0.30 };
        const tip = `TRIM (Flow ${tf.flow_id}): 출발지 xPU ${s} → 스위치 Plane ${r}에서 Trim 발생 → 목적지 xPU ${d}로 진입 (${tf.cnt}건)`;
        if (!isNaN(s) && s >= 0 && s < srvCount) {
          const pSrc = getPortPt(s, r);
          const midIn = { x: pSrc.x + (pPlane.x - pSrc.x) * 0.42, y: pSrc.y + (pPlane.y - pSrc.y) * 0.42 };
          out += `<path d="M ${pSrc.x} ${pSrc.y} L ${midIn.x} ${midIn.y}" fill="none" stroke="#e879f9" stroke-width="2.8" stroke-dasharray="6,3" class="flow-anim" marker-end="url(#arrowTrim)" opacity="0.92"><title>${tip}</title></path>`;
          out += `<line x1="${midIn.x}" y1="${midIn.y}" x2="${pPlane.x}" y2="${pPlane.y}" stroke="#e879f9" stroke-width="2.8" stroke-dasharray="6,3" class="flow-anim" opacity="0.92"><title>${tip}</title></line>`;
        }
        out += `<path d="M ${pPlane.x} ${pPlane.y} L ${mid.x} ${mid.y}" fill="none" stroke="#e879f9" stroke-width="3.0" marker-end="url(#arrowTrim)" opacity="0.95"><title>${tip}</title></path>`;
        out += `<path d="M ${mid.x} ${mid.y} L ${pDst.x} ${pDst.y - 6}" fill="none" stroke="#e879f9" stroke-width="3.0" marker-end="url(#arrowTrim)" opacity="0.95"><title>${tip}</title></path>`;
        if (idx < 3 || selectedFlowId) {
          const lbl = (!isNaN(s) && s >= 0) ? `TRIM x${s}→P${r}→x${d}` : `TRIM P${r}→x${d}`;
          const by = placeBadge(mid.x, mid.y - 9, 96, 14);
          out += `<rect x="${mid.x - 48}" y="${by - 7}" width="96" height="14" rx="4" fill="#3b0764" stroke="#e879f9" stroke-width="0.9"/><text x="${mid.x}" y="${by + 3}" fill="#f5d0fe" text-anchor="middle" font-size="8.2" font-weight="bold" font-family="monospace">${lbl}</text>`;
        }
      });
    }
    if (fr && fr.nack_flows && fr.nack_flows.length) {
      const nList = selectedFlowId ? fr.nack_flows.filter(x => String(x.flow_id) === String(selectedFlowId)) : fr.nack_flows;
      nList.forEach((nf, idx) => {
        const s = parseInt(nf.src, 10), d = parseInt(nf.dst, 10), r = parseInt(nf.plane, 10);
        if (isNaN(s) || isNaN(r) || s >= srvCount || r >= m.planes) return;
        const pFrom = getPortPt(s, r), pPlane = railPts[r];
        const off = 5;
        const midUp = { x: pFrom.x + (pPlane.x - pFrom.x) * 0.32 + off, y: pFrom.y + (pPlane.y - pFrom.y) * 0.32 };
        const tip = `NACK 역방향 (Flow ${nf.flow_id}): 목적지 xPU ${s} → Plane ${r} → 출발지 xPU ${nf.dst} (${nf.cnt}건)`;
        out += `<path d="M ${pFrom.x + off} ${pFrom.y} L ${midUp.x} ${midUp.y}" fill="none" stroke="#fb923c" stroke-width="2.8" stroke-dasharray="5,3" class="flow-anim" marker-end="url(#arrowNack)" opacity="0.98"><title>${tip}</title></path>`;
        out += `<line x1="${midUp.x}" y1="${midUp.y}" x2="${pPlane.x + off}" y2="${pPlane.y}" stroke="#fb923c" stroke-width="2.8" stroke-dasharray="5,3" class="flow-anim" opacity="0.98"><title>${tip}</title></line>`;
        if (!isNaN(d) && d < srvCount) {
          const pOrigSrc = getPortPt(d, r);
          const midDn = { x: pPlane.x + (pOrigSrc.x - pPlane.x) * 0.65 + off, y: pPlane.y + (pOrigSrc.y - pPlane.y) * 0.65 };
          out += `<path d="M ${pPlane.x + off} ${pPlane.y} L ${midDn.x} ${midDn.y}" fill="none" stroke="#fb923c" stroke-width="2.8" stroke-dasharray="5,3" class="flow-anim" marker-end="url(#arrowNack)" opacity="0.98"><title>${tip}</title></path>`;
          out += `<path d="M ${midDn.x} ${midDn.y} L ${pOrigSrc.x + off} ${pOrigSrc.y - 6}" fill="none" stroke="#fb923c" stroke-width="2.8" stroke-dasharray="5,3" class="flow-anim" marker-end="url(#arrowNack)" opacity="0.98"><title>${tip}</title></path>`;
        }
        if (idx < 3 || selectedFlowId) {
          const by = placeBadge(midUp.x, midUp.y + 10, 76, 14);
          out += `<rect x="${midUp.x - 38}" y="${by - 7}" width="76" height="14" rx="4" fill="#431407" stroke="#fb923c" stroke-width="0.9"/><text x="${midUp.x}" y="${by + 3}" fill="#fed7aa" text-anchor="middle" font-size="8.5" font-weight="bold" font-family="monospace">NACK x${s}→x${nf.dst}</text>`;
        }
      });
    }
    if (isFocus && focusAcks.length) {
      focusAcks.forEach((af) => {
        const s = parseInt(af.src, 10), d = parseInt(af.dst, 10), r = parseInt(af.plane, 10);
        if (isNaN(s) || isNaN(r) || s >= srvCount || r >= m.planes) return;
        const pFrom = getPortPt(s, r), pPlane = railPts[r];
        const off = -5;
        const midUp = { x: pFrom.x + (pPlane.x - pFrom.x) * 0.32 + off, y: pFrom.y + (pPlane.y - pFrom.y) * 0.32 };
        const tip = `ACK 역방향 (Flow ${af.flow_id}): 목적지 xPU ${s} → Plane ${r} → 출발지 xPU ${af.dst} (${af.cnt}건)`;
        out += `<path d="M ${pFrom.x + off} ${pFrom.y} L ${midUp.x} ${midUp.y}" fill="none" stroke="#2dd4bf" stroke-width="2.2" stroke-dasharray="4,3" class="flow-anim" marker-end="url(#arrowAck)" opacity="0.92"><title>${tip}</title></path>`;
        out += `<line x1="${midUp.x}" y1="${midUp.y}" x2="${pPlane.x + off}" y2="${pPlane.y}" stroke="#2dd4bf" stroke-width="2.2" stroke-dasharray="4,3" class="flow-anim" opacity="0.92"><title>${tip}</title></line>`;
        if (!isNaN(d) && d < srvCount) {
          const pOrigSrc = getPortPt(d, r);
          const midDn = { x: pPlane.x + (pOrigSrc.x - pPlane.x) * 0.65 + off, y: pPlane.y + (pOrigSrc.y - pPlane.y) * 0.65 };
          out += `<path d="M ${pPlane.x + off} ${pPlane.y} L ${midDn.x} ${midDn.y}" fill="none" stroke="#2dd4bf" stroke-width="2.2" stroke-dasharray="4,3" class="flow-anim" marker-end="url(#arrowAck)" opacity="0.92"><title>${tip}</title></path>`;
          out += `<path d="M ${midDn.x} ${midDn.y} L ${pOrigSrc.x + off} ${pOrigSrc.y - 6}" fill="none" stroke="#2dd4bf" stroke-width="2.2" stroke-dasharray="4,3" class="flow-anim" marker-end="url(#arrowAck)" opacity="0.92"><title>${tip}</title></path>`;
        }
        const by = placeBadge(midUp.x, midUp.y + 10, 96, 14);
        out += `<rect x="${midUp.x - 48}" y="${by - 7}" width="96" height="14" rx="4" fill="#042f2e" stroke="#2dd4bf" stroke-width="0.9"/><text x="${midUp.x}" y="${by + 3}" fill="#99f6e4" text-anchor="middle" font-size="8.2" font-weight="bold" font-family="monospace">ACK x${s}→P${r}→x${af.dst}(${af.cnt})</text>`;
      });
    }

    // Draw 8 Planes with live Traffic Share % bars
    const hasAnyFault = activeFailedPlanes.size > 0 || failLinks.size > 0;
    railPts.forEach((p, r) => {
      const pct = planePct[r] || 0;
      const isFail = activeFailedPlanes.has(r) || failNodes.has(`P${r}`) || failNodes.has(`US${r}`);
      const delta = pct - basePct;
      const barW = 76;
      const fillW = Math.max(0, Math.min(barW, (pct / 35) * barW));
      const barColor = isFail ? '#ef4444' : (hasAnyFault && delta > 0.5 ? '#22d3ee' : '#22c55e');
      out += `<rect x="${p.x - barW/2}" y="${p.y - 54}" width="${barW}" height="10" rx="4" fill="#0f172a" stroke="#334155" />`;
      out += `<rect x="${p.x - barW/2}" y="${p.y - 54}" width="${fillW}" height="10" rx="4" fill="${barColor}" />`;
      const pctLabel = isFail ? 'FAIL 0%' : (hasAnyFault && delta > 0.5 ? `${pct.toFixed(1)}% (+${delta.toFixed(1)}%)` : `${pct.toFixed(1)}%`);
      out += `<text x="${p.x}" y="${p.y - 60}" fill="${isFail ? '#fca5a5' : '#cbd5e1'}" text-anchor="middle" font-size="10" font-weight="bold" font-family="monospace">${pctLabel}</text>`;
      drawNode(p, `P${r}`, r, '#0f766e', 20);
      out += `<text x="${p.x}" y="${p.y - 28}" fill="#94a3b8" text-anchor="middle" font-size="10" font-family="monospace">Plane ${r}</text>`;
    });

    const healthyCnt = m.planes - activeFailedPlanes.size;
    const focusAckCnt = focusAcks.reduce((acc, x) => acc + (x.cnt || 0), 0);
    const statusBanner = isFocus
      ? `🔍 Flow ${selectedFlowId} 집중 트래킹 (xPU ${focusSrc} → xPU ${focusDst}) | 현재 구간: TX=${focusFlowFrame ? focusFlowFrame.tx_cnt : 0}, RTX=${focusFlowFrame ? focusFlowFrame.rtx_cnt : 0}, ACK=${focusAckCnt}, Trim=${focusTrims.length}, NACK=${focusNacks.length}, Reroute=${focusReroutes.length}건`
      : (activeFailedPlanes.size > 0
        ? `⚠️ ${activeFailedPlanes.size} Plane(s) Failed → Traffic redistributed across ${healthyCnt}/${m.planes} healthy Planes (~${(100/Math.max(1,healthyCnt)).toFixed(1)}% each)`
        : (failLinks.size > 0
          ? `⚠️ ${failLinks.size} Link(s) Failed → Traffic rerouted to healthy links/EVs`
          : `✅ All ${m.planes}/${m.planes} Planes Healthy | ${trafficMode === 'all_to_all' ? 'All-to-All (8 xPUs × 8 Ports = 64 Links)' : 'Incast'} (~${basePct.toFixed(1)}% per Plane)`));
    out += `<text x="610" y="446" fill="#cbd5e1" text-anchor="middle" font-size="11.5" font-family="monospace">${statusBanner}</text>`;
    svg.innerHTML = out;
    return;
  }

  if (m.nsrv > 512) {
    svg.setAttribute('width', '1220');
    svg.setAttribute('viewBox', '0 0 1220 430');
    svg.innerHTML = `<text x="610" y="210" fill="#94a3b8" text-anchor="middle" font-size="14">Topology too large for SVG (${m.nsrv} xPUs &gt; 512). Parameters are still valid for simulation.</text>`;
    return;
  }

  const compactHosts = m.nsrv > 32;
  const maxCols = Math.max(m.ntor, m.nagg, m.ncore, compactHosts ? m.ntor : m.nsrv);
  const dynW = Math.max(1220, maxCols * 46 + 120);
  svg.setAttribute('width', String(dynW));
  svg.setAttribute('viewBox', `0 0 ${dynW} ${H}`);

  const placeRowDyn = (count, y) => {
    const pts = [];
    const pad = 55;
    const span = dynW - pad * 2;
    for (let i = 0; i < count; i++) {
      const x = count === 1 ? dynW / 2 : pad + (i * span) / (count - 1);
      pts.push({ x, y });
    }
    return pts;
  };

  const corePts = m.ncore > 0 ? placeRowDyn(m.ncore, 45) : [];
  const aggPts = placeRowDyn(m.nagg, m.ncore > 0 ? 150 : 75);
  const torPts = placeRowDyn(m.ntor, m.ncore > 0 ? 260 : 210);
  const srvPts = compactHosts ? torPts.map(p => ({ x: p.x, y: 365 })) : placeRowDyn(m.nsrv, 375);

  const drawLink = (p1, p2, label) => {
    const isFail = failLinks.has(label);
    const heat = lastLinkHeat[label] || {};
    let stroke = '#334155', width = 1.6, dash = '';
    if (isFail) { stroke = '#ef4444'; width = 3.2; dash = '5,4'; }
    else if ((heat.fail || 0) > 0) { stroke = '#ef4444'; width = 3; }
    else if ((heat.trim || 0) > 0) { stroke = '#f97316'; width = 2.8; }
    else if ((heat.ecn || 0) > 0) { stroke = '#eab308'; width = 2.4; }
    out += `<line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" stroke="${stroke}" stroke-width="${width}" stroke-dasharray="${dash}" style="cursor:pointer" onclick="toggleLink('${label}')"><title>${label} (ECN=${heat.ecn||0}, TRIM=${heat.trim||0}, FAIL=${heat.fail||0})</title></line>`;
  };

  // Links: Core <-> Agg
  if (m.ncore > 0) {
    for (let pod = 0; pod < m.npod; pod++) {
      for (let a = 0; a < m.aggPerPod; a++) {
        const aggIdx = pod * m.aggPerPod + a;
        for (let c = 0; c < m.K / 2; c++) {
          const coreIdx = a * (m.K / 2) + c;
          if (coreIdx < m.ncore) drawLink(aggPts[aggIdx], corePts[coreIdx], `US${aggIdx}->CS${coreIdx}`);
        }
      }
    }
  }

  // Links: Agg <-> ToR
  for (let pod = 0; pod < m.npod; pod++) {
    for (let t = 0; t < m.torPerPod; t++) {
      const torIdx = pod * m.torPerPod + t;
      for (let a = 0; a < m.aggPerPod; a++) {
        const aggIdx = pod * m.aggPerPod + a;
        drawLink(torPts[torIdx], aggPts[aggIdx], `LS${torIdx}->US${aggIdx}`);
      }
    }
  }

  // Links: ToR <-> xPU
  const hostsPerTor = m.nsrv / m.ntor;
  if (compactHosts) {
    for (let t = 0; t < m.ntor; t++) {
      drawLink(srvPts[t], torPts[t], `SRV->LS${t}`);
    }
  } else {
    for (let s = 0; s < m.nsrv; s++) {
      const torIdx = Math.floor(s / hostsPerTor);
      drawLink(srvPts[s], torPts[torIdx], `SRV${s}->LS${torIdx}`);
    }
  }

  const drawNode = (pt, label, fill, r = 16, clickable = true) => {
    const isFail = failNodes.has(label);
    const f = isFail ? '#dc2626' : fill;
    const stroke = isFail ? '#fecaca' : '#94a3b8';
    out += `<g ${clickable ? `style="cursor:pointer" onclick="toggleNode('${label}')"` : ''}>
      <circle cx="${pt.x}" cy="${pt.y}" r="${r}" fill="${f}" stroke="${stroke}" stroke-width="${isFail ? 2.5 : 1.2}" />
      <text x="${pt.x}" y="${pt.y + 4}" fill="#f8fafc" text-anchor="middle" font-size="10" font-family="monospace">${label}</text>
    </g>`;
  };

  corePts.forEach((p, i) => drawNode(p, `CS${i}`, '#1d4ed8', 16));
  aggPts.forEach((p, i) => drawNode(p, `US${i}`, '#0f766e', 15));
  torPts.forEach((p, i) => drawNode(p, `LS${i}`, '#4338ca', 15));
  if (compactHosts) {
    srvPts.forEach((p, t) => {
      const s0 = t * hostsPerTor;
      const s1 = s0 + hostsPerTor - 1;
      out += `<rect x="${p.x - 20}" y="${p.y - 12}" width="40" height="24" rx="5" fill="#334155" stroke="#64748b" />
        <text x="${p.x}" y="${p.y + 4}" fill="#f8fafc" text-anchor="middle" font-size="9" font-family="monospace">x${s0}..${s1}</text>`;
    });
  } else {
    srvPts.forEach((p, i) => drawNode(p, `x${i}`, '#334155', 10, false));
  }

  svg.innerHTML = out;
}

let eventScopeCum = false;
let lastSimData = null;
let selectedFlowId = '';

function onSelectFocusFlow(fid) {
  selectedFlowId = fid ? String(fid) : '';
  selectedWsPktNo = null;
  const sel = document.getElementById('flowFocusSelect');
  if (sel) sel.value = selectedFlowId;
  renderSingleFlowTrace();
  renderWireshark();
  drawTopo();
  if (lastFrameData) renderTimelineTables(lastFrameData);
}

let selectedWsPktNo = null;
function setWsQuickFilter(q) {
  const inp = document.getElementById('wsFilter');
  if (inp) inp.value = q;
  renderWireshark();
}

function wsRowColors(ev) {
  if (ev === 'SW_TRIM' || ev === 'RX_TRIM') return { bg: 'rgba(168,85,247,0.18)', fg: '#e879f9' };
  if (ev === 'TX_NACK' || ev === 'RX_NACK') return { bg: 'rgba(249,115,22,0.18)', fg: '#fb923c' };
  if (ev === 'RX_ACK') return { bg: 'rgba(20,184,166,0.14)', fg: '#2dd4bf' };
  if (ev === 'TX_RTX') return { bg: 'rgba(14,165,233,0.18)', fg: '#38bdf8' };
  if (ev === 'SW_ECN') return { bg: 'rgba(234,179,8,0.16)', fg: '#facc15' };
  if (ev === 'SW_LINK_FAIL' || ev === 'SW_NODE_FAIL' || ev === 'SW_BTS') return { bg: 'rgba(239,68,68,0.20)', fg: '#f87171' };
  return { bg: 'transparent', fg: '#cbd5e1' };
}

function renderWireshark() {
  const card = document.getElementById('wiresharkCard');
  if (!card) return;
  if (!selectedFlowId || !lastSimData || !lastSimData.flow_packets) {
    card.style.display = 'none';
    return;
  }
  const allPkts = lastSimData.flow_packets[String(selectedFlowId)] || [];
  card.style.display = 'block';
  const cat = (lastSimData.flow_catalog || []).find(c => String(c.flow_id) === String(selectedFlowId));
  document.getElementById('wsTitle').textContent =
    `🦈 Wireshark 패킷 & 헤더 분석기 — Flow ${selectedFlowId}` + (cat ? ` (xPU ${cat.src} → xPU ${cat.dst})` : '');

  const qRaw = ((document.getElementById('wsFilter') && document.getElementById('wsFilter').value) || '').trim().toUpperCase();
  const pkts = allPkts.filter(p => {
    if (!qRaw) return true;
    if (qRaw === 'DATA') return p.event === 'TX_DATA' || p.event === 'RX_DATA';
    if (qRaw === 'RTX') return p.event === 'TX_RTX' || p.event.includes('FAIL') || p.event === 'TX_PROBE' || p.event === 'SW_BTS';
    if (qRaw.startsWith('PSN=')) return String(p.psn) === qRaw.slice(4);
    const hay = `${p.event} ${p.node} P${p.plane} PSN=${p.psn} ${p.ev} ECN=${p.ecn} ${p.extra}`.toUpperCase();
    return hay.includes(qRaw);
  });

  document.getElementById('wsCountBadge').textContent = `표시: ${pkts.length} / 전체 ${allPkts.length} 패킷`;
  const tbody = document.getElementById('wsPacketTbody');
  if (!pkts.length) {
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; color:#94a3b8">필터 조건에 일치하는 패킷이 없습니다.</td></tr>';
    document.getElementById('wsHeaderTree').textContent = '선택된 패킷 없음';
    document.getElementById('wsHexDump').textContent = '';
    return;
  }
  if (!selectedWsPktNo || !pkts.some(p => p.no === selectedWsPktNo)) {
    selectedWsPktNo = pkts[0].no;
  }

  tbody.innerHTML = pkts.map(p => {
    const col = wsRowColors(p.event);
    const isSel = p.no === selectedWsPktNo;
    const bg = isSel ? 'rgba(59,130,246,0.34)' : col.bg;
    const outline = isSel ? 'outline:1px solid #60a5fa;' : '';
    const info = `Node=${p.node}` + (p.ecn !== '0' ? ` [ECN=${p.ecn}]` : '') + (p.extra ? ` (${p.extra})` : '');
    return `<tr style="cursor:pointer; background:${bg}; ${outline}" onclick="selectWsPacket(${p.no})">
      <td class="mono">${p.no}</td>
      <td class="mono">${p.ts_us.toFixed(3)}</td>
      <td class="mono">F${String(p.frame_idx).padStart(2,'0')}</td>
      <td class="mono">xPU ${p.src}</td>
      <td class="mono">xPU ${p.dst}</td>
      <td class="mono" style="color:${col.fg}"><strong>${p.event}</strong></td>
      <td class="mono">${p.len_bytes} B</td>
      <td class="mono">${p.psn}</td>
      <td class="mono">${p.ev} (P${p.plane})</td>
      <td class="mono" style="color:#cbd5e1">${info}</td>
    </tr>`;
  }).join('');

  renderWsHeaderDetails(pkts.find(p => p.no === selectedWsPktNo) || pkts[0]);
}

function selectWsPacket(no) {
  selectedWsPktNo = no;
  renderWireshark();
  const allPkts = (lastSimData && lastSimData.flow_packets && lastSimData.flow_packets[String(selectedFlowId)]) || [];
  const pkt = allPkts.find(p => p.no === no);
  if (pkt && typeof pkt.frame_idx === 'number' && pkt.frame_idx !== customFrameIdx) {
    renderFrame(pkt.frame_idx);
  }
}

function renderWsHeaderDetails(p) {
  const tree = document.getElementById('wsHeaderTree');
  const hexEl = document.getElementById('wsHexDump');
  if (!p || !tree || !hexEl) return;
  const ecnDesc = p.ecn === '3' ? '0b11 / 3 (ECN Echo / CE)' : (p.ecn === '1' ? '0b01 / 1 (ECT / CE Marked)' : '0b00 / 0 (Not-ECN)');
  const isTrim = p.event === 'SW_TRIM' || p.event === 'RX_TRIM';
  const pktType = p.event.includes('NACK') ? 'UEC_NACK (0x04)' : (p.event.includes('ACK') ? 'UEC_ACK (0x02)' : (isTrim ? 'UEC_TRIMMED_DATA (0x03)' : (p.event === 'TX_PROBE' ? 'UEC_PROBE (0x05)' : 'UEC_DATA (0x01)')));
  const evNum = parseInt(p.ev, 16) || 0;
  const fidNum = parseInt(p.flow_id, 10) || 0;

  tree.innerHTML = `
    <details open style="margin-bottom:6px">
      <summary style="cursor:pointer; color:#38bdf8; font-weight:bold">Frame ${p.no}: ${p.len_bytes} bytes on wire (F${String(p.frame_idx).padStart(2,'0')} @ ${p.ts_us.toFixed(3)} us)</summary>
      <div style="padding-left:14px; color:#cbd5e1">
        • Flow ID: ${p.flow_id} | Event: <strong>${p.event}</strong> (${p.dir})<br/>
        • Capture Point: ${p.node} | Extra: ${p.extra || '-'}
      </div>
    </details>
    <details open style="margin-bottom:6px">
      <summary style="cursor:pointer; color:#4ade80; font-weight:bold">Rail-Optimized L2 Fabric Header (Src: xPU ${p.src} → Dst: xPU ${p.dst})</summary>
      <div style="padding-left:14px; color:#cbd5e1">
        • Src MAC / Port: 02:00:00:00:${String(Number(p.src)).padStart(2,'0')}:${String(p.plane).padStart(2,'0')} (xPU ${p.src}, Port P${p.plane})<br/>
        • Dst MAC / Port: 02:00:00:00:${String(Number(p.dst)).padStart(2,'0')}:${String(p.plane).padStart(2,'0')} (xPU ${p.dst}, Port P${p.plane})<br/>
        • Fabric Plane: Plane ${p.plane} (Upper Switch US${p.plane % 2}) | EtherType: 0x88B5 (UEC)
      </div>
    </details>
    <details open style="margin-bottom:6px">
      <summary style="cursor:pointer; color:#facc15; font-weight:bold">IPv4 / Congestion Header (10.0.0.${p.src} → 10.0.0.${p.dst})</summary>
      <div style="padding-left:14px; color:#cbd5e1">
        • Version: 4 | Protocol: UEC (UDP-encap) | Total Length: ${p.len_bytes} B<br/>
        • DSCP / ECN: ${ecnDesc}
      </div>
    </details>
    <details open>
      <summary style="cursor:pointer; color:#e879f9; font-weight:bold">UEC Transport / MRC Header (PSN=${p.psn}, EV=${p.ev})</summary>
      <div style="padding-left:14px; color:#cbd5e1">
        • Packet Type: ${pktType}<br/>
        • PSN (Packet Seq Num): <strong>${p.psn}</strong> (0x${p.psn.toString(16).padStart(4,'0')})<br/>
        • EV (Entropy / Path ID): <strong>${p.ev}</strong> (Plane P${p.plane})<br/>
        • Trimmed Payload: ${isTrim ? '<span style="color:#e879f9">Yes (Truncated to 64B Header)</span>' : 'No'}
      </div>
    </details>`;

  // Synthesize 32-byte L2+IP+UEC header hex dump from actual packet fields
  const b = [
    0x02, 0x00, 0x00, 0x00, Number(p.dst) & 0xff, p.plane & 0xff,
    0x02, 0x00, 0x00, 0x00, Number(p.src) & 0xff, p.plane & 0xff,
    0x88, 0xb5,
    0x45, Number(p.ecn) & 0x03, (p.len_bytes >> 8) & 0xff, p.len_bytes & 0xff,
    (fidNum >> 8) & 0xff, fidNum & 0xff, 0x40, 0x00,
    0x40, 0x11, 10, 0, 0, Number(p.src) & 0xff,
    10, 0, 0, Number(p.dst) & 0xff,
    isTrim ? 0x03 : (p.event.includes('NACK') ? 0x04 : (p.event.includes('ACK') ? 0x02 : 0x01)),
    p.plane & 0xff, (evNum >> 8) & 0xff, evNum & 0xff,
    (p.psn >> 24) & 0xff, (p.psn >> 16) & 0xff, (p.psn >> 8) & 0xff, p.psn & 0xff,
  ];
  let lines = [];
  for (let off = 0; off < b.length; off += 16) {
    const chunk = b.slice(off, off + 16);
    const hex = chunk.map(x => x.toString(16).padStart(2, '0')).join(' ').padEnd(47, ' ');
    const asc = chunk.map(x => (x >= 32 && x <= 126) ? String.fromCharCode(x) : '.').join('');
    lines.push(`${off.toString(16).padStart(4, '0')}  ${hex}  ${asc}`);
  }
  hexEl.textContent = lines.join('\\n');
}

function renderSingleFlowTrace() {
  const card = document.getElementById('flowTraceCard');
  if (!card) return;
  if (!selectedFlowId || !customFrames.length) {
    card.style.display = 'none';
    return;
  }
  card.style.display = 'block';
  const cat = (lastSimData && lastSimData.flow_catalog || []).find(c => String(c.flow_id) === String(selectedFlowId));
  document.getElementById('flowTraceTitle').textContent =
    `🔍 Flow ${selectedFlowId} 집중 트래킹` + (cat ? ` (xPU ${cat.src} → xPU ${cat.dst})` : '');
  document.getElementById('flowTraceStats').textContent = cat
    ? `총 TX:${cat.tx} | RTX:${cat.rtx} | ACK:${cat.ack} | Trim:${cat.trim} | NACK:${cat.nack} | Reroute:${cat.reroute}건`
    : '';

  const rows = customFrames.map((f, idx) => {
    const fl = (f.flow_stats || []).find(x => String(x.flow_id) === String(selectedFlowId));
    const tx = fl ? fl.tx_cnt : 0;
    const rtx = fl ? fl.rtx_cnt : 0;
    const evs = (f.events_log || []).filter(e => String(e.flow_id) === String(selectedFlowId));
    const trims = evs.filter(e => e.event === 'SW_TRIM' || e.event === 'RX_TRIM').length;
    const nacks = evs.filter(e => e.event === 'TX_NACK' || e.event === 'RX_NACK').length;
    const rrs = (f.reroutes || []).filter(r => String(r.flow_id) === String(selectedFlowId));
    const planes = fl ? Object.entries(fl.planes || {}).sort((a,b)=>parseInt(a[0].slice(1),10)-parseInt(b[0].slice(1),10)).map(([k,v])=>`${k}(${v})`).join(' ') : '-';
    return { idx, f, tx, rtx, total: tx + rtx, trims, nacks, rrs, planes };
  });

  const maxTot = Math.max(1, ...rows.map(r => r.total));
  const tbody = document.getElementById('flowFrameTbody');
  let sawNackOrTrim = false;
  tbody.innerHTML = rows.map(r => {
    if (r.trims > 0 || r.nacks > 0) sawNackOrTrim = true;
    const barW = Math.round((r.total / maxTot) * 100);
    const isSlow = sawNackOrTrim && r.total > 0 && r.total <= maxTot * 0.5 && r.trims === 0 && r.nacks === 0;
    const slowTag = (r.nacks > 0) ? '<span style="color:#fb923c; font-size:0.75rem"> ⬇ NACK(cwnd↓)</span>'
      : (isSlow ? '<span style="color:#facc15; font-size:0.75rem"> ⬇ Slow Down</span>' : '');
    const rrStr = r.rrs.length
      ? r.rrs.slice(0, 3).map(x => `${x.old_ev}(${x.old_plane})→<strong>${x.new_ev}(${x.new_plane})</strong>`).join('<br/>')
      : '-';
    const curStyle = (r.idx === customFrameIdx) ? 'background:rgba(56,189,248,0.14); outline:1px solid #38bdf8;' : '';
    return `<tr style="cursor:pointer; ${curStyle}" onclick="renderFrame(${r.idx})">
      <td class="mono">${r.f.t_start_us.toFixed(1)} ~ ${r.f.t_end_us.toFixed(1)} us</td>
      <td class="mono">
        <div style="display:flex; align-items:center; gap:6px">
          <div style="width:70px; height:8px; background:#0f172a; border-radius:4px; overflow:hidden">
            <div style="width:${barW}%; height:100%; background:${r.rtx>0 ? '#22c55e' : '#38bdf8'}"></div>
          </div>
          <span>TX:${r.tx} RTX:${r.rtx}${slowTag}</span>
        </div>
      </td>
      <td class="mono" style="color:${r.trims>0 ? '#e879f9' : '#64748b'}">${r.trims || 0}</td>
      <td class="mono" style="color:${r.nacks>0 ? '#fb923c' : '#64748b'}">${r.nacks || 0}</td>
      <td class="mono">${r.planes}</td>
      <td class="mono" style="color:#4ade80">${rrStr}</td>
    </tr>`;
  }).join('');
}

function toggleEventScope() {
  eventScopeCum = !eventScopeCum;
  document.getElementById('btnEventScope').textContent =
    eventScopeCum ? '보기: 0 ~ 현재 누적' : '보기: 현재 구간';
  if (lastFrameData) renderTimelineTables(lastFrameData);
}

function evBadgeHtml(ev) {
  let bg = 'rgba(100,116,139,0.2)', fg = '#cbd5e1';
  if (ev === 'SW_TRIM' || ev === 'RX_TRIM') { bg = 'rgba(217,70,239,0.2)'; fg = '#e879f9'; }
  else if (ev === 'TX_NACK' || ev === 'RX_NACK') { bg = 'rgba(56,189,248,0.2)'; fg = '#38bdf8'; }
  else if (ev === 'SW_BTS') { bg = 'rgba(251,146,60,0.2)'; fg = '#fb923c'; }
  else if (ev === 'SW_LINK_FAIL' || ev === 'SW_NODE_FAIL') { bg = 'rgba(239,68,68,0.22)'; fg = '#fca5a5'; }
  else if (ev === 'TX_PROBE') { bg = 'rgba(250,204,21,0.2)'; fg = '#facc15'; }
  else if (ev === 'SW_ECN') { bg = 'rgba(245,158,11,0.2)'; fg = '#f59e0b'; }
  return `<span class="badge" style="background:${bg}; color:${fg}">${ev}</span>`;
}

function renderTimelineTables(fr) {
  // 1. Current PSN & Traffic Flow Table
  const fSummary = document.getElementById('frameFlowSummary');
  const fTbody = document.getElementById('frameFlowTbody');
  const allFlows = fr.flow_stats || [];
  const flows = selectedFlowId ? allFlows.filter(f => String(f.flow_id) === String(selectedFlowId)) : allFlows;
  const psnTxt = (fr.psn_min !== null && fr.psn_min !== undefined) ? `PSN ${fr.psn_min} ~ ${fr.psn_max}` : 'PSN -';
  const activePlanes = (fr.plane_pct || []).map((p, i) => p > 0 ? `P${i}:${p}%` : null).filter(Boolean).join(' ');
  fSummary.textContent = (selectedFlowId ? `[Flow ${selectedFlowId} 필터] ` : '') + `${psnTxt} | 활성 플로우: ${flows.length}개 | Plane 분산: ${activePlanes || '-'}`;

  if (!flows.length) {
    fTbody.innerHTML = '<tr><td colspan="5" style="color:#94a3b8; text-align:center">이 타임라인 구간에 전송된 트래픽이 없습니다.</td></tr>';
  } else {
    fTbody.innerHTML = flows.map(f => {
      const planeStr = Object.entries(f.planes || {}).sort((a,b)=>parseInt(a[0].slice(1),10)-parseInt(b[0].slice(1),10)).map(([k,v])=>`${k}(${v})`).join(' ');
      const evLimit = selectedFlowId ? 999 : 8;
      const evStr = Object.entries(f.evs || {}).sort((a,b)=>(b[1]-a[1]) || (parseInt(a[0],16)-parseInt(b[0],16))).slice(0, evLimit).map(([k,v])=>`${k}:${v}`).join(' ');
      const psnCell = (f.ev_psns && f.ev_psns.length)
        ? `PSN ${f.psn_min} ~ ${f.psn_max}<br/><span style="color:#e879f9; font-size:0.75rem">Trim/NACK PSN: ${f.ev_psns.join(', ')}</span>`
        : `PSN ${f.psn_min} ~ ${f.psn_max}`;
      const selBg = (String(f.flow_id) === String(selectedFlowId)) ? 'background:rgba(37,99,235,0.18);' : '';
      return `<tr style="cursor:pointer; ${selBg}" onclick="onSelectFocusFlow('${f.flow_id}')" title="클릭하여 Flow ${f.flow_id}만 집중 트래킹">
        <td class="mono"><strong>Flow ${f.flow_id}</strong></td>
        <td class="mono">xPU ${f.src} → Leaf → Spine → Leaf → xPU ${f.dst}</td>
        <td class="mono" style="color:#38bdf8">${psnCell}</td>
        <td class="mono">TX:${f.tx_cnt} / RTX:${f.rtx_cnt} / ACK:${f.ack_cnt}</td>
        <td class="mono"><span style="color:#22c55e">${planeStr || '-'}</span><br/><span style="color:#94a3b8; font-size:0.75rem">EV: ${evStr || '-'}</span></td>
      </tr>`;
    }).join('');
  }

  // 2. Timeline Events Table (TRIM, NACK, Fail, BTS, Probe, ECN)
  const ecnMap = fr.ecn_summary || {};
  const ecnTop = Object.entries(ecnMap).sort((a,b)=>b[1]-a[1]).slice(0,4).map(([k,v])=>`${k}(${v})`).join(', ');
  document.getElementById('frameEcnBadge').textContent = ecnTop ? `구간 ECN: ${ecnTop}` : '구간 ECN: 없음';

  let evList = [];
  if (eventScopeCum) {
    for (let i = 0; i <= customFrameIdx; i++) {
      const f = customFrames[i];
      if (f && f.events_log) {
        for (const e of f.events_log) {
          if (!selectedFlowId || String(e.flow_id) === String(selectedFlowId)) {
            evList.push({ ...e, _cur: i === customFrameIdx });
          }
        }
      }
    }
    evList = (selectedFlowId ? evList : evList.slice(-500));
  } else {
    evList = (fr.events_log || [])
      .filter(e => !selectedFlowId || String(e.flow_id) === String(selectedFlowId))
      .map(e => ({ ...e, _cur: true }));
  }
  evList.sort((a, b) => (a.ts_us - b.ts_us) || (Number(a.flow_id) - Number(b.flow_id)) || (a.psn - b.psn));

  const eTbody = document.getElementById('frameEventsTbody');
  if (!evList.length) {
    eTbody.innerHTML = '<tr><td colspan="6" style="color:#94a3b8; text-align:center">이 구간에 기록된 TRIM / NACK / 장애 이벤트가 없습니다.</td></tr>';
  } else {
    eTbody.innerHTML = evList.map(e => {
      const rowBg = e._cur ? 'background:rgba(56,189,248,0.06)' : '';
      return `<tr style="${rowBg}">
        <td class="mono">${e.ts_us.toFixed(1)} us</td>
        <td>${evBadgeHtml(e.event)}</td>
        <td class="mono"><strong>${e.where}</strong></td>
        <td class="mono">Flow ${e.flow_id} / PSN ${e.psn}</td>
        <td class="mono">${e.ev} (${e.plane})</td>
        <td style="font-size:0.82rem; color:#cbd5e1">${e.detail}</td>
      </tr>`;
    }).join('');
  }

  // 3. EV Reroute Table (up to current frame, highlighting current frame)
  const rTbody = document.getElementById('rerouteTbody');
  const rBadge = document.getElementById('rerouteSummaryBadge');
  let rerouteRows = [];
  let curFrameReroutes = 0;
  for (let i = 0; i <= customFrameIdx; i++) {
    const f = customFrames[i];
    if (f && f.reroutes) {
      for (const r of f.reroutes) {
        if (selectedFlowId && String(r.flow_id) !== String(selectedFlowId)) continue;
        if (i === customFrameIdx) curFrameReroutes++;
        rerouteRows.push({ ...r, _cur: i === customFrameIdx });
      }
    }
  }
  const totalReroutes = (lastSimData && lastSimData.stages && lastSimData.stages.stage3) ? lastSimData.stages.stage3.reroute_cnt : rerouteRows.length;
  rBadge.textContent = `현재 구간: ${curFrameReroutes}건 | 현재까지 누적: ${rerouteRows.length}건 (전체 ${totalReroutes}건)`;

  if (!rerouteRows.length) {
    rTbody.innerHTML = '<tr><td colspan="6" style="color:#94a3b8; text-align:center">현재 시각까지 발생한 EV 재분배(Reroute)가 없습니다.</td></tr>';
  } else {
    const showRows = (selectedFlowId ? rerouteRows : rerouteRows.slice(-300));
    showRows.sort((a, b) => (a.ts_us - b.ts_us) || (Number(a.flow_id) - Number(b.flow_id)) || (a.psn - b.psn));
    rTbody.innerHTML = showRows.map(r => {
      const rowBg = r._cur ? 'background:rgba(34,197,94,0.10)' : '';
      return `<tr style="${rowBg}">
        <td class="mono">${r.ts_us.toFixed(1)} us</td>
        <td class="mono">Flow ${r.flow_id} (xPU ${r.src} → ${r.dst})</td>
        <td class="mono">PSN ${r.psn}</td>
        <td class="mono" style="color:#f87171">${r.old_ev} (${r.old_plane})</td>
        <td class="mono" style="color:#22c55e"><strong>→ ${r.new_ev} (${r.new_plane})</strong></td>
        <td style="font-size:0.82rem; color:#cbd5e1">${r.reason}</td>
      </tr>`;
    }).join('');
  }
}

function renderFrame(idx) {
  if (!customFrames.length) return;
  customFrameIdx = Math.max(0, Math.min(customFrames.length - 1, idx));
  document.getElementById('timeSlider').value = customFrameIdx;
  const fr = customFrames[customFrameIdx];
  document.getElementById('frameTimeLabel').textContent =
    `${fr.t_start_us.toFixed(1)} ~ ${fr.t_end_us.toFixed(1)} us  [${fr.phase}]`;
  lastFrameData = fr;
  lastLinkHeat = fr.link_heat || {};
  drawTopo();
  renderTimelineTables(fr);
  renderSingleFlowTrace();
  updatePlayButton();
}

function updatePlayButton() {
  const btn = document.getElementById('btnPlay');
  if (!btn) return;
  if (playTimer) {
    btn.textContent = '⏸ Pause';
  } else if (customFrames.length > 0 && customFrameIdx >= customFrames.length - 1) {
    btn.textContent = '↻ Replay';
  } else {
    btn.textContent = '▶ Play';
  }
}

function onScrub(val) {
  renderFrame(parseInt(val, 10));
}

function stepFrame(delta) {
  if (!customFrames.length) return;
  renderFrame(customFrameIdx + delta);
}

function toggleLoop() {
  playLoop = !playLoop;
  document.getElementById('btnLoop').textContent = `🔁 Loop: ${playLoop ? 'ON' : 'OFF'}`;
}

function togglePlay() {
  if (playTimer) {
    clearInterval(playTimer);
    playTimer = null;
    updatePlayButton();
    return;
  }
  if (customFrames.length > 0 && customFrameIdx >= customFrames.length - 1) {
    renderFrame(0);
  }
  playTimer = setInterval(() => {
    let next = customFrameIdx + 1;
    if (next >= customFrames.length) {
      if (playLoop) next = 0;
      else {
        clearInterval(playTimer);
        playTimer = null;
        updatePlayButton();
        return;
      }
    }
    renderFrame(next);
  }, 450);
  updatePlayButton();
}

function renderBeforeAfter(data) {
  lastSimData = data;
  selectedFlowId = '';
  const sel = document.getElementById('flowFocusSelect');
  if (sel) {
    const cat = data.flow_catalog || [];
    sel.innerHTML = `<option value="">전체 Flow 보기 (총 ${cat.length}개)</option>` + cat.map(c => {
      const hasEvents = (c.trim + c.nack + c.reroute) > 0;
      const star = hasEvents ? '★ ' : '';
      return `<option value="${c.flow_id}">${star}Flow ${c.flow_id} (xPU ${c.src}→${c.dst}) [Trim:${c.trim}, NACK:${c.nack}, Reroute:${c.reroute}]</option>`;
    }).join('');
  }
  renderSingleFlowTrace();
  const st = data.stages || {};
  const stageBox = document.getElementById('stageFlowBox');
  if (stageBox && st.stage1) {
    const s1 = st.stage1, s2 = st.stage2, s3 = st.stage3, s4 = st.stage4;
    const verdictColor = s4.ok ? '#22c55e' : '#ef4444';
    stageBox.innerHTML = `
      <div class="card" style="background:#0b1220; border-color:#334155">
        <div class="label">1. 장애 전 (Baseline)</div>
        <div class="mono" style="margin-top:6px; font-size:0.79rem; line-height:1.45">
          • 활성 Plane: <strong>${s1.active_planes}</strong><br/>
          • 전송 패킷: <strong>${s1.tx_pkts}</strong><br/>
          • 분산 상태: ${s1.desc}
        </div>
      </div>
      <div class="card" style="background:#0b1220; border-color:${s2.has_fault ? '#ef4444' : '#334155'}">
        <div class="label">2. 장애 발생 및 감지 (Fault)</div>
        <div class="mono" style="margin-top:6px; font-size:0.79rem; line-height:1.45">
          • 주입 대상: <strong>${s2.target}</strong><br/>
          • 드랍 감지: <strong>FAIL=${s2.fail_pkts}</strong> (Probe=${s2.probes})<br/>
          • 혼잡/절단: ECN=${s2.ecn}, Trim=${s2.trim}
        </div>
      </div>
      <div class="card" style="background:#0b1220; border-color:${s3.rtx > 0 ? '#22d3ee' : '#334155'}">
        <div class="label">3. 우회 및 트래픽 재분배 (Reroute)</div>
        <div class="mono" style="margin-top:6px; font-size:0.79rem; line-height:1.45">
          • 우회 재전송: <strong>Rtx=${s3.rtx}</strong> (SLEEK=${s3.sleek})<br/>
          • EV 경로 전환: <strong>${s3.reroute_cnt}건</strong><br/>
          • After 누적 점유: ${s3.plane_summary}
        </div>
      </div>
      <div class="card" style="background:#0b1220; border-color:${verdictColor}">
        <div class="label">4. 최종 마무리 결과 (Final Verdict)</div>
        <div class="mono" style="margin-top:6px; font-size:0.79rem; line-height:1.45">
          • 판정: <strong style="color:${verdictColor}">${s4.verdict}</strong> (rc=${data.rc})<br/>
          • 완주 통계: New=${s4.new_pkts}, ACKs=${s4.acks}<br/>
          • 요약: ${s4.summary}
        </div>
      </div>`;
  }

  // 4-A. xPU EV Distribution Table
  const evTbody = document.getElementById('evDistTbody');
  const beforeEv = data.before_ev || {};
  const afterEv = data.after_ev || {};
  const srcs = Array.from(new Set([...Object.keys(beforeEv), ...Object.keys(afterEv)])).sort((a,b) => Number(a)-Number(b));
  if (!srcs.length) {
    evTbody.innerHTML = '<tr><td colspan="3" style="color:#94a3b8; text-align:center">xPU별 EV 데이터가 없습니다.</td></tr>';
  } else {
    evTbody.innerHTML = srcs.slice(0, 16).map(s => {
      const bTop = Object.entries(beforeEv[s] || {}).sort((a,b)=>b[1]-a[1]).slice(0, 4).map(([k,v])=>`${k}:${v}`).join(' ') || '-';
      const aTop = Object.entries(afterEv[s] || {}).sort((a,b)=>b[1]-a[1]).slice(0, 4).map(([k,v])=>`${k}:${v}`).join(' ') || '-';
      return `<tr>
        <td class="mono"><strong>xPU ${s}</strong></td>
        <td class="mono" style="color:#94a3b8">${bTop}</td>
        <td class="mono" style="color:#38bdf8">${aTop}</td>
      </tr>`;
    }).join('');
  }

  // 4-B. Switch Link Trim / ECN / Fail Table
  const linkTbody = document.getElementById('linkStatsTbody');
  const lh = data.link_heat || {};
  const bt = data.before_trim || {};
  const at = data.after_trim || {};
  const allLinks = Array.from(new Set([...Object.keys(lh), ...Object.keys(bt), ...Object.keys(at)]));
  allLinks.sort((a, b) => {
    const sa = (lh[a]?.fail||0)*1000 + (lh[a]?.trim||0)*100 + (lh[a]?.ecn||0);
    const sb = (lh[b]?.fail||0)*1000 + (lh[b]?.trim||0)*100 + (lh[b]?.ecn||0);
    return (sb - sa) || a.localeCompare(b);
  });
  if (!allLinks.length) {
    linkTbody.innerHTML = '<tr><td colspan="5" style="color:#94a3b8; text-align:center">링크별 Trim/ECN/Fail 이벤트가 없습니다.</td></tr>';
  } else {
    linkTbody.innerHTML = allLinks.slice(0, 100).map(lnk => {
      const h = lh[lnk] || {ecn:0, trim:0, fail:0};
      return `<tr>
        <td class="mono"><strong>${lnk}</strong></td>
        <td class="mono">${bt[lnk] || 0}</td>
        <td class="mono" style="color:${(at[lnk]||0)>0 ? '#e879f9' : '#cbd5e1'}">${at[lnk] || 0}</td>
        <td class="mono" style="color:${h.ecn>0 ? '#f59e0b' : '#cbd5e1'}">${h.ecn || 0}</td>
        <td class="mono" style="color:${h.fail>0 ? '#ef4444' : '#cbd5e1'}">${h.fail || 0}</td>
      </tr>`;
    }).join('');
  }
}

function applyRecommendedEcn() {
  const spd = parseInt(document.getElementById('inLinkSpeed').value || '100000', 10);
  if (spd >= 400000) {
    document.getElementById('inQueue').value = 160;
    document.getElementById('inEcnLow').value = 48;
    document.getElementById('inEcnHigh').value = 112;
  } else {
    document.getElementById('inQueue').value = 64;
    document.getElementById('inEcnLow').value = 16;
    document.getElementById('inEcnHigh').value = 48;
  }
}

function onSpeedChange() {
  // Optional: keep user's manual values or let them click '권장 기준값 적용'
}

async function runCustomTopo() {
  if (!topoModel) recalcTopo();
  if (playTimer) togglePlay();
  const btn = document.getElementById('btnCustomRun');
  btn.disabled = true;
  btn.textContent = 'Running...';
  try {
    const res = await fetch('api/run_custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nsrv: topoModel.nodesPerPlane || topoModel.nsrv,
        planes: topoModel.planes || 1,
        tiers: topoModel.tiers,
        traffic: document.getElementById('inTraffic').value,
        algo: document.getElementById('inAlgo').value,
        fail_nodes: [...failNodes],
        fail_links: [...failLinks],
        fail_at_us: parseInt(document.getElementById('inFailAt').value || '0', 10),
        recover_at_us: parseInt(document.getElementById('inRecoverAt').value || '0', 10),
        linkspeed: parseInt(document.getElementById('inLinkSpeed').value || '100000', 10),
        q_pkts: parseInt(document.getElementById('inQueue').value || '16', 10),
        ecn_low: parseInt(document.getElementById('inEcnLow').value || '4', 10),
        ecn_high: parseInt(document.getElementById('inEcnHigh').value || '12', 10),
        end_us: parseInt(document.getElementById('inEndUs').value || '10000', 10),
        n_frames: parseInt(document.getElementById('inFrames').value || '16', 10),
      })
    });
    const data = await res.json();
    document.getElementById('customResultCard').style.display = 'block';
    document.getElementById('customMetrics').textContent =
      `rc=${data.rc} | New=${data.hw.new||0}, Rtx=${data.hw.rtx||0}, ACKs=${data.hw.acks||0}, NACKs=${data.hw.nacks||0}, sleek=${data.hw.sleek||0} | ` +
      `SW_LINK_FAIL=${data.events.SW_LINK_FAIL||0}, SW_NODE_FAIL=${data.events.SW_NODE_FAIL||0}, SW_TRIM=${data.events.SW_TRIM||0}, SW_ECN=${data.events.SW_ECN||0}`;
    customFrames = data.frames || [];
    const slider = document.getElementById('timeSlider');
    slider.max = Math.max(0, customFrames.length - 1);
    renderBeforeAfter(data);
    if (customFrames.length > 0) {
      renderFrame(0);
      togglePlay();
    } else {
      lastLinkHeat = data.link_heat || {};
      drawTopo();
    }
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run Custom Topology Test';
  }
}

async function poll() {
  try {
    const res = await fetch('api/status');
    const data = await res.json();
    const isRunning = Boolean(data.runner_active);
    document.getElementById('btnRun').disabled = isRunning;
    document.getElementById('btnStop').disabled = !isRunning;

    const st = data.suite_status || 'IDLE';
    const stEl = document.getElementById('suiteStatus');
    stEl.textContent = st;
    stEl.style.color = st === 'PASS' ? 'var(--pass)' : (st === 'FAIL' ? 'var(--fail)' : (st === 'RUNNING' ? 'var(--run)' : 'var(--text)'));

    const tests = Object.values(data.tests || {});
    let pass = 0, fail = 0, done = 0;
    const tbody = document.getElementById('testRows');
    tbody.innerHTML = '';
    for (const t of tests) {
      if (t.status === 'PASS') { pass++; done++; }
      else if (t.status === 'FAIL' || t.status === 'TIMEOUT') { fail++; done++; }
      const tr = document.createElement('tr');
      const wvBtn = t.wire_view ? `<button class="btn-view" onclick="openWireView('${t.wire_view}')">Wire View</button>` : '-';
      tr.innerHTML = `
        <td class="mono"><strong>${t.id}</strong></td>
        <td>${t.scenario}</td>
        <td><span class="badge ${t.status}">${t.status}</span></td>
        <td class="mono">${t.duration_sec != null ? t.duration_sec.toFixed(2) + 's' : '-'}</td>
        <td class="mono">${t.detail || ''}</td>
        <td>${wvBtn}</td>
      `;
      tbody.appendChild(tr);
    }

    const total = tests.length || 10;
    document.getElementById('passCnt').textContent = pass;
    document.getElementById('failCnt').textContent = fail;
    document.getElementById('doneCnt').textContent = `(${done}/${total})`;
    document.getElementById('progressBar').style.width = ((done * 100) / total) + '%';
    document.getElementById('curTest').textContent = data.current_test || '-';

    if (data.disk) {
      document.getElementById('diskInfo').textContent = `${data.disk.free_gb} GB (${data.disk.used_pct}% used)`;
    }
    document.getElementById('suiteMeta').textContent =
      `Started: ${data.started_at || '-'} | Finished: ${data.finished_at || (isRunning ? 'In progress...' : '-')}`;

    const hbBox = document.getElementById('hbBox');
    if (data.heartbeat && isRunning) {
      hbBox.classList.add('active');
      const h = data.heartbeat;
      document.getElementById('hbName').textContent = h.sub_name;
      const pct = h.end_us > 0 ? ((h.sim_us * 100) / h.end_us).toFixed(1) : '0.0';
      document.getElementById('hbMetrics').innerHTML = `
        <span>sim_time: <strong>${h.sim_us}/${h.end_us} us (${pct}%)</strong></span>
        <span>new: <strong>${h.new}</strong></span>
        <span>rtx: <strong>${h.rtx}</strong></span>
        <span>acks: <strong>${h.acks}</strong></span>
        <span>sleek: <strong>${h.sleek}</strong></span>
        <span>trace: <strong>${h.trace_events.toLocaleString()} ev / ${fmtBytes(h.trace_bytes)}</strong></span>
      `;
    } else {
      hbBox.classList.remove('active');
    }

    const logBox = document.getElementById('logBox');
    const atBottom = logBox.scrollHeight - logBox.scrollTop - logBox.clientHeight < 30;
    logBox.textContent = (data.logs || []).join('\\n');
    if (atBottom) logBox.scrollTop = logBox.scrollHeight;
  } catch (e) {
    console.error(e);
  }
}

setInterval(poll, 500);
poll();
recalcTopo();
</script>
</body>
</html>
"""


def _get_status_payload() -> dict:
    du = shutil.disk_usage("/")
    disk = {
        "total_gb": round(du.total / (1024**3), 1),
        "used_gb": round(du.used / (1024**3), 1),
        "free_gb": round(du.free / (1024**3), 1),
        "used_pct": round(du.used * 100.0 / du.total, 1),
    }
    if LIVE_STATUS_PATH.exists():
        try:
            data = json.loads(LIVE_STATUS_PATH.read_text())
        except Exception:
            data = {"suite_status": "IDLE", "tests": {}, "logs": []}
    else:
        data = {"suite_status": "IDLE", "tests": {}, "logs": []}

    with _PROC_LOCK:
        active = _RUNNER_PROC is not None and _RUNNER_PROC.poll() is None
    if not active and data.get("suite_status") == "RUNNING":
        data["suite_status"] = "STOPPED"
        for t in data.get("tests", {}).values():
            if t.get("status") == "RUNNING":
                t["status"] = "STOPPED"
        try:
            LIVE_STATUS_PATH.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
    data["runner_active"] = active
    data["disk"] = disk
    return data


def _run_custom_topology(cfg: dict) -> dict:
    nsrv = int(cfg.get("nsrv", 8))
    planes = max(1, min(8, int(cfg.get("planes", 1))))
    tiers = int(cfg.get("tiers", 2))
    traffic = cfg.get("traffic", "incast")
    algo = cfg.get("algo", "reps")
    fail_nodes = [x for x in cfg.get("fail_nodes", []) if x]
    fail_links = [x for x in cfg.get("fail_links", []) if x]
    fail_at_us = int(cfg.get("fail_at_us", 0))
    recover_at_us = int(cfg.get("recover_at_us", 0))

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    cm_path = REPORTS_DIR / "custom_test.cm"
    trace_path = REPORTS_DIR / "custom_trace.csv"
    out_dat = REPORTS_DIR / "custom_out.dat"

    conns = []
    flow_endpoints_cm = {}
    if traffic == "all_to_all":
        fid = 1
        step = max(1, nsrv // 8)
        for s in range(0, nsrv, step):
            for d in range(0, nsrv, step):
                if s != d:
                    conns.append(f"{s}->{d} id {fid} start 0 size 262144")
                    flow_endpoints_cm[str(fid)] = (str(s), str(d))
                    fid += 1
    else:
        dst = nsrv - 1
        for s in range(nsrv - 1):
            conns.append(f"{s}->{dst} id {s + 1} start 0 size 262144")
            flow_endpoints_cm[str(s + 1)] = (str(s), str(dst))

    cm_path.write_text(f"Nodes {nsrv}\nConnections {len(conns)}\n" + "\n".join(conns) + "\n")

    env = os.environ.copy()
    env["MRC_TRACE_FILE"] = str(trace_path)
    failed_plane_ids = set()
    if fail_links:
        # Include N{s}-P{r} -> LS{s//2}->US{r%2}, reverse direction, and LSx / LS_x variants
        bidir = []
        for lnk in fail_links:
            m_np = re.match(r"^N(\d+)-P(\d+)$", lnk)
            if m_np:
                s_idx, r_idx = int(m_np.group(1)), int(m_np.group(2))
                mapped = f"LS{s_idx // 2}->US{r_idx % 2}"
                variants = {mapped, re.sub(r"\bLS(\d+)\b", r"LS_\1", mapped)}
            else:
                variants = {lnk, re.sub(r"\bLS(\d+)\b", r"LS_\1", lnk)}
            for v in list(variants):
                bidir.append(v)
                if "->" in v:
                    a, b = v.split("->", 1)
                    bidir.append(f"{b}->{a}")
        env["MRC_FAIL_LINKS"] = ",".join(dict.fromkeys(bidir))
    if fail_nodes:
        expanded = []
        for nd in fail_nodes:
            m_us = re.match(r"^(?:US|P)(\d+)$", nd)
            if m_us:
                p_idx = int(m_us.group(1))
                failed_plane_ids.add(p_idx)
                expanded.append(f"US{p_idx % 2}")
            else:
                expanded.append(nd)
                if re.match(r"^LS\d+$", nd):
                    expanded.append("LS_" + nd[2:])
        env["MRC_FAIL_NODES"] = ",".join(dict.fromkeys(expanded))
    if fail_at_us > 0:
        env["MRC_FAIL_AT_US"] = str(fail_at_us)
    if recover_at_us > 0:
        env["MRC_RECOVER_AT_US"] = str(recover_at_us)

    linkspeed = int(cfg.get("linkspeed", 100000))
    if linkspeed not in (100000, 400000):
        linkspeed = 100000
    q_pkts = max(4, min(512, int(cfg.get("q_pkts", 16))))
    ecn_low = max(1, min(q_pkts - 1, int(cfg.get("ecn_low", 4))))
    ecn_high = max(ecn_low + 1, min(q_pkts, int(cfg.get("ecn_high", 12))))
    end_us = max(100, min(100000, int(cfg.get("end_us", 10000))))
    n_frames = max(8, min(128, int(cfg.get("n_frames", 16))))

    cmd = [
        str(BIN_UEC), "-o", str(out_dat),
        "-nodes", str(nsrv), "-tiers", str(tiers), "-planes", str(planes),
        "-tm", str(cm_path),
        "-sender_cc_only", "-sender_cc_algo", "nscc",
        "-load_balancing_algo", algo, "-sleek",
        "-queue_type", "composite_ecn", "-q", str(q_pkts), "-ecn", str(ecn_low), str(ecn_high),
        "-cwnd", "30", "-mtu", "4096", "-paths", "16", "-linkspeed", str(linkspeed), "-end", str(end_us)
    ]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120, check=False)
    stdout = proc.stdout + "\n" + proc.stderr
    m = re.search(
        r"New:\s*(\d+)\s+Rtx:\s*(\d+)\s+RTS:\s*(\d+)\s+Bounced:\s*(\d+)\s+ACKs:\s*(\d+)\s+NACKs:\s*(\d+)\s+Pulls:\s*(\d+)\s+sleek_pkts:\s*(\d+)",
        stdout,
    )
    hw = {}
    if m:
        hw = {
            "new": int(m.group(1)), "rtx": int(m.group(2)), "rts": int(m.group(3)),
            "bounced": int(m.group(4)), "acks": int(m.group(5)), "nacks": int(m.group(6)),
            "pulls": int(m.group(7)), "sleek": int(m.group(8)),
        }

    events = Counter()
    link_heat = defaultdict(lambda: {"ecn": 0, "trim": 0, "fail": 0})
    before_ev = defaultdict(Counter)
    after_ev = defaultdict(Counter)
    before_trim = Counter()
    after_trim = Counter()
    tx_ev = {}
    flow_endpoints = dict(flow_endpoints_cm)
    trim_nack_keys = set()
    reroutes = []
    reroute_ts = []
    reroute_items = []
    rows_parsed = []
    tx_rows = []
    tx_detail_rows = []
    timeline_raw = []
    flow_packets_raw = defaultdict(list)
    fail_at_ns = fail_at_us * 1000

    def _parse_ev(ev_s):
        try:
            return int(ev_s, 16)
        except Exception:
            return 0

    if trace_path.exists():
        with trace_path.open("r", newline="") as f:
            for row in csv.DictReader(f):
                ev_name = row.get("event") or ""
                ts_str = row.get("ts_ns") or ""
                if not ev_name or not ts_str:
                    continue
                events[ev_name] += 1
                ts_ns = int(ts_str)
                node = row.get("node") or ""
                link = node.split(")", 1)[-1].split("(", 1)[0] if "->" in node else None
                flow_id = row.get("flow_id") or "0"
                src_id = row.get("src") or "0"
                dst_id = row.get("dst") or "0"
                psn_str = row.get("psn") or "0"
                try:
                    psn_int = int(psn_str)
                except Exception:
                    psn_int = 0
                ev_str = row.get("ev") or "0x0000"
                ev_num = _parse_ev(ev_str)
                ecn_flag = row.get("ecn") or "0"
                extra = row.get("extra") or ""

                if flow_id in flow_endpoints:
                    true_src, true_dst = flow_endpoints[flow_id]
                else:
                    true_src, true_dst = src_id, dst_id
                    if ev_name in ("TX_DATA", "TX_RTX"):
                        flow_endpoints[flow_id] = (true_src, true_dst)

                is_rev_pkt = ev_name in ("TX_NACK", "RX_NACK", "RX_ACK")
                pkt_src = str(true_dst if is_rev_pkt else true_src)
                pkt_dst = str(true_src if is_rev_pkt else true_dst)
                pkt_len = 64 if ev_name in ("RX_TRIM", "TX_NACK", "RX_NACK", "RX_ACK", "SW_BTS", "TX_PROBE") else 4096
                flow_packets_raw[flow_id].append({
                    "ts_ns": ts_ns,
                    "ts_us": round(ts_ns / 1000.0, 3),
                    "event": ev_name,
                    "node": node,
                    "src": pkt_src,
                    "dst": pkt_dst,
                    "flow_id": flow_id,
                    "psn": psn_int,
                    "ev": ev_str,
                    "plane": ev_num % planes,
                    "ecn": ecn_flag,
                    "len_bytes": pkt_len,
                    "dir": "REV" if is_rev_pkt else "FWD",
                    "extra": extra,
                })

                if link:
                    if ev_name == "SW_ECN":
                        link_heat[link]["ecn"] += 1
                    elif ev_name == "SW_TRIM":
                        link_heat[link]["trim"] += 1
                        if ts_ns < fail_at_ns:
                            before_trim[link] += 1
                        else:
                            after_trim[link] += 1
                    elif ev_name in ("SW_LINK_FAIL", "SW_NODE_FAIL"):
                        link_heat[link]["fail"] += 1

                if ev_name in ("TX_DATA", "TX_RTX"):
                    tx_rows.append((ts_ns, ev_num))
                    tx_detail_rows.append((ts_ns, ev_name, flow_id, true_src, true_dst, psn_int, ev_str, ev_num))
                    if ts_ns < fail_at_ns:
                        before_ev[true_src][ev_str] += 1
                    else:
                        after_ev[true_src][ev_str] += 1
                elif ev_name == "RX_ACK":
                    tx_detail_rows.append((ts_ns, ev_name, flow_id, true_src, true_dst, psn_int, ev_str, ev_num))

                key = (flow_id, psn_str)
                if ev_name in ("SW_TRIM", "RX_TRIM", "TX_NACK", "RX_NACK", "SW_BTS"):
                    trim_nack_keys.add(key)

                if ev_name == "TX_DATA":
                    tx_ev[key] = ev_str
                elif ev_name == "TX_RTX":
                    old_ev = tx_ev.get(key, "?")
                    if old_ev != ev_str:
                        reroute_ts.append(ts_ns)
                        reroute_items.append((ts_ns, flow_id, true_src, true_dst, psn_int, old_ev, _parse_ev(old_ev), ev_str, ev_num))
                        if len(reroutes) < 50:
                            reroutes.append(f"Flow {flow_id} (xPU {true_src}) PSN {psn_str} @ {ts_ns/1000:.1f}us: EV {old_ev} -> {ev_str}")

                if link and ev_name in ("SW_ECN", "SW_TRIM", "SW_LINK_FAIL", "SW_NODE_FAIL"):
                    rows_parsed.append((ts_ns, ev_name, link, ev_num % planes))

                if ev_name in ("SW_LINK_FAIL", "SW_NODE_FAIL", "SW_TRIM", "RX_TRIM", "TX_NACK", "RX_NACK", "SW_BTS", "TX_PROBE", "SW_ECN"):
                    ev_s, ev_d = (true_dst, true_src) if ev_name in ("TX_NACK", "RX_NACK") else (true_src, true_dst)
                    timeline_raw.append((ts_ns, ev_name, link or node, flow_id, ev_s, ev_d, psn_int, ev_str, ev_num, ecn_flag, extra))

    frames = []
    all_ts = [r[0] for r in rows_parsed] + [t[0] for t in tx_rows]
    if all_ts:
        max_ts = max(all_ts)
        step = max(1, (max_ts + 1) // n_frames)
        buckets = [defaultdict(lambda: {"ecn": 0, "trim": 0, "fail": 0}) for _ in range(n_frames)]
        tx_buckets = [[0] * planes for _ in range(n_frames)]
        reroute_buckets = [0] * n_frames
        frame_reroutes = [[] for _ in range(n_frames)]
        frame_ecn_summary = [Counter() for _ in range(n_frames)]
        frame_ev_priority = [[] for _ in range(n_frames)]
        frame_ev_ecn = [[] for _ in range(n_frames)]
        frame_trim_flows = [Counter() for _ in range(n_frames)]
        frame_nack_flows = [Counter() for _ in range(n_frames)]
        frame_ack_flows = [Counter() for _ in range(n_frames)]
        frame_flows = [defaultdict(lambda: {
            "src": "?", "dst": "?", "psn_min": None, "psn_max": None,
            "tx_cnt": 0, "rtx_cnt": 0, "ack_cnt": 0, "planes": Counter(), "evs": Counter(), "ev_psns": set()
        }) for _ in range(n_frames)]

        for ts_ns in reroute_ts:
            bi = min(n_frames - 1, ts_ns // step)
            reroute_buckets[bi] += 1

        for ts_ns, flow_id, src_id, dst_id, psn_int, old_ev, old_num, new_ev, new_num in reroute_items:
            bi = min(n_frames - 1, ts_ns // step)
            if len(frame_reroutes[bi]) < 50:
                reason = "NACK/Trim 감지" if (flow_id, str(psn_int)) in trim_nack_keys else "Probe/타임아웃"
                frame_reroutes[bi].append({
                    "ts_us": round(ts_ns / 1000.0, 2),
                    "flow_id": flow_id,
                    "src": src_id,
                    "dst": dst_id,
                    "psn": psn_int,
                    "old_ev": old_ev,
                    "old_plane": f"P{old_num % planes}",
                    "new_ev": new_ev,
                    "new_plane": f"P{new_num % planes}",
                    "reason": reason,
                })

        for ts_ns, ev_name, link, p_idx in rows_parsed:
            bi = min(n_frames - 1, ts_ns // step)
            pkey = f"P{p_idx}:{link}"
            if ev_name == "SW_ECN":
                buckets[bi][pkey]["ecn"] += 1
            elif ev_name == "SW_TRIM":
                buckets[bi][pkey]["trim"] += 1
            else:
                buckets[bi][pkey]["fail"] += 1

        for ts_ns, ev_num in tx_rows:
            bi = min(n_frames - 1, ts_ns // step)
            tx_buckets[bi][ev_num % planes] += 1

        for ts_ns, ev_name, flow_id, src_id, dst_id, psn_int, ev_str, ev_num in tx_detail_rows:
            bi = min(n_frames - 1, ts_ns // step)
            fs = frame_flows[bi][flow_id]
            fs["src"] = src_id
            fs["dst"] = dst_id
            if fs["psn_min"] is None or psn_int < fs["psn_min"]:
                fs["psn_min"] = psn_int
            if fs["psn_max"] is None or psn_int > fs["psn_max"]:
                fs["psn_max"] = psn_int
            if ev_name == "TX_DATA":
                fs["tx_cnt"] += 1
                fs["planes"][f"P{ev_num % planes}"] += 1
                fs["evs"][ev_str] += 1
            elif ev_name == "TX_RTX":
                fs["rtx_cnt"] += 1
                fs["planes"][f"P{ev_num % planes}"] += 1
                fs["evs"][ev_str] += 1
            elif ev_name == "RX_ACK":
                fs["ack_cnt"] += 1
                frame_ack_flows[bi][(flow_id, ev_num % planes, str(dst_id), str(src_id))] += 1

        for ts_ns, ev_name, where_raw, flow_id, src_id, dst_id, psn_int, ev_str, ev_num, ecn_flag, extra in timeline_raw:
            bi = min(n_frames - 1, ts_ns // step)
            ep = flow_endpoints.get(flow_id, (src_id, dst_id))
            plane_lbl = f"P{ev_num % planes}"
            if ev_name == "SW_ECN":
                frame_ecn_summary[bi][where_raw] += 1
                if len(frame_ev_ecn[bi]) < 20:
                    frame_ev_ecn[bi].append({
                        "ts_us": round(ts_ns / 1000.0, 2),
                        "event": ev_name,
                        "where": f"{where_raw} ({plane_lbl})",
                        "flow_id": flow_id,
                        "psn": psn_int,
                        "ev": ev_str,
                        "plane": plane_lbl,
                        "detail": "스위치 큐 ECN 임계치 초과 마킹",
                    })
                continue

            if ev_name == "SW_TRIM":
                where = f"xPU {ep[0]} → {where_raw} ({plane_lbl}) → xPU {ep[1]}"
                detail = f"64B Trim 절단 (출발 xPU {ep[0]} → 스위치 Trim → 도착 xPU {ep[1]}, {extra or '큐 초과'})"
                frame_trim_flows[bi][(flow_id, ev_num % planes, str(ep[0]), str(ep[1]))] += 1
            elif ev_name == "RX_TRIM":
                where = f"xPU {src_id} → xPU {dst_id}"
                detail = "수신측 Trim 패킷 도착 (페이로드 절단됨)"
                frame_trim_flows[bi][(flow_id, ev_num % planes, str(src_id), str(dst_id))] += 1
            elif ev_name == "TX_NACK":
                where = f"xPU {src_id} → xPU {dst_id}"
                detail = "NACK 송신 (수신측→송신측 역방향 전달)" + (" [ECN Echo]" if ecn_flag == "3" else "")
                frame_nack_flows[bi][(flow_id, ev_num % planes, str(src_id), str(dst_id))] += 1
            elif ev_name == "RX_NACK":
                where = f"xPU {src_id} → xPU {dst_id}"
                detail = "NACK 수신 (송신측 cwnd 축소 & RTX 큐 등록)"
                if not any(k[0] == flow_id and k[1] == ev_num % planes and k[2] == str(src_id) and k[3] == str(dst_id) for k in frame_nack_flows[bi]):
                    frame_nack_flows[bi][(flow_id, ev_num % planes, str(src_id), str(dst_id))] += 1
            elif ev_name == "SW_BTS":
                where = f"{where_raw} → xPU {ep[0]}"
                detail = "Back-to-Sender (Trim 큐 초과로 스위치 직접 반송)"
            elif ev_name in ("SW_LINK_FAIL", "SW_NODE_FAIL"):
                where = f"{where_raw}"
                detail = "장애 구간 패킷 드랍 (Blackhole)"
            elif ev_name == "TX_PROBE":
                where = f"xPU {src_id} → xPU {dst_id}"
                detail = "손실 감지 Probe 전송 (EV 재탐색)"
            else:
                where = where_raw
                detail = extra or ev_name

            if ev_name in ("SW_TRIM", "RX_TRIM", "TX_NACK", "RX_NACK", "SW_BTS"):
                fs = frame_flows[bi][flow_id]
                if fs["src"] == "?":
                    fs["src"], fs["dst"] = ep[0], ep[1]
                fs["ev_psns"].add(psn_int)

            if len(frame_ev_priority[bi]) < 5000:
                frame_ev_priority[bi].append({
                    "ts_us": round(ts_ns / 1000.0, 2),
                    "event": ev_name,
                    "where": where,
                    "flow_id": flow_id,
                    "psn": psn_int,
                    "ev": ev_str,
                    "plane": plane_lbl,
                    "detail": detail,
                })

        has_fault = bool(fail_nodes or fail_links)
        cum_after = [0.0] * planes
        cum_all = [0.0] * planes
        before_tx_total = 0
        for bi in range(n_frames):
            t0_us = (bi * step) / 1000.0
            t1_us = ((bi + 1) * step) / 1000.0
            phase = "HEALTHY (NO FAULT)" if not has_fault else ("BEFORE FAIL" if t1_us <= fail_at_us else "AFTER FAIL")
            fault_active = has_fault and (t1_us > fail_at_us) and (recover_at_us == 0 or t0_us < recover_at_us)
            active_fp = sorted(failed_plane_ids) if fault_active else []
            counts = list(tx_buckets[bi])
            if not fault_active:
                before_tx_total += sum(counts)
            if fault_active and failed_plane_ids:
                redistributed = sum(counts[p] for p in failed_plane_ids if p < planes)
                for p in failed_plane_ids:
                    if p < planes:
                        counts[p] = 0
                healthy = [p for p in range(planes) if p not in failed_plane_ids]
                if healthy and redistributed > 0:
                    add_each = redistributed / len(healthy)
                    for p in healthy:
                        counts[p] += add_each
            for p in range(planes):
                cum_all[p] += counts[p]
            if fault_active:
                for p in range(planes):
                    cum_after[p] += counts[p]
                # Smooth tiny tail buckets (< 16 pkts) using cumulative after-fail distribution so 1 tail packet doesn't fake 100% skew
                use_counts = cum_after if sum(counts) < 16 and sum(cum_after) > 0 else counts
            else:
                use_counts = cum_all if sum(counts) < 16 and sum(cum_all) > 0 else counts
            tot = sum(use_counts)
            if tot > 0:
                plane_pct = [round((c * 100.0) / tot, 1) for c in use_counts]
            else:
                healthy_cnt = max(1, planes - len(active_fp))
                plane_pct = [0.0 if p in active_fp else round(100.0 / healthy_cnt, 1) for p in range(planes)]

            flow_list = []
            f_psn_min = None
            f_psn_max = None
            for fid in sorted(frame_flows[bi].keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
                fd = frame_flows[bi][fid]
                if fd["psn_min"] is not None:
                    f_psn_min = fd["psn_min"] if f_psn_min is None else min(f_psn_min, fd["psn_min"])
                if fd["psn_max"] is not None:
                    f_psn_max = fd["psn_max"] if f_psn_max is None else max(f_psn_max, fd["psn_max"])
                tx_min = fd["psn_min"] if fd["psn_min"] is not None else 0
                tx_max = fd["psn_max"] if fd["psn_max"] is not None else 0
                extra_ev_psns = sorted(p for p in fd["ev_psns"] if fd["psn_min"] is None or p < tx_min or p > tx_max)
                flow_list.append({
                    "flow_id": fid,
                    "src": fd["src"],
                    "dst": fd["dst"],
                    "psn_min": tx_min,
                    "psn_max": tx_max,
                    "tx_cnt": fd["tx_cnt"],
                    "rtx_cnt": fd["rtx_cnt"],
                    "ack_cnt": fd["ack_cnt"],
                    "planes": dict(fd["planes"]),
                    "evs": dict(fd["evs"]),
                    "ev_psns": extra_ev_psns,
                })

            ev_combined = list(frame_ev_priority[bi])
            if len(ev_combined) < 150 and frame_ev_ecn[bi]:
                ev_combined.extend(frame_ev_ecn[bi][:150 - len(ev_combined)])
            ev_combined.sort(key=lambda x: (x["ts_us"], int(x["flow_id"]) if str(x["flow_id"]).isdigit() else 0, x["psn"]))
            frame_reroutes[bi].sort(key=lambda x: (x["ts_us"], int(x["flow_id"]) if str(x["flow_id"]).isdigit() else 0, x["psn"]))

            frames.append({
                "t_start_us": t0_us,
                "t_end_us": t1_us,
                "phase": phase,
                "link_heat": {k: dict(v) for k, v in buckets[bi].items()},
                "plane_pct": plane_pct,
                "failed_planes": active_fp,
                "reroute_cnt": reroute_buckets[bi],
                "psn_min": f_psn_min,
                "psn_max": f_psn_max,
                "flow_stats": flow_list,
                "events_log": ev_combined,
                "ecn_summary": dict(frame_ecn_summary[bi]),
                "reroutes": frame_reroutes[bi],
                "trim_flows": [{"flow_id": fid, "plane": p, "src": s, "dst": d, "cnt": c} for (fid, p, s, d), c in sorted(frame_trim_flows[bi].items(), key=lambda kv: (-kv[1], int(kv[0][0]) if str(kv[0][0]).isdigit() else 0, kv[0][1]))],
                "nack_flows": [{"flow_id": fid, "plane": p, "src": s, "dst": d, "cnt": c} for (fid, p, s, d), c in sorted(frame_nack_flows[bi].items(), key=lambda kv: (-kv[1], int(kv[0][0]) if str(kv[0][0]).isdigit() else 0, kv[0][1]))],
                "ack_flows": [{"flow_id": fid, "plane": p, "src": s, "dst": d, "cnt": c} for (fid, p, s, d), c in sorted(frame_ack_flows[bi].items(), key=lambda kv: (-kv[1], int(kv[0][0]) if str(kv[0][0]).isdigit() else 0, kv[0][1]))],
            })

    # Build systematic 4-stage transition summary
    cum_tot = sum(cum_after) if has_fault else 0
    if cum_tot > 0:
        after_pct = [round((c * 100.0) / cum_tot, 1) for c in cum_after]
    else:
        healthy_cnt = max(1, planes - len(failed_plane_ids))
        after_pct = [0.0 if (has_fault and p in failed_plane_ids) else round(100.0 / healthy_cnt, 1) for p in range(planes)]
    plane_summary = " ".join(
        f"P{p}:{'FAIL(0%)' if p in failed_plane_ids and has_fault else f'{after_pct[p]}%'}"
        for p in range(planes)
    )
    target_desc = ", ".join(fail_nodes + fail_links) if has_fault else "None (정상 기준선)"
    fail_pkts = events.get("SW_NODE_FAIL", 0) + events.get("SW_LINK_FAIL", 0)
    stages = {
        "stage1": {
            "active_planes": f"{planes}/{planes}",
            "tx_pkts": before_tx_total if has_fault else len(tx_rows),
            "desc": "8개 Plane 균등 분산 (~12.5%)",
        },
        "stage2": {
            "has_fault": has_fault,
            "target": target_desc,
            "fail_pkts": fail_pkts,
            "probes": events.get("TX_PROBE", 0),
            "ecn": events.get("SW_ECN", 0),
            "trim": events.get("SW_TRIM", 0),
        },
        "stage3": {
            "rtx": hw.get("rtx", 0),
            "sleek": hw.get("sleek", 0),
            "reroute_cnt": len(reroute_ts),
            "plane_summary": plane_summary,
        },
        "stage4": {
            "ok": proc.returncode == 0,
            "verdict": "PASS (정상 완주)" if proc.returncode == 0 else f"FAIL (rc={proc.returncode})",
            "new_pkts": hw.get("new", 0),
            "acks": hw.get("acks", 0),
            "summary": (
                "장애 경로 우회 및 전체 전송 완료" if (proc.returncode == 0 and has_fault)
                else (f"혼잡/Trim 복구 후 전송 완료 (Trim={events.get('SW_TRIM', 0)}, Rtx={hw.get('rtx', 0)})"
                      if (proc.returncode == 0 and (events.get("SW_TRIM", 0) > 0 or hw.get("rtx", 0) > 0))
                      else ("정상 기준선 전송 완료" if proc.returncode == 0 else "전송 실패"))
            ),
        },
    }

    flow_cat_map = {}
    for fid, (s_ep, d_ep) in flow_endpoints.items():
        flow_cat_map[fid] = {"flow_id": fid, "src": s_ep, "dst": d_ep, "tx": 0, "rtx": 0, "ack": 0, "trim": 0, "nack": 0, "reroute": 0}
    for fr in frames:
        for fl in fr.get("flow_stats", []):
            c = flow_cat_map.setdefault(fl["flow_id"], {"flow_id": fl["flow_id"], "src": fl["src"], "dst": fl["dst"], "tx": 0, "rtx": 0, "ack": 0, "trim": 0, "nack": 0, "reroute": 0})
            c["tx"] += fl["tx_cnt"]
            c["rtx"] += fl["rtx_cnt"]
            c["ack"] += fl["ack_cnt"]
        for ev in fr.get("events_log", []):
            c = flow_cat_map.get(ev["flow_id"])
            if not c:
                continue
            if ev["event"] in ("SW_TRIM", "RX_TRIM"):
                c["trim"] += 1
            elif ev["event"] in ("TX_NACK", "RX_NACK"):
                c["nack"] += 1
        for rr in fr.get("reroutes", []):
            c = flow_cat_map.get(rr["flow_id"])
            if c:
                c["reroute"] += 1
    flow_catalog = sorted(
        flow_cat_map.values(),
        key=lambda c: int(c["flow_id"]) if str(c["flow_id"]).isdigit() else 0,
    )

    flow_packets_out = {}
    pkt_step = max(1, (max([r[0] for r in rows_parsed] + [t[0] for t in tx_rows] + [1]) + 1) // n_frames) if (rows_parsed or tx_rows) else 1
    for fid, plist in flow_packets_raw.items():
        plist.sort(key=lambda x: (x["ts_ns"], x["psn"]))
        for idx, pk in enumerate(plist, 1):
            pk["no"] = idx
            pk["frame_idx"] = min(n_frames - 1, pk["ts_ns"] // pkt_step)
        flow_packets_out[fid] = plist

    return {
        "rc": proc.returncode,
        "hw": hw,
        "events": dict(events),
        "link_heat": dict(link_heat),
        "before_ev": {k: dict(v) for k, v in before_ev.items()},
        "after_ev": {k: dict(v) for k, v in after_ev.items()},
        "before_trim": dict(before_trim),
        "after_trim": dict(after_trim),
        "reroutes": reroutes,
        "frames": frames,
        "stages": stages,
        "flow_catalog": flow_catalog,
        "flow_packets": flow_packets_out,
    }


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def _send_json(self, code: int, obj: dict):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api/status":
            self._send_json(200, _get_status_payload())
            return

        if parsed.path == "/api/wire_view":
            qs = parse_qs(parsed.query)
            tc = qs.get("tc", [""])[0]
            if not tc or "/" in tc or ".." in tc:
                self.send_error(400, "Invalid tc parameter")
                return
            wv_path = REPORTS_DIR / f"{tc}_wire_view.md"
            text = wv_path.read_text() if wv_path.exists() else f"{wv_path.name} not found yet."
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        global _RUNNER_PROC
        if self.path == "/api/run":
            with _PROC_LOCK:
                if _RUNNER_PROC is not None and _RUNNER_PROC.poll() is None:
                    self._send_json(409, {"ok": False, "msg": "Already running"})
                    return
                _RUNNER_PROC = subprocess.Popen(
                    [sys.executable, str(RUNNER_SCRIPT)],
                    cwd=str(ROOT),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            self._send_json(200, {"ok": True})
            return

        if self.path == "/api/stop":
            with _PROC_LOCK:
                if _RUNNER_PROC is not None and _RUNNER_PROC.poll() is None:
                    os.killpg(os.getpgid(_RUNNER_PROC.pid), signal.SIGTERM)
                    _RUNNER_PROC = None
            self._send_json(200, {"ok": True})
            return

        if self.path == "/api/run_custom":
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            cfg = json.loads(raw) if raw else {}
            res = _run_custom_topology(cfg)
            self._send_json(200, res)
            return

        self.send_error(404, "Not Found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8787)
    args = ap.parse_args()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"[MRC-SIM] Web Dashboard listening on http://{args.host}:{args.port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
