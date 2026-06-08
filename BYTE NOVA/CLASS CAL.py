# =========================================
# CLASS MARK CALCULATOR SYSTEM
# With built-in web UI (no extra installs)
# Run: python class_mark_calculator.py
# =========================================

import http.server
import json
import threading
import webbrowser
from urllib.parse import parse_qs, urlparse

# =========================================
# CORE CALCULATION LOGIC
# =========================================

def calculate_stats(students):
    if not students:
        return {}

    marks = [s["mark"] for s in students]
    average = sum(marks) / len(marks)
    sorted_students = sorted(students, key=lambda s: s["mark"], reverse=True)
#AI prediction for class
    if average >= 75:
        prediction = "Excellent performance expected."
    elif average >= 50:
        prediction = "Likely to pass with consistent effort."
    else:
        prediction = "Additional support may be required."

    distinctions = [s for s in students if s["mark"] >= 75]
    top_10 = sorted_students[:10]
    groups = len(students) // 5

    even_odd = [
        {**s, "parity": "Even" if s["mark"] % 2 == 0 else "Odd"}
        for s in students
    ]

    return {
        "average": round(average, 2),
        "minimum": min(marks),
        "maximum": max(marks),
        "groups": groups,
        "prediction": prediction,
        "distinctions": distinctions,
        "top_10": top_10,
        "even_odd": even_odd,
        "sorted_students": sorted_students,
    }


