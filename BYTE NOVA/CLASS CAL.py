# =========================================
# CLASS MARK CALCULATOR
# CSV Upload + Data Visualisation + AI Chat
# No pip installs needed
# Run: python class_mark_calculator.py
# =========================================

import http.server
import json
import csv
import io
import threading
import webbrowser
from urllib.parse import urlparse

# =========================================
# CORE CALCULATION LOGIC
# =========================================

def calculate_stats(students):
    if not students:
        return {}

    marks = [s["mark"] for s in students]
    average = sum(marks) / len(marks)
    sorted_students = sorted(students, key=lambda s: s["mark"], reverse=True)

    distinctions = [s for s in students if s["mark"] >= 75]
    passes = [s for s in students if 50 <= s["mark"] < 75]
    fails = [s for s in students if s["mark"] < 50]

    if average >= 75:
        prediction = "Excellent performance expected."
    elif average >= 50:
        prediction = "Likely to pass with consistent effort."
    else:
        prediction = "Additional support may be required."

    # Mark distribution buckets
    buckets = {"0-29": 0, "30-49": 0, "50-59": 0, "60-69": 0, "70-74": 0, "75-84": 0, "85-100": 0}
    for m in marks:
        if m < 30: buckets["0-29"] += 1
        elif m < 50: buckets["30-49"] += 1
        elif m < 60: buckets["50-59"] += 1
        elif m < 70: buckets["60-69"] += 1
        elif m < 75: buckets["70-74"] += 1
        elif m < 85: buckets["75-84"] += 1
        else: buckets["85-100"] += 1

    even_odd = [
        {**s, "parity": "Even" if s["mark"] % 2 == 0 else "Odd"}
        for s in students
    ]

    return {
        "average": round(average, 2),
        "minimum": min(marks),
        "maximum": max(marks),
        "groups": len(students) // 5,
        "prediction": prediction,
        "distinctions": distinctions,
        "passes": passes,
        "fails": fails,
        "top_10": sorted_students[:10],
        "even_odd": even_odd,
        "buckets": buckets,
        "total": len(students),
    }


# =========================================
# CSV PARSING (no pip needed)
# =========================================

def parse_csv(text):
    """
    Accepts CSV text. Tries to find a name column and a mark column.
    Very flexible — handles headers like Name/Student/Learner and
    Mark/Score/Marks/Percentage/Result.
    Also handles a plain 2-column CSV with no header.
    """
    students = []
    reader = csv.reader(io.StringIO(text.strip()))
    rows = list(reader)
    if not rows:
        return []

    # Detect header row
    name_col = mark_col = None
    first = [c.strip().lower() for c in rows[0]]

    name_keywords = ["name", "student", "learner", "pupil", "firstname", "surname", "fullname"]
    mark_keywords = ["mark", "marks", "score", "scores", "percent", "percentage", "result", "grade", "total"]

    for i, cell in enumerate(first):
        if any(k in cell for k in name_keywords):
            name_col = i
        if any(k in cell for k in mark_keywords):
            mark_col = i

    data_rows = rows[1:] if (name_col is not None or mark_col is not None) else rows

    # If still no column found, assume col 0 = name, col 1 = mark
    if name_col is None: name_col = 0
    if mark_col is None: mark_col = 1

    seen = set()
    for row in data_rows:
        if len(row) <= max(name_col, mark_col):
            continue
        name = row[name_col].strip()
        raw_mark = row[mark_col].strip().replace("%", "").replace(",", ".")
        if not name or not raw_mark:
            continue
        try:
            mark = float(raw_mark)
        except ValueError:
            continue
        if not (0 <= mark <= 100):
            continue
        if name.lower() in ("name", "student", "learner"):
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        students.append({"name": name, "mark": mark})

    return students


# =========================================
# HTML UI
# =========================================

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ClassMark</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Space+Mono:wght@700&display=swap" rel="stylesheet"/>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #0a0a0f;
  --surface: #13131a;
  --card: #1a1a24;
  --border: #2a2a3a;
  --text: #f0ede4;
  --muted: #7a7a9a;
  --fail: #f87171;
  --pass: #f5a623;
  --dist: #4ade80;
  --purple: #a78bfa;
  --purple-dim: rgba(167,139,250,.13);
  --fail-dim: rgba(248,113,113,.13);
  --pass-dim: rgba(245,166,35,.13);
  --dist-dim: rgba(74,222,128,.13);
}
body { background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; min-height:100vh; padding-bottom:80px; }

/* ── header ── */
.header { border-bottom:1px solid var(--border); padding:16px 32px; display:flex; align-items:center; justify-content:space-between; }
.logo { width:34px; height:34px; border-radius:9px; background:var(--purple); display:flex; align-items:center; justify-content:center; font-size:17px; margin-right:12px; flex-shrink:0; }
.brand { font-size:15px; font-weight:700; letter-spacing:-.01em; }
.brand-sub { font-size:10px; color:var(--muted); font-family:'DM Mono',monospace; letter-spacing:.08em; text-transform:uppercase; }
.btn-ghost { background:transparent; border:1px solid var(--border); border-radius:8px; color:var(--muted); padding:7px 16px; font-size:13px; font-family:'DM Mono',monospace; cursor:pointer; }
.btn-ghost:hover { border-color:var(--purple); color:var(--purple); }

