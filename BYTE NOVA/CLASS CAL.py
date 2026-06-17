

# =========================================
# CLASS MARK CALCULATOR SYSTEM
# =========================================

import http.server
import json
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
# HTML / JS UI
# =========================================

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ClassMark Calculator</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Space+Mono:wght@700&display=swap" rel="stylesheet"/>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#0a0a0f;--surface:#13131a;--card:#1a1a24;--border:#2a2a3a;
    --text:#f0ede4;--muted:#7a7a9a;
    --fail:#f87171; /* red - fail */
    --pass:#f5a623; /* orange - pass */
    --dist:#4ade80; /* green - distinction */
    --pass-dim:rgba(245,166,35,.13);
    --dist-dim:rgba(74,222,128,.13);
    --fail-dim:rgba(248,113,113,.13);
    --purple:#a78bfa;--purple-dim:rgba(167,139,250,.13);
  }
  body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;padding-bottom:60px}
  input[type=text],input[type=number],input[type=password]{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-family:'DM Mono',monospace;font-size:14px;outline:none;transition:border-color .2s;width:100%}
  input:focus{border-color:var(--purple)}
  input::placeholder{color:var(--muted)}
  button{cursor:pointer;transition:opacity .15s,transform .1s;font-family:'DM Sans',sans-serif}
  button:hover{opacity:.88} button:active{transform:scale(.97)}
  label{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-family:'DM Mono',monospace;display:block;margin-bottom:6px}
  .err{color:var(--fail);font-size:11px;font-family:'DM Mono',monospace;margin-top:4px}

  .header{border-bottom:1px solid var(--border);padding:18px 32px;display:flex;align-items:center;justify-content:space-between}
  .logo{width:32px;height:32px;border-radius:8px;background:var(--purple);display:flex;align-items:center;justify-content:center;font-size:16px;margin-right:12px;flex-shrink:0}
  .brand{font-size:15px;font-weight:700}
  .brand-sub{font-size:11px;color:var(--muted);font-family:'DM Mono',monospace;letter-spacing:.06em}
  .btn-outline{background:transparent;border:1px solid var(--border);border-radius:8px;color:var(--muted);padding:7px 16px;font-size:13px;font-family:'DM Mono',monospace}

  .main{max-width:760px;margin:0 auto;padding:32px 24px}
  .card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:24px;margin-bottom:20px}
  .card-title{font-size:13px;font-weight:600;color:var(--muted);letter-spacing:.05em;text-transform:uppercase;font-family:'DM Mono',monospace;margin-bottom:18px}

  .key-banner{background:var(--purple-dim);border:1px solid rgba(167,139,250,.3);border-radius:12px;padding:18px 20px;margin-bottom:20px}
  .key-row{display:flex;gap:10px;align-items:flex-end;margin-top:10px}
  .key-row input{flex:1}
  .btn-save-key{background:var(--purple);color:#fff;border:none;border-radius:8px;padding:10px 18px;font-weight:700;font-size:13px;white-space:nowrap}
  .key-set{display:flex;align-items:center;gap:8px;font-size:13px;font-family:'DM Mono',monospace;color:var(--dist);margin-top:8px}

  .form-grid{display:grid;grid-template-columns:1fr 160px;gap:14px;margin-bottom:16px}
  .btn-add{background:var(--purple);color:#fff;border:none;border-radius:8px;padding:10px 22px;font-weight:700;font-size:14px}

  .student-row{display:flex;align-items:center;gap:12px;padding:10px 14px;background:var(--surface);border-radius:10px;border:1px solid var(--border);margin-bottom:8px}
  .student-num{font-size:11px;color:var(--muted);font-family:'DM Mono',monospace;min-width:24px}
  .student-name{flex:1;font-size:14px;font-weight:500}
  .mark-bar-wrap{flex:1;height:6px;background:var(--border);border-radius:99px;overflow:hidden;min-width:60px}
  .mark-bar{height:100%;border-radius:99px;transition:width .4s ease}
  .student-mark{font-size:14px;font-family:'DM Mono',monospace;font-weight:700;min-width:48px;text-align:right}
  .student-grade{font-size:11px;min-width:70px;text-align:right;font-family:'DM Mono',monospace}
  .btn-remove{background:transparent;border:none;color:var(--muted);font-size:18px;padding:0 4px;line-height:1}
  .btn-remove:hover{color:var(--fail)}

  .btn-generate{width:100%;background:var(--dist);color:#0a0a0f;border:none;border-radius:12px;padding:15px;font-weight:700;font-size:16px}
  .empty{text-align:center;padding:48px 0;color:var(--muted);font-family:'DM Mono',monospace;font-size:13px}

  .legend{display:flex;gap:16px;flex-wrap:wrap;margin-top:14px;font-size:11px;font-family:'DM Mono',monospace;color:var(--muted)}
  .legend span{display:inline-flex;align-items:center;gap:6px}
  .dot{width:8px;height:8px;border-radius:50%;display:inline-block}

  .stats-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:24px}
  .stat-card{background:var(--card);border-radius:12px;padding:16px 20px}
  .stat-label{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-family:'DM Mono',monospace;margin-bottom:4px}
  .stat-value{font-size:24px;font-weight:700;font-family:'Space Mono',monospace}
  .prediction{background:var(--purple-dim);border:1px solid rgba(167,139,250,.33);border-radius:12px;padding:16px 20px;margin-bottom:24px;display:flex;align-items:center;gap:12px}
  .pred-label{font-size:11px;color:var(--purple);font-family:'DM Mono',monospace;letter-spacing:.1em;text-transform:uppercase;margin-bottom:2px}
  .pred-text{font-size:15px;font-weight:600}
  .dist-wrap{display:flex;flex-wrap:wrap;gap:8px}
  .dist-badge{background:var(--dist-dim);border:1px solid rgba(74,222,128,.33);border-radius:8px;padding:8px 14px;display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600}
  .pill-even{font-size:11px;font-family:'DM Mono',monospace;padding:3px 10px;border-radius:99px;background:rgba(74,222,128,.13);color:var(--dist);border:1px solid rgba(74,222,128,.27)}
  .pill-odd{font-size:11px;font-family:'DM Mono',monospace;padding:3px 10px;border-radius:99px;background:rgba(167,139,250,.13);color:var(--purple);border:1px solid rgba(167,139,250,.27)}
  .eo-mark{font-size:13px;font-family:'DM Mono',monospace;color:var(--muted);margin-right:4px}

  .chat-box{display:flex;flex-direction:column;gap:10px;max-height:360px;overflow-y:auto;margin-bottom:14px;padding-right:4px}
  .chat-msg{padding:12px 14px;border-radius:10px;font-size:13px;line-height:1.6;max-width:90%}
  .chat-msg.user{background:var(--purple-dim);border:1px solid rgba(167,139,250,.3);align-self:flex-end;color:var(--text)}
  .chat-msg.ai{background:var(--surface);border:1px solid var(--border);align-self:flex-start;color:var(--text)}
  .chat-msg.error{background:var(--fail-dim);border:1px solid rgba(248,113,113,.3);color:var(--fail)}
  .chat-input-row{display:flex;gap:10px}
  .chat-input-row input{flex:1}
  .btn-send{background:var(--purple);color:#fff;border:none;border-radius:8px;padding:0 20px;font-weight:700;font-size:14px}
  .btn-send:disabled{opacity:.5;cursor:not-allowed}
  .suggestion-chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
  .chip{background:var(--surface);border:1px solid var(--border);border-radius:99px;padding:6px 14px;font-size:12px;color:var(--muted);font-family:'DM Mono',monospace}
  .chip:hover{border-color:var(--purple);color:var(--purple)}
  .typing{display:flex;gap:4px;padding:12px 14px}
  .typing span{width:6px;height:6px;border-radius:50%;background:var(--purple);animation:bounce 1.2s infinite}
  .typing span:nth-child(2){animation-delay:.15s}
  .typing span:nth-child(3){animation-delay:.3s}
  @keyframes bounce{0%,60%,100%{transform:translateY(0);opacity:.5}30%{transform:translateY(-4px);opacity:1}}

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
          <input id="inputMark" type="number" min="0" max="100" placeholder="0-100" onkeydown="if(event.key==='Enter')addStudent()"/>
          <div class="err" id="errMark"></div>
        </div>
      </div>
      <button class="btn-add" onclick="addStudent()">+ Add Student</button>
    </div>

    <div class="card" id="studentListCard" style="display:none">
      <div class="card-title">Students <span id="studentCount" style="color:var(--purple)"></span></div>
      <div id="studentList"></div>
      <div class="legend">
        <span><span class="dot" style="background:var(--fail)"></span>Fail (&lt;50%)</span>
        <span><span class="dot" style="background:var(--pass)"></span>Pass (50-74%)</span>
        <span><span class="dot" style="background:var(--dist)"></span>Distinction (75%+)</span>
      </div>
    </div>

    <button class="btn-generate" id="btnGenerate" style="display:none" onclick="generateReport()">Generate Report →</button>
    <div class="empty" id="emptyMsg">Add at least one student to generate a report.</div>
  </div>

  <div id="phaseReport" style="display:none">
    <div class="stats-grid" id="statsGrid"></div>
    <div class="prediction" id="predictionBox"></div>
    <div class="card" id="top10Card"></div>
    <div class="card" id="distinctionsCard"></div>
    <div class="card" id="evenOddCard"></div>

    <div class="card">
      <div class="card-title">🤖 AI Insights Chat</div>

      <div class="key-banner" id="keyBanner">
        <div style="font-size:13px;font-weight:700;margin-bottom:4px">🔑 Anthropic API Key</div>
        <div style="font-size:12px;color:var(--muted);font-family:'DM Mono',monospace">Get yours free at console.anthropic.com</div>
        <div class="key-row">
          <input type="password" id="apiKeyInput" placeholder="sk-ant-..."/>
          <button class="btn-save-key" onclick="saveKey()">Save Key</button>
        </div>
        <div class="key-set" id="keySet" style="display:none">✓ API key saved — chat is ready</div>
      </div>

      <div class="suggestion-chips" id="chips">
        <button class="chip" onclick="askChip('Which students need the most support and why?')">Who needs support?</button>
        <button class="chip" onclick="askChip('Summarize this class performance in 2-3 sentences.')">Summarize performance</button>
        <button class="chip" onclick="askChip('Give me 3 practical tips to raise the class average.')">Tips to improve average</button>
        <button class="chip" onclick="askChip('What patterns or trends do you notice in these marks?')">Spot trends</button>
      </div>

      <div class="chat-box" id="chatBox"></div>

      <div class="chat-input-row">
        <input id="chatInput" type="text" placeholder="Ask about this class's performance..." onkeydown="if(event.key==='Enter')sendChat()"/>
        <button class="btn-send" id="btnSend" onclick="sendChat()">Send</button>
      </div>
    </div>
  </div>

</div>

<script>
let students = [];
let apiKey = '';
let lastReportData = null;
let chatHistory = [];

function saveKey() {
  const val = document.getElementById('apiKeyInput').value.trim();
  if (!val.startsWith('sk-')) { alert('That does not look like a valid API key. It should start with sk-ant-'); return; }
  apiKey = val;
  document.getElementById('keySet').style.display = 'flex';
  document.getElementById('apiKeyInput').value = '';
}

function addStudent() {
  const nameEl = document.getElementById('inputName');
  const markEl = document.getElementById('inputMark');
  const errN = document.getElementById('errName');
  const errM = document.getElementById('errMark');
  let valid = true;
  if (!nameEl.value.trim()) { errN.textContent = 'Name is required.'; valid = false; } else errN.textContent = '';
  const m = parseFloat(markEl.value);
  if (isNaN(m) || m < 0 || m > 100) { errM.textContent = 'Enter a mark between 0 and 100.'; valid = false; } else errM.textContent = '';
  if (!valid) return;
  students.push({ name: nameEl.value.trim(), mark: m });
  nameEl.value = ''; markEl.value = '';
  nameEl.focus();
  renderStudentList();
}

function removeStudent(i) {
  students.splice(i, 1);
  renderStudentList();
}

function renderStudentList() {
  const list = document.getElementById('studentList');
  const card = document.getElementById('studentListCard');
  const btn = document.getElementById('btnGenerate');
  const empty = document.getElementById('emptyMsg');
  const count = document.getElementById('studentCount');
  if (students.length === 0) {
    card.style.display = 'none'; btn.style.display = 'none'; empty.style.display = 'block'; return;
  }
  card.style.display = 'block'; btn.style.display = 'block'; empty.style.display = 'none';
  count.textContent = '(' + students.length + ')';
  list.innerHTML = students.map((s, i) => {
    const g = gradeInfo(s.mark);
    return '<div class="student-row">' +
      '<span class="student-num">#' + (i+1) + '</span>' +
      '<span class="student-name">' + escHtml(s.name) + '</span>' +
      '<div class="mark-bar-wrap"><div class="mark-bar" style="width:' + s.mark + '%;background:' + barColor(s.mark) + '"></div></div>' +
      '<span class="student-mark" style="color:' + g.color + '">' + s.mark + '%</span>' +
      '<span class="student-grade" style="color:' + g.color + '">' + g.label + '</span>' +
      '<button class="btn-remove" onclick="removeStudent(' + i + ')">×</button>' +
      '</div>';
  }).join('');
}

async function generateReport() {
  const res = await fetch('/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ students })
  });
  const data = await res.json();
  lastReportData = data;
  renderReport(data);
}

function renderReport(d) {
  document.getElementById('phaseInput').style.display = 'none';
  document.getElementById('phaseReport').style.display = 'block';
  document.getElementById('btnNewSession').style.display = 'block';

  document.getElementById('statsGrid').innerHTML =
    '<div class="stat-card" style="border:1px solid rgba(167,139,250,.27)"><div class="stat-label">Class Average</div><div class="stat-value" style="color:var(--purple)">' + d.average + '%</div></div>' +
    '<div class="stat-card" style="border:1px solid var(--border)"><div class="stat-label">Highest Mark</div><div class="stat-value">' + d.maximum + '%</div></div>' +
    '<div class="stat-card" style="border:1px solid var(--border)"><div class="stat-label">Lowest Mark</div><div class="stat-value">' + d.minimum + '%</div></div>' +
    '<div class="stat-card" style="border:1px solid var(--border)"><div class="stat-label">Groups of 5</div><div class="stat-value">' + d.groups + '</div></div>';

  document.getElementById('predictionBox').innerHTML =
    '<span style="font-size:20px">🎯</span><div><div class="pred-label">Prediction</div><div class="pred-text">' + escHtml(d.prediction) + '</div></div>';

  const top10Rows = d.top_10.map((s, i) => {
    const g = gradeInfo(s.mark); const gold = i === 0;
    return '<div class="student-row" style="' + (gold ? 'background:var(--purple-dim);border-color:rgba(167,139,250,.27)' : '') + '">' +
      '<span class="student-num" style="' + (gold ? 'color:var(--purple);' : '') + 'font-family:Space Mono,monospace;font-weight:700">#' + (i+1) + '</span>' +
      '<span class="student-name" style="' + (gold ? 'font-weight:700' : '') + '">' + escHtml(s.name) + '</span>' +
      '<div class="mark-bar-wrap"><div class="mark-bar" style="width:' + s.mark + '%;background:' + barColor(s.mark) + '"></div></div>' +
      '<span class="student-mark" style="color:' + g.color + '">' + s.mark + '%</span></div>';
  }).join('');
  document.getElementById('top10Card').innerHTML = '<div class="card-title">Top 10 Performers</div>' + top10Rows;

  const distContent = d.distinctions.length === 0
    ? '<span style="color:var(--muted);font-size:13px;font-family:DM Mono,monospace">No distinctions found.</span>'
    : '<div class="dist-wrap">' + d.distinctions.map(s =>
        '<div class="dist-badge"><span style="color:var(--dist)">★</span>' + escHtml(s.name) +
        '<span style="font-size:12px;font-family:DM Mono,monospace;color:var(--dist)">' + s.mark + '%</span></div>'
      ).join('') + '</div>';
  document.getElementById('distinctionsCard').innerHTML =
    '<div class="card-title">Distinctions <span style="color:var(--dist)">(' + d.distinctions.length + ')</span></div>' + distContent;

  const eoRows = d.even_odd.map(s =>
    '<div class="student-row" style="margin-bottom:6px">' +
    '<span class="student-name" style="font-size:13px">' + escHtml(s.name) + '</span>' +
    '<span class="eo-mark">' + s.mark + '%</span>' +
    '<span class="' + (s.parity === 'Even' ? 'pill-even' : 'pill-odd') + '">' + s.parity + '</span></div>'
  ).join('');
  document.getElementById('evenOddCard').innerHTML = '<div class="card-title">Even / Odd Marks</div>' + eoRows;

  chatHistory = [];
  document.getElementById('chatBox').innerHTML = '';
}

function askChip(question) {
  document.getElementById('chatInput').value = question;
  sendChat();
}

function buildContextSummary() {
  if (!lastReportData) return '';
  const d = lastReportData;
  const studentLines = students.map(s => s.name + ': ' + s.mark + '%').join('; ');
  return 'Class data — Average: ' + d.average + '%, Highest: ' + d.maximum + '%, Lowest: ' + d.minimum +
    '%, Number of students: ' + students.length + ', Distinctions (75%+): ' + d.distinctions.length +
    '. Full list of students and marks: ' + studentLines + '.';
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const question = input.value.trim();
  if (!question) return;

  if (!apiKey) {
    appendChatMsg('error', 'Please save your API key above first.');
    return;
  }

  appendChatMsg('user', question);
  input.value = '';
  document.getElementById('btnSend').disabled = true;
  const typingId = appendTyping();

  try {
    const systemContext = 'You are a helpful teaching assistant analyzing a class performance report. ' +
      'Be concise (3-6 sentences max unless asked for more), practical, and specific to the actual data given. ' +
      buildContextSummary();

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify({
        model: 'claude-opus-4-6',
        max_tokens: 600,
        system: systemContext,
        messages: [...chatHistory, { role: 'user', content: question }]
      })
    });

    removeTyping(typingId);

    if (!response.ok) {
      const err = await response.json();
      appendChatMsg('error', 'API error: ' + (err.error?.message || response.status));
      document.getElementById('btnSend').disabled = false;
      return;
    }

    const data = await response.json();
    const reply = data.content[0].text.trim();
    chatHistory.push({ role: 'user', content: question });
    chatHistory.push({ role: 'assistant', content: reply });
    appendChatMsg('ai', reply);

  } catch (err) {
    removeTyping(typingId);
    appendChatMsg('error', 'Something went wrong: ' + err.message);
  }
  document.getElementById('btnSend').disabled = false;
}