# =========================================
# HTML / JS UI  (self-contained, no build)
# =========================================

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ClassMark Calculator</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Space+Mono:wght@700&display=swap" rel="stylesheet"/>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#0a0a0f;--surface:#13131a;--card:#1a1a24;--border:#2a2a3a;
    --accent:#e8c547;--accent-dim:rgba(232,197,71,.13);
    --text:#f0ede4;--muted:#7a7a9a;
    --pass:#4ade80;--fail:#f87171;--dist:#e8c547;
  }
  body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;padding-bottom:60px}
  input{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-family:'DM Mono',monospace;font-size:14px;outline:none;transition:border-color .2s;width:100%}
  input:focus{border-color:var(--accent)}
  input::placeholder{color:var(--muted)}
  button{cursor:pointer;transition:opacity .15s,transform .1s;font-family:'DM Sans',sans-serif}
  button:hover{opacity:.88}
  button:active{transform:scale(.97)}
  label{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-family:'DM Mono',monospace;display:block;margin-bottom:6px}
  .err{color:var(--fail);font-size:11px;font-family:'DM Mono',monospace;margin-top:4px}
  .header{border-bottom:1px solid var(--border);padding:18px 32px;display:flex;align-items:center;justify-content:space-between}
  .logo{width:32px;height:32px;border-radius:8px;background:var(--accent);display:flex;align-items:center;justify-content:center;font-size:16px;margin-right:12px;flex-shrink:0}
  .brand{font-size:15px;font-weight:700;letter-spacing:-.01em}
  .brand-sub{font-size:11px;color:var(--muted);font-family:'DM Mono',monospace;letter-spacing:.06em}
  .btn-outline{background:transparent;border:1px solid var(--border);border-radius:8px;color:var(--muted);padding:7px 16px;font-size:13px;font-family:'DM Mono',monospace}
  .main{max-width:760px;margin:0 auto;padding:32px 24px}
  .card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:24px;margin-bottom:24px}
  .card-title{font-size:13px;font-weight:600;color:var(--muted);letter-spacing:.05em;text-transform:uppercase;font-family:'DM Mono',monospace;margin-bottom:18px}
  .form-grid{display:grid;grid-template-columns:1fr 160px;gap:14px;margin-bottom:16px}
  .btn-add{background:var(--accent);color:#0a0a0f;border:none;border-radius:8px;padding:10px 22px;font-weight:700;font-size:14px}
  .student-row{display:flex;align-items:center;gap:12px;padding:10px 14px;background:var(--surface);border-radius:10px;border:1px solid var(--border);margin-bottom:8px}
  .student-num{font-size:11px;color:var(--muted);font-family:'DM Mono',monospace;min-width:24px}
  .student-name{flex:1;font-size:14px;font-weight:500}
  .mark-bar-wrap{flex:1;height:6px;background:var(--border);border-radius:99px;overflow:hidden;min-width:60px}
  .mark-bar{height:100%;border-radius:99px;transition:width .4s ease}
  .student-mark{font-size:14px;font-family:'DM Mono',monospace;font-weight:700;min-width:48px;text-align:right}
  .student-grade{font-size:11px;min-width:70px;text-align:right;font-family:'DM Mono',monospace}
  .btn-remove{background:transparent;border:none;color:var(--muted);font-size:18px;padding:0 4px;line-height:1}
  .btn-remove:hover{color:var(--fail)}
  .btn-generate{width:100%;background:var(--accent);color:#0a0a0f;border:none;border-radius:12px;padding:15px;font-weight:700;font-size:16px;letter-spacing:-.01em}
  .empty{text-align:center;padding:48px 0;color:var(--muted);font-family:'DM Mono',monospace;font-size:13px}
  .stats-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:24px}
  .stat-card{background:var(--card);border-radius:12px;padding:16px 20px}
  .stat-label{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-family:'DM Mono',monospace;margin-bottom:4px}
  .stat-value{font-size:24px;font-weight:700;font-family:'Space Mono',monospace}
  .prediction{background:var(--accent-dim);border:1px solid rgba(232,197,71,.33);border-radius:12px;padding:16px 20px;margin-bottom:24px;display:flex;align-items:center;gap:12px}
  .pred-label{font-size:11px;color:var(--accent);font-family:'DM Mono',monospace;letter-spacing:.1em;text-transform:uppercase;margin-bottom:2px}
  .pred-text{font-size:15px;font-weight:600}
  .dist-wrap{display:flex;flex-wrap:wrap;gap:8px}
  .dist-badge{background:var(--accent-dim);border:1px solid rgba(232,197,71,.33);border-radius:8px;padding:8px 14px;display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600}
  .pill-even{font-size:11px;font-family:'DM Mono',monospace;padding:3px 10px;border-radius:99px;background:rgba(74,222,128,.13);color:var(--pass);border:1px solid rgba(74,222,128,.27)}
  .pill-odd{font-size:11px;font-family:'DM Mono',monospace;padding:3px 10px;border-radius:99px;background:rgba(167,139,250,.13);color:#a78bfa;border:1px solid rgba(167,139,250,.27)}
  .eo-mark{font-size:13px;font-family:'DM Mono',monospace;color:var(--muted)}
  @media(max-width:520px){
    .form-grid{grid-template-columns:1fr}
    .stats-grid{grid-template-columns:1fr}
    .header{padding:14px 16px}
    .main{padding:20px 14px}
  }
</style>
</head>
<body>

<div class="header">
  <div style="display:flex;align-items:center">
    <div class="logo">📊</div>
    <div>
      <div class="brand">ClassMark</div>
      <div class="brand-sub">PERFORMANCE CALCULATOR</div>
    </div>
  </div>
  <button class="btn-outline" id="btnNewSession" style="display:none" onclick="newSession()">← New Session</button>
</div>

<div class="main">

  <!-- INPUT PHASE -->
  <div id="phaseInput">
    <div class="card">
      <div class="card-title">Add Student</div>
      <div class="form-grid">
        <div>
          <label>Student Name</label>
          <input id="inputName" type="text" placeholder="e.g. Jane Doe" onkeydown="if(event.key==='Enter')addStudent()"/>
          <div class="err" id="errName"></div>
        </div>
        <div>
          <label>Mark (%)</label>
          <input id="inputMark" type="number" min="0" max="100" placeholder="0–100" onkeydown="if(event.key==='Enter')addStudent()"/>
          <div class="err" id="errMark"></div>
        </div>
      </div>
      <button class="btn-add" onclick="addStudent()">+ Add Student</button>
    </div>

    <div class="card" id="studentListCard" style="display:none">
      <div class="card-title">Students <span id="studentCount" style="color:var(--accent)"></span></div>
      <div id="studentList"></div>
    </div>

    <button class="btn-generate" id="btnGenerate" style="display:none" onclick="generateReport()">Generate Report →</button>
    <div class="empty" id="emptyMsg">Add at least one student to generate a report.</div>
  </div>

  <!-- REPORT PHASE -->
  <div id="phaseReport" style="display:none">
    <div class="stats-grid" id="statsGrid"></div>
    <div class="prediction" id="predictionBox"></div>
    <div class="card" id="top10Card"></div>
    <div class="card" id="distinctionsCard"></div>
    <div class="card" id="evenOddCard"></div>
  </div>

</div>

<script>
let students = [];

function gradeInfo(mark) {
  if (mark >= 75) return { label: "Distinction", color: "var(--dist)" };
  if (mark >= 50) return { label: "Pass",        color: "var(--pass)" };
  return              { label: "Fail",           color: "var(--fail)" };
}

function markBarColor(mark) {
  if (mark >= 75) return "var(--dist)";
  if (mark >= 50) return "var(--pass)";
  return "var(--fail)";
}

function addStudent() {
  const nameEl = document.getElementById("inputName");
  const markEl = document.getElementById("inputMark");
  const errN   = document.getElementById("errName");
  const errM   = document.getElementById("errMark");
  let valid = true;

  if (!nameEl.value.trim()) { errN.textContent = "Name is required."; valid = false; } else errN.textContent = "";
  const m = parseFloat(markEl.value);
  if (isNaN(m) || m < 0 || m > 100) { errM.textContent = "Enter a mark between 0 and 100."; valid = false; } else errM.textContent = "";
  if (!valid) return;

  students.push({ name: nameEl.value.trim(), mark: m });
  nameEl.value = ""; markEl.value = "";
  nameEl.focus();
  renderStudentList();
}

function removeStudent(i) {
  students.splice(i, 1);
  renderStudentList();
}

function renderStudentList() {
  const list  = document.getElementById("studentList");
  const card  = document.getElementById("studentListCard");
  const btn   = document.getElementById("btnGenerate");
  const empty = document.getElementById("emptyMsg");
  const count = document.getElementById("studentCount");

  if (students.length === 0) {
    card.style.display  = "none";
    btn.style.display   = "none";
    empty.style.display = "block";
    return;
  }
  card.style.display  = "block";
  btn.style.display   = "block";
  empty.style.display = "none";
  count.textContent   = `(${students.length})`;

  list.innerHTML = students.map((s, i) => {
    const g = gradeInfo(s.mark);
    return `<div class="student-row">
      <span class="student-num">#${i+1}</span>
      <span class="student-name">${escHtml(s.name)}</span>
      <div class="mark-bar-wrap"><div class="mark-bar" style="width:${s.mark}%;background:${markBarColor(s.mark)}"></div></div>
      <span class="student-mark" style="color:${g.color}">${s.mark}%</span>
      <span class="student-grade" style="color:${g.color}">${g.label}</span>
      <button class="btn-remove" onclick="removeStudent(${i})">×</button>
    </div>`;
  }).join("");
}

async function generateReport() {
  const res  = await fetch("/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ students })
  });
  const data = await res.json();
  renderReport(data);
}

function renderReport(d) {
  document.getElementById("phaseInput").style.display  = "none";
  document.getElementById("phaseReport").style.display = "block";
  document.getElementById("btnNewSession").style.display = "block";

  document.getElementById("statsGrid").innerHTML = `
    <div class="stat-card" style="border:1px solid rgba(232,197,71,.27)">
      <div class="stat-label">Class Average</div>
      <div class="stat-value" style="color:var(--accent)">${d.average}%</div>
    </div>
    <div class="stat-card" style="border:1px solid var(--border)">
      <div class="stat-label">Highest Mark</div>
      <div class="stat-value">${d.maximum}%</div>
    </div>
    <div class="stat-card" style="border:1px solid var(--border)">
      <div class="stat-label">Lowest Mark</div>
      <div class="stat-value">${d.minimum}%</div>
    </div>
    <div class="stat-card" style="border:1px solid var(--border)">
      <div class="stat-label">Groups of 5</div>
      <div class="stat-value">${d.groups}</div>
    </div>`;

  document.getElementById("predictionBox").innerHTML = `
    <span style="font-size:20px">🎯</span>
    <div>
      <div class="pred-label">Prediction</div>
      <div class="pred-text">${escHtml(d.prediction)}</div>
    </div>`;

  const top10Rows = d.top_10.map((s, i) => {
    const g = gradeInfo(s.mark);
    const gold = i === 0;
    return `<div class="student-row" style="${gold ? 'background:var(--accent-dim);border-color:rgba(232,197,71,.27)' : ''}">
      <span class="student-num" style="${gold ? 'color:var(--accent)' : ''};font-family:'Space Mono',monospace;font-weight:700">#${i+1}</span>
      <span class="student-name" style="${gold ? 'font-weight:700' : ''}">${escHtml(s.name)}</span>
      <div class="mark-bar-wrap"><div class="mark-bar" style="width:${s.mark}%;background:${markBarColor(s.mark)}"></div></div>
      <span class="student-mark" style="color:${g.color}">${s.mark}%</span>
    </div>`;
  }).join("");
  document.getElementById("top10Card").innerHTML =
    `<div class="card-title">Top 10 Performers</div>${top10Rows}`;

  const distContent = d.distinctions.length === 0
    ? `<span style="color:var(--muted);font-family:'DM Mono',monospace;font-size:13px">No distinctions found.</span>`
    : `<div class="dist-wrap">${d.distinctions.map(s =>
        `<div class="dist-badge"><span style="color:var(--accent)">★</span>${escHtml(s.name)}<span style="font-size:12px;font-family:'DM Mono',monospace;color:var(--accent)">${s.mark}%</span></div>`
      ).join("")}</div>`;
  document.getElementById("distinctionsCard").innerHTML =
    `<div class="card-title">Distinctions <span style="color:var(--accent)">(${d.distinctions.length})</span></div>${distContent}`;

  const eoRows = d.even_odd.map(s =>
    `<div class="student-row" style="margin-bottom:6px">
      <span class="student-name" style="font-size:13px">${escHtml(s.name)}</span>
      <span class="eo-mark">${s.mark}%</span>
      <span class="${s.parity === 'Even' ? 'pill-even' : 'pill-odd'}">${s.parity}</span>
    </div>`
  ).join("");
  document.getElementById("evenOddCard").innerHTML =
    `<div class="card-title">Even / Odd Marks</div>${eoRows}`;
}

function newSession() {
  students = [];
  document.getElementById("phaseInput").style.display   = "block";
  document.getElementById("phaseReport").style.display  = "none";
  document.getElementById("btnNewSession").style.display = "none";
  renderStudentList();
}

function escHtml(s) {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
</script>
</body>
</html>"""


# =========================================
# HTTP SERVER
# =========================================

class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # silence request logs

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        if urlparse(self.path).path == "/calculate":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            payload = json.loads(body)
            result  = calculate_stats(payload.get("students", []))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()


# =========================================
# ENTRY POINT
# =========================================

if __name__ == "__main__":
    PORT = 5050
    server = http.server.HTTPServer(("localhost", PORT), Handler)

    print(f"┌─────────────────────────────────────┐")
    print(f"│  ClassMark Calculator                │")
    print(f"│  http://localhost:{PORT}               │")
    print(f"│  Press Ctrl+C to stop                │")
    print(f"└─────────────────────────────────────┘")

    threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