/* ── layout ── */
.main { max-width:820px; margin:0 auto; padding:32px 24px; }
.card { background:var(--card); border:1px solid var(--border); border-radius:16px; padding:24px; margin-bottom:22px; }
.card-title { font-size:12px; font-weight:600; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; font-family:'DM Mono',monospace; margin-bottom:18px; }

/* ── inputs ── */
input[type=text],input[type=number],input[type=password],textarea {
  background:var(--surface); border:1px solid var(--border); border-radius:8px;
  padding:10px 14px; color:var(--text); font-family:'DM Mono',monospace;
  font-size:14px; outline:none; transition:border-color .2s; width:100%;
}
input:focus,textarea:focus { border-color:var(--purple); }
input::placeholder,textarea::placeholder { color:var(--muted); }
label { font-size:11px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); font-family:'DM Mono',monospace; display:block; margin-bottom:6px; }
button { cursor:pointer; transition:opacity .15s,transform .1s; font-family:'DM Sans',sans-serif; }
button:hover { opacity:.88; } button:active { transform:scale(.97); }

/* ── tabs ── */
.tabs { display:flex; gap:8px; margin-bottom:22px; }
.tab { flex:1; padding:11px; border-radius:10px; border:1px solid var(--border); background:transparent; color:var(--muted); font-size:13px; font-weight:600; transition:all .2s; }
.tab.active { background:var(--purple-dim); border-color:rgba(167,139,250,.4); color:var(--purple); }

/* ── CSV drop zone ── */
.drop-zone { border:2px dashed var(--border); border-radius:12px; padding:40px 24px; text-align:center; transition:all .2s; cursor:pointer; position:relative; }
.drop-zone:hover,.drop-zone.over { border-color:var(--purple); background:var(--purple-dim); }
.drop-zone input[type=file] { position:absolute; inset:0; opacity:0; cursor:pointer; width:100%; height:100%; }
.drop-icon { font-size:36px; margin-bottom:10px; }
.drop-title { font-size:16px; font-weight:600; margin-bottom:4px; }
.drop-sub { font-size:12px; color:var(--muted); font-family:'DM Mono',monospace; }
.file-pill { display:flex; align-items:center; gap:10px; background:var(--purple-dim); border:1px solid rgba(167,139,250,.3); border-radius:10px; padding:10px 14px; margin-top:12px; }
.file-pill-name { flex:1; font-size:13px; font-family:'DM Mono',monospace; color:var(--purple); }
.btn-x { background:transparent; border:none; color:var(--muted); font-size:18px; line-height:1; }
.btn-x:hover { color:var(--fail); }

/* status */
.status { display:flex; align-items:center; gap:10px; padding:11px 14px; border-radius:10px; font-size:13px; font-family:'DM Mono',monospace; margin-top:12px; }
.status.ok { background:var(--dist-dim); border:1px solid rgba(74,222,128,.25); color:var(--dist); }
.status.err { background:var(--fail-dim); border:1px solid rgba(248,113,113,.25); color:var(--fail); }
.status.info { background:var(--purple-dim); border:1px solid rgba(167,139,250,.25); color:var(--purple); }

/* ── manual form ── */
.form-grid { display:grid; grid-template-columns:1fr 150px; gap:14px; margin-bottom:14px; }
.btn-add { background:var(--purple); color:#fff; border:none; border-radius:8px; padding:10px 20px; font-weight:700; font-size:14px; }
.btn-gen { width:100%; background:var(--dist); color:#0a0a0f; border:none; border-radius:12px; padding:14px; font-weight:700; font-size:16px; }
.empty-msg { text-align:center; padding:44px 0; color:var(--muted); font-family:'DM Mono',monospace; font-size:13px; }

/* student rows */
.s-row { display:flex; align-items:center; gap:10px; padding:9px 12px; background:var(--surface); border-radius:9px; border:1px solid var(--border); margin-bottom:7px; }
.s-num { font-size:11px; color:var(--muted); font-family:'DM Mono',monospace; min-width:22px; }
.s-name { flex:1; font-size:14px; font-weight:500; }
.bar-wrap { flex:1; height:5px; background:var(--border); border-radius:99px; overflow:hidden; min-width:50px; }
.bar { height:100%; border-radius:99px; transition:width .4s; }
.s-mark { font-size:13px; font-family:'DM Mono',monospace; font-weight:700; min-width:44px; text-align:right; }
.s-grade { font-size:11px; min-width:66px; text-align:right; font-family:'DM Mono',monospace; }
.btn-del { background:transparent; border:none; color:var(--muted); font-size:17px; }
.btn-del:hover { color:var(--fail); }

.legend { display:flex; gap:14px; flex-wrap:wrap; margin-top:12px; font-size:11px; font-family:'DM Mono',monospace; color:var(--muted); }
.legend span { display:inline-flex; align-items:center; gap:5px; }
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; }

/* ── report stats ── */
.stats-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:12px; margin-bottom:22px; }
.stat-card { background:var(--card); border-radius:12px; padding:16px 20px; }
.stat-label { font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); font-family:'DM Mono',monospace; margin-bottom:4px; }
.stat-value { font-size:26px; font-weight:700; font-family:'Space Mono',monospace; }