function appendChatMsg(type, text) {
  const box = document.getElementById('chatBox');
  const div = document.createElement('div');
  div.className = 'chat-msg ' + type;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function appendTyping() {
  const box = document.getElementById('chatBox');
  const div = document.createElement('div');
  const id = 'typing-' + Date.now();
  div.id = id;
  div.className = 'chat-msg ai typing';
  div.innerHTML = '<span></span><span></span><span></span>';
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function newSession() {
  students = []; lastReportData = null; chatHistory = [];
  document.getElementById('phaseInput').style.display = 'block';
  document.getElementById('phaseReport').style.display = 'none';
  document.getElementById('btnNewSession').style.display = 'none';
  renderStudentList();
}

function gradeInfo(mark) {
  if (mark >= 75) return { label: 'Distinction', color: 'var(--dist)' };
  if (mark >= 50) return { label: 'Pass', color: 'var(--pass)' };
  return { label: 'Fail', color: 'var(--fail)' };
}
function barColor(mark) {
  if (mark >= 75) return 'var(--dist)';
  if (mark >= 50) return 'var(--pass)';
  return 'var(--fail)';
}
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        payload = json.loads(body)

        if path == "/calculate":
            result = calculate_stats(payload.get("students", []))
            self._json(result)
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


if __name__ == "__main__":
    PORT = 5050
    server = http.server.HTTPServer(("localhost", PORT), Handler)

    print("+-----------------------------------------+")
    print("| ClassMark Calculator |")
    print(f"| http://localhost:{PORT} |")
    print("| |")
    print("| No pip installs needed! |")
    print("| AI Insights chat needs an API key, |")
    print("| entered directly in the app. |")
    print("| |")
    print("| Press Ctrl+C to stop |")
    print("+-----------------------------------------+")

    threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