.pred-box { background:var(--purple-dim); border:1px solid rgba(167,139,250,.33); border-radius:12px; padding:16px 20px; margin-bottom:22px; display:flex; align-items:center; gap:12px; }
.pred-label { font-size:10px; color:var(--purple); font-family:'DM Mono',monospace; letter-spacing:.1em; text-transform:uppercase; margin-bottom:3px; }
.pred-text { font-size:15px; font-weight:600; }

/* ── data visualisation ── */
.viz-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:22px; }
.viz-card { background:var(--card); border:1px solid var(--border); border-radius:14px; padding:20px; }
.viz-title { font-size:11px; font-weight:600; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; font-family:'DM Mono',monospace; margin-bottom:16px; }

/* donut */
.donut-wrap { display:flex; flex-direction:column; align-items:center; gap:14px; }
.donut-svg { overflow:visible; }
.donut-legend { display:flex; flex-direction:column; gap:6px; width:100%; }
.donut-item { display:flex; align-items:center; gap:8px; font-size:12px; font-family:'DM Mono',monospace; }
.donut-swatch { width:10px; height:10px; border-radius:3px; flex-shrink:0; }
.donut-label { flex:1; color:var(--muted); }
.donut-count { font-weight:700; }
.donut-pct { color:var(--muted); font-size:11px; }

/* bar chart */
.bar-chart { display:flex; flex-direction:column; gap:9px; }
.bc-row { display:flex; align-items:center; gap:8px; }
.bc-label { font-size:11px; font-family:'DM Mono',monospace; color:var(--muted); min-width:52px; text-align:right; }
.bc-track { flex:1; height:18px; background:var(--surface); border-radius:5px; overflow:hidden; }
.bc-fill { height:100%; border-radius:5px; transition:width .6s ease; display:flex; align-items:center; padding-left:6px; }
.bc-num { font-size:11px; font-family:'DM Mono',monospace; color:#0a0a0f; font-weight:700; }

/* grade breakdown summary cards */
.grade-cards { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:22px; }
.grade-card { border-radius:12px; padding:14px 16px; text-align:center; }
.grade-card .gc-count { font-size:28px; font-weight:700; font-family:'Space Mono',monospace; }
.grade-card .gc-label { font-size:10px; font-family:'DM Mono',monospace; letter-spacing:.1em; text-transform:uppercase; margin-top:2px; }

/* dist / top10 */
.dist-wrap { display:flex; flex-wrap:wrap; gap:8px; }
.dist-badge { background:var(--dist-dim); border:1px solid rgba(74,222,128,.3); border-radius:8px; padding:7px 13px; display:flex; align-items:center; gap:7px; font-size:13px; font-weight:600; }

.pill-even { font-size:11px; font-family:'DM Mono',monospace; padding:3px 9px; border-radius:99px; background:var(--dist-dim); color:var(--dist); border:1px solid rgba(74,222,128,.27); }
.pill-odd { font-size:11px; font-family:'DM Mono',monospace; padding:3px 9px; border-radius:99px; background:var(--purple-dim); color:var(--purple); border:1px solid rgba(167,139,250,.27); }
.eo-mark { font-size:13px; font-family:'DM Mono',monospace; color:var(--muted); margin-right:4px; }

/* ── AI chat ── */
.key-banner { background:var(--purple-dim); border:1px solid rgba(167,139,250,.3); border-radius:12px; padding:16px 18px; margin-bottom:16px; }
.key-row { display:flex; gap:10px; align-items:flex-end; margin-top:10px; }
.key-row input { flex:1; }
.btn-save-key { background:var(--purple); color:#fff; border:none; border-radius:8px; padding:10px 16px; font-weight:700; font-size:13px; white-space:nowrap; }
.key-ok { display:flex; align-items:center; gap:7px; font-size:13px; font-family:'DM Mono',monospace; color:var(--dist); margin-top:8px; }

.chips { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
.chip { background:var(--surface); border:1px solid var(--border); border-radius:99px; padding:6px 13px; font-size:12px; color:var(--muted); font-family:'DM Mono',monospace; }
.chip:hover { border-color:var(--purple); color:var(--purple); }

.chat-box { display:flex; flex-direction:column; gap:10px; max-height:320px; overflow-y:auto; margin-bottom:12px; }
.chat-msg { padding:11px 13px; border-radius:10px; font-size:13px; line-height:1.65; max-width:92%; white-space:pre-wrap; }
.chat-msg.user { background:var(--purple-dim); border:1px solid rgba(167,139,250,.3); align-self:flex-end; }
.chat-msg.ai { background:var(--surface); border:1px solid var(--border); align-self:flex-start; }
.chat-msg.error { background:var(--fail-dim); border:1px solid rgba(248,113,113,.3); color:var(--fail); }
.chat-row { display:flex; gap:10px; }
.chat-row input { flex:1; }
.btn-send { background:var(--purple); color:#fff; border:none; border-radius:8px; padding:0 18px; font-weight:700; }
.btn-send:disabled { opacity:.45; cursor:not-allowed; }

.typing span { width:6px; height:6px; border-radius:50%; background:var(--purple); display:inline-block; animation:bob 1.1s infinite; margin:0 2px; }
.typing span:nth-child(2){animation-delay:.15s} .typing span:nth-child(3){animation-delay:.3s}
@keyframes bob{0%,60%,100%{transform:translateY(0);opacity:.5}30%{transform:translateY(-5px);opacity:1}}

@media(max-width:560px){
  .viz-grid{grid-template-columns:1fr}
  .stats-grid{grid-template-columns:1fr}
  .grade-cards{grid-template-columns:1fr}
  .form-grid{grid-template-columns:1fr}
  .header{padding:12px 16px}
  .main{padding:20px 14px}
  .tabs{flex-direction:column}
}
</style>
</head>
<body>

<div class="header">
  <div style="display:flex;align-items:center">
    <div class="logo">📊</div>
    <div>
      <div class="brand">ClassMark</div>
      <div class="brand-sub">Educational Analytics</div>
    </div>
  </div>
  <button class="btn-ghost" id="btnNew" style="display:none" onclick="newSession()">← New Session</button>
</div>

<div class="main">

  <!-- ═══════════════ INPUT PHASE ═══════════════ -->
  <div id="phaseInput">

    <div class="tabs">
      <button class="tab active" id="tabCSV" onclick="switchTab('csv')">📂 Upload CSV</button>
      <button class="tab" id="tabManual" onclick="switchTab('manual')">✏️ Manual Entry</button>
    </div>

    <!-- CSV TAB -->
    <div id="panelCSV">
      <div class="card">
        <div class="card-title">Upload CSV File</div>
        <p style="font-size:13px;color:var(--muted);font-family:'DM Mono',monospace;margin-bottom:16px;line-height:1.7">
          Your CSV needs at least two columns: one for the student name and one for the mark (0–100).
          Any header names work — e.g. <strong style="color:var(--text)">Name, Mark</strong> or <strong style="color:var(--text)">Student, Score</strong>.
          You can also upload a file with no headers — just name in column 1 and mark in column 2.
        </p>

        <div class="drop-zone" id="dropZone">
          <input type="file" accept=".csv,.txt" id="fileInput" onchange="onFileChosen(event)"/>
          <div class="drop-icon">📂</div>
          <div class="drop-title">Drop your CSV here</div>
          <div class="drop-sub">or click to browse — .csv or .txt</div>
        </div>

        <div id="filePill" style="display:none" class="file-pill">
          <span style="font-size:18px">📄</span>
          <span class="file-pill-name" id="fileName"></span>
          <button class="btn-x" onclick="clearFile()">×</button>
        </div>

        <div id="csvStatus" style="display:none"></div>
      </div>
    </div>

    <!-- MANUAL TAB -->
    <div id="panelManual" style="display:none">
      <div class="card">
        <div class="card-title">Add Student</div>
        <div class="form-grid">
          <div>
            <label>Student Name</label>
            <input id="inName" type="text" placeholder="e.g. Jane Doe" onkeydown="if(event.key==='Enter')addStudent()"/>
            <div style="color:var(--fail);font-size:11px;font-family:'DM Mono',monospace;margin-top:4px" id="errName"></div>
          </div>
          <div>
            <label>Mark (%)</label>
            <input id="inMark" type="number" min="0" max="100" placeholder="0–100" onkeydown="if(event.key==='Enter')addStudent()"/>
            <div style="color:var(--fail);font-size:11px;font-family:'DM Mono',monospace;margin-top:4px" id="errMark"></div>
          </div>
        </div>
        <button class="btn-add" onclick="addStudent()">+ Add Student</button>
      </div>
    </div>

    <!-- Shared student preview list -->
    <div class="card" id="listCard" style="display:none">
      <div class="card-title">Students <span id="listCount" style="color:var(--purple)"></span></div>
      <div id="studentList"></div>
      <div class="legend">
        <span><span class="dot" style="background:var(--fail)"></span>Fail (&lt;50%)</span>
        <span><span class="dot" style="background:var(--pass)"></span>Pass (50–74%)</span>
        <span><span class="dot" style="background:var(--dist)"></span>Distinction (75%+)</span>
      </div>
    </div>

    <button class="btn-gen" id="btnGen" style="display:none" onclick="generateReport()">Generate Report →</button>
    <div class="empty-msg" id="emptyMsg">Upload a CSV or add students manually to get started.</div>

  </div>

  <!-- ═══════════════ REPORT PHASE ═══════════════ -->
  <div id="phaseReport" style="display:none">

    <!-- Summary stats -->
    <div class="stats-grid" id="statsGrid"></div>

    <!-- Prediction -->
    <div class="pred-box" id="predBox"></div>

    <!-- Grade breakdown cards -->
    <div class="grade-cards" id="gradeCards"></div>

    <!-- ── DATA VISUALISATION ── -->
    <div class="viz-grid">

      <!-- Donut chart -->
      <div class="viz-card">
        <div class="viz-title">Grade Breakdown</div>
        <div class="donut-wrap">
          <svg class="donut-svg" id="donutSvg" width="140" height="140" viewBox="0 0 140 140"></svg>
          <div class="donut-legend" id="donutLegend"></div>
        </div>
      </div>

      <!-- Bar chart -->
      <div class="viz-card">
        <div class="viz-title">Mark Distribution</div>
        <div class="bar-chart" id="barChart"></div>
      </div>

    </div>

    <!-- Top 10 -->
    <div class="card" id="top10Card"></div>

    <!-- Distinctions -->
    <div class="card" id="distCard"></div>

    <!-- Even / Odd -->
    <div class="card" id="eoCard"></div>

    <!-- AI Chat -->
    <div class="card">
      <div class="card-title">🤖 AI Insights Chat</div>

      <div class="key-banner" id="keyBanner">
        <div style="font-size:13px;font-weight:700;margin-bottom:3px">🔑 Anthropic API Key <span style="font-weight:400;color:var(--muted);font-size:12px">(optional — for AI chat only)</span></div>
        <div style="font-size:12px;color:var(--muted);font-family:'DM Mono',monospace">Get yours free at console.anthropic.com</div>
        <div class="key-row">
          <input type="password" id="apiKey" placeholder="sk-ant-..."/>
          <button class="btn-save-key" onclick="saveKey()">Save Key</button>
        </div>
        <div class="key-ok" id="keyOk" style="display:none">✓ Key saved — AI chat ready</div>
      </div>

      <div class="chips">
        <button class="chip" onclick="chip('Which students need the most support and why?')">Who needs support?</button>
        <button class="chip" onclick="chip('Summarize this class performance in 3 sentences.')">Summarize class</button>
        <button class="chip" onclick="chip('Give 3 practical tips to raise the class average.')">Tips to improve</button>
        <button class="chip" onclick="chip('What trends or patterns do you notice in these marks?')">Spot trends</button>
      </div>

      <div class="chat-box" id="chatBox"></div>

      <div class="chat-row">
        <input id="chatIn" type="text" placeholder="Ask anything about this class..." onkeydown="if(event.key==='Enter')sendChat()"/>
        <button class="btn-send" id="btnSend" onclick="sendChat()">Send</button>
      </div>
    </div>

  </div>
</div>

<script>
// ══════════════════════════════════════════════
// State
// ══════════════════════════════════════════════
let students = [];
let reportData = null;
let apiKey = '';
let chatHistory = [];
let currentTab = 'csv';

// ══════════════════════════════════════════════
// Tabs
// ══════════════════════════════════════════════
function switchTab(t) {
  currentTab = t;
  document.getElementById('tabCSV').classList.toggle('active', t === 'csv');
  document.getElementById('tabManual').classList.toggle('active', t === 'manual');
  document.getElementById('panelCSV').style.display = t === 'csv' ? 'block' : 'none';
  document.getElementById('panelManual').style.display = t === 'manual' ? 'block' : 'none';
}

// ══════════════════════════════════════════════
// CSV upload
// ══════════════════════════════════════════════
const dz = document.getElementById('dropZone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('over'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('over');
  const f = e.dataTransfer.files[0];
  if (f) readCSVFile(f);
});
function onFileChosen(e) { if (e.target.files[0]) readCSVFile(e.target.files[0]); }

function readCSVFile(f) {
  document.getElementById('fileName').textContent = f.name;
  document.getElementById('filePill').style.display = 'flex';
  setCSVStatus('info', 'Reading ' + f.name + '…');
  const reader = new FileReader();
  reader.onload = async e => {
    const text = e.target.result;
    try {
      const res = await fetch('/parse-csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ csv: text })
      });
      const data = await res.json();
      if (data.error) { setCSVStatus('err', data.error); return; }
      if (!data.students.length) { setCSVStatus('err', 'No students found. Check your CSV has a name column and a mark column.'); return; }
      students = data.students;
      setCSVStatus('ok', 'Found ' + students.length + ' student' + (students.length > 1 ? 's' : '') + ' — ready to generate report!');
      renderList();
    } catch(err) {
      setCSVStatus('err', 'Error reading file: ' + err.message);
    }
  };
  reader.readAsText(f);
}

function clearFile() {
  document.getElementById('filePill').style.display = 'none';
  document.getElementById('fileInput').value = '';
  document.getElementById('csvStatus').style.display = 'none';
  students = [];
  renderList();
}

function setCSVStatus(type, msg) {
  const el = document.getElementById('csvStatus');
  el.style.display = 'flex';
  el.className = 'status ' + type;
  const icons = { ok: '✓', err: '✗', info: '…' };
  el.innerHTML = '<span>' + icons[type] + '</span><span>' + esc(msg) + '</span>';
}

// ══════════════════════════════════════════════
// Manual entry
// ══════════════════════════════════════════════
function addStudent() {
  const nEl = document.getElementById('inName');
  const mEl = document.getElementById('inMark');
  let ok = true;
  if (!nEl.value.trim()) { document.getElementById('errName').textContent = 'Name required.'; ok = false; } else document.getElementById('errName').textContent = '';
  const m = parseFloat(mEl.value);
  if (isNaN(m)||m<0||m>100) { document.getElementById('errMark').textContent = 'Enter 0–100.'; ok = false; } else document.getElementById('errMark').textContent = '';
  if (!ok) return;
  students.push({ name: nEl.value.trim(), mark: m });
  nEl.value = ''; mEl.value = ''; nEl.focus();
  renderList();
}
function removeStudent(i) { students.splice(i,1); renderList(); }

// ══════════════════════════════════════════════
// Student list preview
// ══════════════════════════════════════════════
function renderList() {
  const listEl = document.getElementById('studentList');
  const card = document.getElementById('listCard');
  const btn = document.getElementById('btnGen');
  const empty = document.getElementById('emptyMsg');
  const count = document.getElementById('listCount');
  if (!students.length) { card.style.display='none'; btn.style.display='none'; empty.style.display='block'; return; }
  card.style.display='block'; btn.style.display='block'; empty.style.display='none';
  count.textContent = '(' + students.length + ')';
  listEl.innerHTML = students.map((s,i) => {
    const g = gi(s.mark);
    return '<div class="s-row">' +
      '<span class="s-num">#'+(i+1)+'</span>' +
      '<span class="s-name">'+esc(s.name)+'</span>' +
      '<div class="bar-wrap"><div class="bar" style="width:'+s.mark+'%;background:'+bc(s.mark)+'"></div></div>' +
      '<span class="s-mark" style="color:'+g.c+'">'+s.mark+'%</span>' +
      '<span class="s-grade" style="color:'+g.c+'">'+g.l+'</span>' +
      '<button class="btn-del" onclick="removeStudent('+i+')">×</button>' +
    '</div>';
  }).join('');
}

// ══════════════════════════════════════════════
// Generate Report
// ══════════════════════════════════════════════
async function generateReport() {
  const res = await fetch('/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ students })
  });
  reportData = await res.json();
  chatHistory = [];
  renderReport(reportData);
}

function renderReport(d) {
  document.getElementById('phaseInput').style.display = 'none';
  document.getElementById('phaseReport').style.display = 'block';
  document.getElementById('btnNew').style.display = 'block';

  // Stats
  document.getElementById('statsGrid').innerHTML =
    sc('Class Average', d.average + '%', 'rgba(167,139,250,.27)', 'var(--purple)') +
    sc('Highest Mark', d.maximum + '%') +
    sc('Lowest Mark', d.minimum + '%') +
    sc('Groups of 5', d.groups);

  // Prediction
  document.getElementById('predBox').innerHTML =
    '<span style="font-size:22px">🎯</span>' +
    '<div><div class="pred-label">Prediction</div><div class="pred-text">'+esc(d.prediction)+'</div></div>';

  // Grade cards
  document.getElementById('gradeCards').innerHTML =
    gc(d.distinctions.length, 'Distinctions', 'var(--dist-dim)', 'var(--dist)') +
    gc(d.passes.length, 'Passes', 'var(--pass-dim)', 'var(--pass)') +
    gc(d.fails.length, 'Fails', 'var(--fail-dim)', 'var(--fail)');

  // Donut chart
  renderDonut(d);

  // Bar chart
  renderBarChart(d.buckets, d.total);

  // Top 10
  const rows10 = d.top_10.map((s,i) => {
    const g=gi(s.mark); const gold=i===0;
    return '<div class="s-row" style="'+(gold?'background:var(--purple-dim);border-color:rgba(167,139,250,.27)':'')+'">' +
      '<span class="s-num" style="'+(gold?'color:var(--purple);':'')+' font-family:Space Mono,monospace;font-weight:700">#'+(i+1)+'</span>' +
      '<span class="s-name" style="'+(gold?'font-weight:700':'')+'">'+esc(s.name)+'</span>' +
      '<div class="bar-wrap"><div class="bar" style="width:'+s.mark+'%;background:'+bc(s.mark)+'"></div></div>' +
      '<span class="s-mark" style="color:'+g.c+'">'+s.mark+'%</span></div>';
  }).join('');
  document.getElementById('top10Card').innerHTML = '<div class="card-title">Top 10 Performers</div>' + rows10;

  // Distinctions
  const dBadges = d.distinctions.length === 0
    ? '<span style="color:var(--muted);font-size:13px;font-family:DM Mono,monospace">No distinctions found.</span>'
    : '<div class="dist-wrap">' + d.distinctions.map(s =>
        '<div class="dist-badge"><span style="color:var(--dist)">★</span>'+esc(s.name)+
        '<span style="font-size:12px;font-family:DM Mono,monospace;color:var(--dist)">'+s.mark+'%</span></div>'
      ).join('') + '</div>';
  document.getElementById('distCard').innerHTML =
    '<div class="card-title">Distinctions <span style="color:var(--dist)">('+d.distinctions.length+')</span></div>' + dBadges;

  // Even / Odd
  const eoRows = d.even_odd.map(s =>
    '<div class="s-row" style="margin-bottom:5px">' +
    '<span class="s-name" style="font-size:13px">'+esc(s.name)+'</span>' +
    '<span class="eo-mark">'+s.mark+'%</span>' +
    '<span class="'+(s.parity==='Even'?'pill-even':'pill-odd')+'">'+s.parity+'</span></div>'
  ).join('');
  document.getElementById('eoCard').innerHTML = '<div class="card-title">Even / Odd Marks</div>' + eoRows;

  document.getElementById('chatBox').innerHTML = '';
}

// ══════════════════════════════════════════════
// Donut chart (pure SVG, no library)
// ══════════════════════════════════════════════
function renderDonut(d) {
  const total = d.total;
  const slices = [
    { label: 'Distinction', count: d.distinctions.length, color: '#4ade80' },
    { label: 'Pass', count: d.passes.length, color: '#f5a623' },
    { label: 'Fail', count: d.fails.length, color: '#f87171' },
  ].filter(s => s.count > 0);

  const cx=70, cy=70, r=52, inner=34;
  let angle = -Math.PI/2;
  let paths = '';

  slices.forEach(s => {
    const sweep = (s.count / total) * 2 * Math.PI;
    const x1=cx+r*Math.cos(angle), y1=cy+r*Math.sin(angle);
    const x2=cx+r*Math.cos(angle+sweep), y2=cy+r*Math.sin(angle+sweep);
    const ix1=cx+inner*Math.cos(angle), iy1=cy+inner*Math.sin(angle);
    const ix2=cx+inner*Math.cos(angle+sweep), iy2=cy+inner*Math.sin(angle+sweep);
    const large = sweep > Math.PI ? 1 : 0;
    paths += '<path d="M'+ix1+' '+iy1+' L'+x1+' '+y1+' A'+r+' '+r+' 0 '+large+' 1 '+x2+' '+y2+' L'+ix2+' '+iy2+' A'+inner+' '+inner+' 0 '+large+' 0 '+ix1+' '+iy1+' Z" fill="'+s.color+'" opacity=".9"/>';
    angle += sweep;
  });

  // Centre text
  paths += '<text x="70" y="66" text-anchor="middle" font-family="Space Mono,monospace" font-size="18" font-weight="700" fill="#f0ede4">'+total+'</text>';
  paths += '<text x="70" y="80" text-anchor="middle" font-family="DM Mono,monospace" font-size="9" fill="#7a7a9a">STUDENTS</text>';

  document.getElementById('donutSvg').innerHTML = paths;

  document.getElementById('donutLegend').innerHTML = slices.map(s =>
    '<div class="donut-item">' +
    '<span class="donut-swatch" style="background:'+s.color+'"></span>' +
    '<span class="donut-label">'+s.label+'</span>' +
    '<span class="donut-count" style="color:'+s.color+'">'+s.count+'</span>' +
    '<span class="donut-pct">'+(Math.round(s.count/total*1000)/10)+'%</span>' +
    '</div>'
  ).join('');
}

// ══════════════════════════════════════════════
// Bar chart (pure HTML, no library)
// ══════════════════════════════════════════════
function renderBarChart(buckets, total) {
  const keys = Object.keys(buckets);
  const maxVal = Math.max(...Object.values(buckets), 1);
  const colors = { '0-29':'#f87171','30-49':'#fb923c','50-59':'#f5a623','60-69':'#facc15','70-74':'#a3e635','75-84':'#4ade80','85-100':'#34d399' };

  document.getElementById('barChart').innerHTML = keys.map(k => {
    const v = buckets[k];
    const pct = Math.round(v / maxVal * 100);
    return '<div class="bc-row">' +
      '<span class="bc-label">'+k+'</span>' +
      '<div class="bc-track"><div class="bc-fill" style="width:'+pct+'%;background:'+colors[k]+'">' +
      (v > 0 ? '<span class="bc-num">'+v+'</span>' : '') +
      '</div></div></div>';
  }).join('');
}

// ══════════════════════════════════════════════
// AI Chat
// ══════════════════════════════════════════════
function saveKey() {
  const v = document.getElementById('apiKey').value.trim();
  if (!v.startsWith('sk-')) { alert('Key should start with sk-ant-'); return; }
  apiKey = v;
  document.getElementById('keyOk').style.display = 'flex';
  document.getElementById('apiKey').value = '';
}

function chip(q) { document.getElementById('chatIn').value = q; sendChat(); }

function ctx() {
  if (!reportData) return '';
  const d = reportData;
  return 'Class stats — Average:'+d.average+'%, High:'+d.maximum+'%, Low:'+d.minimum+
    '%, Total:'+d.total+', Distinctions:'+d.distinctions.length+', Passes:'+d.passes.length+', Fails:'+d.fails.length+
    '. Students: '+students.map(s=>s.name+':'+s.mark+'%').join('; ')+'.';
}

async function sendChat() {
  const inp = document.getElementById('chatIn');
  const q = inp.value.trim();
  if (!q) return;
  if (!apiKey) { addMsg('error','Save your API key above first.'); return; }
  addMsg('user', q); inp.value = '';
  document.getElementById('btnSend').disabled = true;
  const tid = addTyping();
  try {
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type':'application/json',
        'x-api-key': apiKey,
        'anthropic-version':'2023-06-01',
        'anthropic-dangerous-direct-browser-access':'true'
      },
      body: JSON.stringify({
        model:'claude-opus-4-6', max_tokens:600,
        system:'You are a helpful teaching assistant. Be concise and specific. ' + ctx(),
        messages:[...chatHistory,{role:'user',content:q}]
      })
    });
    rmTyping(tid);
    if (!res.ok) { const e=await res.json(); addMsg('error','API error: '+(e.error?.message||res.status)); }
    else {
      const data = await res.json();
      const reply = data.content[0].text.trim();
      chatHistory.push({role:'user',content:q},{role:'assistant',content:reply});
      addMsg('ai', reply);
    }
  } catch(e) { rmTyping(tid); addMsg('error','Error: '+e.message); }
  document.getElementById('btnSend').disabled = false;
}

function addMsg(type, text) {
  const box = document.getElementById('chatBox');
  const d = document.createElement('div');
  d.className = 'chat-msg ' + type;
  d.textContent = text;
  box.appendChild(d); box.scrollTop = box.scrollHeight;
}
function addTyping() {
  const box = document.getElementById('chatBox');
  const d = document.createElement('div');
  const id = 'ty' + Date.now();
  d.id = id; d.className = 'chat-msg ai typing';
  d.innerHTML = '<span></span><span></span><span></span>';
  box.appendChild(d); box.scrollTop = box.scrollHeight; return id;
}
function rmTyping(id) { const e=document.getElementById(id); if(e) e.remove(); }

// ══════════════════════════════════════════════
// Session reset
// ══════════════════════════════════════════════
function newSession() {
  students=[]; reportData=null; chatHistory=[];
  document.getElementById('phaseInput').style.display = 'block';
  document.getElementById('phaseReport').style.display = 'none';
  document.getElementById('btnNew').style.display = 'none';
  document.getElementById('fileInput').value = '';
  document.getElementById('filePill').style.display = 'none';
  document.getElementById('csvStatus').style.display = 'none';
  renderList();
  switchTab('csv');
}

// ══════════════════════════════════════════════
// Helpers
// ══════════════════════════════════════════════
function gi(m) { if(m>=75) return{l:'Distinction',c:'var(--dist)'}; if(m>=50) return{l:'Pass',c:'var(--pass)'}; return{l:'Fail',c:'var(--fail)'}; }
function bc(m) { if(m>=75) return 'var(--dist)'; if(m>=50) return 'var(--pass)'; return 'var(--fail)'; }
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function sc(label,val,border,color) {
  return '<div class="stat-card" style="border:1px solid '+(border||'var(--border)')+'"><div class="stat-label">'+label+'</div><div class="stat-value" style="color:'+(color||'var(--text)')+'">'+val+'</div></div>';
}
function gc(n, label, bg, color) {
  return '<div class="grade-card" style="background:'+bg+';border:1px solid '+color+'44">' +
    '<div class="gc-count" style="color:'+color+'">'+n+'</div>' +
    '<div class="gc-label" style="color:'+color+'">'+label+'</div></div>';
}
</script>
</body>
</html>"""


# =========================================
# HTTP SERVER
# =========================================

class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length))

        if path == "/calculate":
            self._json(calculate_stats(payload.get("students", [])))

        elif path == "/parse-csv":
            try:
                students = parse_csv(payload.get("csv", ""))
                self._json({"students": students})
            except Exception as e:
                self._json({"error": str(e), "students": []})

        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# =========================================
# ENTRY POINT
# =========================================

if __name__ == "__main__":
    import os

    PORT = 5050
    server = http.server.HTTPServer(("localhost", PORT), Handler)

    print("╔══════════════════════════════════════╗")
    print("║ ClassMark — Educational Analytics ║")
    print(f"║ http://localhost:{PORT} ║")
    print("║ ║")
    print("║ No pip installs needed! ║")
    print("║ Press Ctrl+C to stop ║")
    print("╚══════════════════════════════════════╝")

    threading.Timer(0.9, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
