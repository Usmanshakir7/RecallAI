import html
import io
import json
import math
import re
import time

import requests
import streamlit as st
import streamlit.components.v1 as components

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

# ===== UPGRADE MODULE (upload, replay, workload, confetti) =====
PALETTE = ["#35e0f2", "#8b7cff", "#4df0b0", "#ffc857", "#ff6b9a", "#7cc4ff"]


# ---------------------------------------------------------
# Small helpers
# ---------------------------------------------------------
def _md(html_text):
    """Render HTML in Streamlit (indentation stripped so it is not read as code)."""
    lines = [ln.strip() for ln in html_text.strip().splitlines() if ln.strip()]
    st.markdown("\n".join(lines), unsafe_allow_html=True)


def _esc(value):
    return html.escape(str(value))


# ---------------------------------------------------------
# CSS
# ---------------------------------------------------------
EXTRA_CSS = """
<style>
@property --ang { syntax: '<angle>'; initial-value: 0deg; inherits: false; }
@keyframes spinBorder { to { --ang: 360deg; } }
@keyframes floatUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes zonePulse { 0%,100% { box-shadow: 0 0 0 rgba(53,224,242,0); } 50% { box-shadow: 0 0 28px rgba(139,124,255,0.35); } }

/* Hero: rotating rainbow border */
.hero {
    border: 1.5px solid transparent;
    background:
        linear-gradient(135deg, rgba(17,28,51,0.96), rgba(9,15,29,0.96)) padding-box,
        conic-gradient(from var(--ang), #35e0f2, #8b7cff, #ff6b9a, #ffc857, #35e0f2) border-box;
    animation: spinBorder 7s linear infinite;
    box-shadow: 0 20px 60px rgba(139,124,255,0.15);
}

/* Glass + lift */
.panel, .summary-card, .ring-card { backdrop-filter: blur(10px); }
.metric-card { transition: transform .25s ease, box-shadow .25s ease; animation: floatUp .7s ease both; }
.metric-card:hover { transform: translateY(-6px) scale(1.02); box-shadow: 0 14px 34px rgba(53,224,242,0.18); }

/* Upload zone */
div[data-testid="stFileUploader"] section {
    background: linear-gradient(135deg, rgba(53,224,242,0.06), rgba(139,124,255,0.08));
    border: 2px dashed rgba(139,124,255,0.6);
    border-radius: 18px;
    padding: 22px;
    animation: zonePulse 3.2s ease-in-out infinite;
    transition: border-color .2s ease, transform .2s ease;
}
div[data-testid="stFileUploader"] section:hover { border-color: #35e0f2; transform: scale(1.01); }
div[data-testid="stFileUploader"] small, div[data-testid="stFileUploader"] span { color: #8fa3c4; }
div[data-testid="stFileUploader"] button {
    border-radius: 10px; border: 1px solid #34486f; background: #111c33; color: #e8f0ff;
}
.upload-ok {
    display: flex; gap: 10px; align-items: center; margin: 10px 0 4px; padding: 10px 14px;
    border-radius: 12px; font-size: 13px; color: #d9fff0;
    background: rgba(77,240,176,0.1); border: 1px solid rgba(77,240,176,0.45);
    animation: floatUp .5s ease both;
}
.upload-bad {
    margin: 10px 0 4px; padding: 10px 14px; border-radius: 12px; font-size: 13px;
    color: #ffd9e5; background: rgba(255,107,154,0.1); border: 1px solid rgba(255,107,154,0.45);
}
.fmt-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 10px; }
.fmt { font-size: 11px; padding: 2px 9px; border-radius: 99px; color: #b9aaff;
       border: 1px solid rgba(139,124,255,0.4); background: rgba(139,124,255,0.1); }

/* Replay */
.rp-legend { display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 0 14px; }
.rp { position: relative; padding: 6px 0 6px 0; }
.rp::before {
    content: ""; position: absolute; left: 50%; top: 0; bottom: 0; width: 1px;
    background: linear-gradient(180deg, transparent, rgba(139,124,255,0.4), transparent);
}
.rp-row { display: flex; gap: 10px; margin: 12px 0; width: 100%; animation: floatUp .6s ease both; }
.rp-row.right { flex-direction: row-reverse; }
.rp-av {
    width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0; display: flex;
    align-items: center; justify-content: center; font-weight: 700; color: #06101f;
    background: var(--c); box-shadow: 0 0 14px var(--c);
}
.rp-bubble {
    position: relative; z-index: 1; max-width: 46%; padding: 10px 14px; border-radius: 16px;
    background: #0d1526; border: 1px solid var(--c); line-height: 1.55; font-size: 14px;
    overflow-wrap: anywhere;
}
.rp-bubble.hot { box-shadow: 0 0 22px color-mix(in srgb, var(--tc) 45%, transparent); border-color: var(--tc); }
.rp-name { font-size: 11px; font-weight: 700; color: var(--c); margin-bottom: 3px; letter-spacing: .4px; }
.rp-tag { display: inline-block; margin-left: 8px; padding: 1px 8px; border-radius: 99px; font-size: 10px;
          font-weight: 700; color: #06101f; background: var(--tc); }
.rp-note { text-align: center; font-size: 12px; color: #6d7f9f; margin: 8px 0; position: relative; z-index: 1; }

/* Workload */
.wl-card {
    background: linear-gradient(150deg, #111c33, #0d1526); border: 1px solid #1f2f4d;
    border-radius: 16px; padding: 16px 18px; margin: 10px 0; animation: floatUp .6s ease both;
}
.wl-head { display: flex; align-items: center; gap: 12px; }
.wl-av { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center;
         justify-content: center; font-weight: 700; color: #06101f; background: var(--c); box-shadow: 0 0 16px var(--c); }
.wl-name { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 16px; flex: 1; }
.wl-count { font-family: 'Space Grotesk', sans-serif; font-size: 26px; font-weight: 700; color: var(--c); }
.wl-track { height: 8px; border-radius: 99px; background: #14213b; margin: 12px 0 8px; overflow: hidden; }
.wl-fill { height: 100%; width: var(--w); border-radius: 99px; background: var(--c); animation: barGrow 1.3s cubic-bezier(.2,.8,.2,1); }
.wl-task { font-size: 13px; color: #b6c4e0; padding: 3px 0; }
.wl-task i { color: #8fa3c4; font-style: normal; font-size: 12px; }
@media (max-width: 700px) { .rp-bubble { max-width: 78%; } }
/* Team member social links — reveal on hover */
.team-links {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 14px;
    opacity: 0;
    transform: translateY(8px);
    max-height: 0;
    overflow: hidden;
    transition: opacity 0.25s ease, transform 0.25s ease,
                max-height 0.25s ease;
}

.team-card:hover .team-links,
.team-card:focus-within .team-links {
    opacity: 1;
    transform: translateY(0);
    max-height: 50px;
}

.team-links a {
    display: inline-block;
    padding: 6px 10px;
    border: 1px solid var(--line);
    border-radius: 8px;
    color: var(--cyan);
    font-size: 12px;
    text-decoration: none;
    background: rgba(53, 224, 242, 0.07);
    transition: background 0.2s ease, border-color 0.2s ease;
}

.team-links a:hover {
    background: rgba(139, 124, 255, 0.16);
    border-color: var(--violet);
}
</style>
"""


def inject_extras():
    """Call once, right after the main CSS block."""
    st.markdown(EXTRA_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------
# UPLOAD
# ---------------------------------------------------------
def _clean_subtitles(raw):
    """Turn .srt/.vtt into 'Name: text' lines (keeps speaker tags if present)."""
    out = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.upper().startswith("WEBVTT") or s.isdigit() or "-->" in s:
            continue
        m = re.match(r"^<v\s+([^>]+)>(.*)$", s)  # VTT voice tag
        if m:
            s = f"{m.group(1).strip()}: {m.group(2).strip()}"
        out.append(re.sub(r"<[^>]+>", "", s))
    return "\n".join(out)


def _json_to_text(raw):
    data = json.loads(raw)
    if isinstance(data, dict):
        data = data.get("segments") or data.get("transcript") or data.get("messages") or data
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        lines = []
        for seg in data:
            if isinstance(seg, dict):
                who = seg.get("speaker") or seg.get("name") or seg.get("user")
                text = seg.get("text") or seg.get("content") or seg.get("message") or ""
                lines.append(f"{who}: {text}" if who else str(text))
            else:
                lines.append(str(seg))
        return "\n".join(lines)
    return json.dumps(data, indent=2)


def read_uploaded_file(uploaded):
    """Return the transcript text inside an uploaded file."""
    name = uploaded.name.lower()
    data = uploaded.getvalue()

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError:
            raise RuntimeError("PDF upload needs:  pip install pypdf")
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)

    if name.endswith(".docx"):
        try:
            import docx
        except ImportError:
            raise RuntimeError("DOCX upload needs:  pip install python-docx")
        return "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)

    raw = data.decode("utf-8", errors="ignore")
    if name.endswith((".srt", ".vtt")):
        return _clean_subtitles(raw)
    if name.endswith(".json"):
        return _json_to_text(raw)
    return raw


def _upload_key():
    return f"upload_box_{st.session_state.get('upload_n', 0)}"


def _handle_upload():
    st.session_state.pop("upload_error", None)
    uploaded = st.session_state.get(_upload_key())
    if uploaded is None:
        return
    try:
        text = read_uploaded_file(uploaded).strip()
        if not text:
            raise RuntimeError("That file has no readable text (scanned PDF or empty file?).")
        text = text[:60000]  # keep requests to the backend reasonable
        # Callbacks run before the text area is drawn, so this is allowed.
        st.session_state["meeting_transcript"] = text
        st.session_state["transcript_saved"] = text
        st.session_state["upload_info"] = f"{uploaded.name}  ·  {len(text.split()):,} words loaded"
    except Exception as error:
        st.session_state["upload_error"] = str(error)


def reset_upload():
    """Call inside clear_all(): swaps the uploader key so the file chip disappears."""
    st.session_state["upload_n"] = st.session_state.get("upload_n", 0) + 1
    st.session_state.pop("upload_info", None)
    st.session_state.pop("upload_error", None)


def render_upload_zone():
    """Drop zone. Put it above the transcript text area."""
    _md(
        """
        <div class="panel-heading">📎 Upload a transcript</div>
        <div class="panel-subtitle">Drag a file here, or paste text below.</div>
        <div class="fmt-row">
            <span class="fmt">.txt</span><span class="fmt">.md</span><span class="fmt">.vtt</span>
            <span class="fmt">.srt</span><span class="fmt">.json</span><span class="fmt">.pdf</span><span class="fmt">.docx</span>
        </div>
        """
    )
    st.file_uploader(
        "Upload transcript",
        type=["txt", "md", "vtt", "srt", "json", "pdf", "docx"],
        key=_upload_key(),
        on_change=_handle_upload,
        label_visibility="collapsed",
    )
    if st.session_state.get("upload_error"):
        _md(f'<div class="upload-bad">⚠ {_esc(st.session_state["upload_error"])}</div>')
    elif st.session_state.get("upload_info"):
        _md(f'<div class="upload-ok">✔ {_esc(st.session_state["upload_info"])}. Review it below, then analyze.</div>')


# ---------------------------------------------------------
# REPLAY TAB
# ---------------------------------------------------------
def _words(text):
    return {w for w in re.findall(r"[a-z0-9']+", text.lower()) if len(w) > 3}


def _match_kind(line, buckets):
    lw = _words(line)
    if len(lw) < 2:
        return None
    for kind in ("action", "decision", "question"):
        for text in buckets.get(kind, []):
            tw = _words(text)
            shared = len(lw & tw)
            if shared >= 2 and shared / max(1, min(len(lw), len(tw))) >= 0.5:
                return kind
    return None


TAGS = {
    "action": ("⚡ Action", "#8b7cff"),
    "decision": ("✅ Decision", "#4df0b0"),
    "question": ("❓ Open", "#ffc857"),
}


def render_replay(transcript, buckets):
    """buckets = {"action": [texts], "decision": [texts], "question": [texts]}"""
    rows, colors, side_of = [], {}, {}
    count = {"action": 0, "decision": 0, "question": 0}

    for i, line in enumerate([l for l in str(transcript).splitlines() if l.strip()][:70]):
        delay = f"{min(i * 0.10, 4):.2f}s"
        m = re.match(r"^\s*([A-Za-z][A-Za-z .'\-]{0,28}?)\s*:\s*(.+)$", line)
        if not m or len(m.group(1).split()) > 3:
            rows.append(f'<div class="rp-note" style="animation-delay:{delay}">{_esc(line.strip())}</div>')
            continue

        name, text = m.group(1).strip(), m.group(2).strip()
        if name not in colors:
            colors[name] = PALETTE[len(colors) % len(PALETTE)]
            side_of[name] = "right" if len(colors) % 2 == 0 else "left"

        kind = _match_kind(text, buckets)
        tag, tcolor, hot = "", "#35e0f2", ""
        if kind:
            count[kind] += 1
            label, tcolor = TAGS[kind]
            tag = f'<span class="rp-tag">{label}</span>'
            hot = " hot"

        rows.append(
            f'<div class="rp-row {side_of[name]}" style="--c:{colors[name]};--tc:{tcolor};animation-delay:{delay}">'
            f'<div class="rp-av">{_esc(name[:1].upper())}</div>'
            f'<div class="rp-bubble{hot}"><div class="rp-name">{_esc(name)}{tag}</div>{_esc(text)}</div></div>'
        )

    if not colors:
        st.info("Replay needs lines written like \"Name: what they said\".")
        return

    legend = "".join(
        f'<span class="fmt" style="color:{TAGS[k][1]};border-color:{TAGS[k][1]}">{TAGS[k][0]} · {n}</span>'
        for k, n in count.items()
    )
    _md(f'<div class="col-title">🎬 Meeting replay</div>')
    st.caption("Glowing bubbles are the moments the AI turned into actions, decisions or open questions.")
    _md(f'<div class="rp-legend">{legend}</div><div class="rp">{"".join(rows)}</div>')


# ---------------------------------------------------------
# WORKLOAD TAB
# ---------------------------------------------------------
def render_workload(actions, get_item_details):
    groups = {}
    for item in actions:
        text, owner, due = get_item_details(item)
        key = (owner or "Unassigned").strip()
        groups.setdefault(key, []).append((text, due))

    _md('<div class="col-title">⚖️ Who carries the load</div>')
    st.caption("Action items grouped by owner. Unassigned work is a risk.")
    if not groups:
        st.info("No action items were detected.")
        return

    biggest = max(len(v) for v in groups.values())
    ranked = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)
    for idx, (owner, tasks) in enumerate(ranked):
        color = "#ff6b9a" if owner == "Unassigned" else PALETTE[idx % len(PALETTE)]
        pct = round(len(tasks) / biggest * 100)
        task_html = "".join(
            f'<div class="wl-task">• {_esc(t)}{f" <i>· due {_esc(d)}</i>" if d else ""}</div>' for t, d in tasks
        )
        _md(
            f"""
            <div class="wl-card" style="--c:{color};animation-delay:{idx * 0.12:.2f}s">
                <div class="wl-head">
                    <div class="wl-av">{_esc(owner[:1].upper())}</div>
                    <div class="wl-name">{_esc(owner)}</div>
                    <div class="wl-count">{len(tasks)}</div>
                </div>
                <div class="wl-track"><div class="wl-fill" style="--w:{pct}%"></div></div>
                {task_html}
            </div>
            """
        )


# ---------------------------------------------------------
# CELEBRATION BURST (canvas confetti drawn over the whole page)
# ---------------------------------------------------------
_CONFETTI_JS = """
<script>
(function () {
  try {
    var doc = window.parent.document, old = doc.getElementById('recall-burst');
    if (old) old.remove();
    var c = doc.createElement('canvas'); c.id = 'recall-burst';
    c.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:99999';
    doc.body.appendChild(c);
    var w = c.width = window.parent.innerWidth, h = c.height = window.parent.innerHeight;
    var g = c.getContext('2d'), cols = ['#35e0f2', '#8b7cff', '#4df0b0', '#ffc857', '#ff6b9a'], p = [];
    for (var i = 0; i < 170; i++) {
      var a = Math.random() * 6.283, s = 6 + Math.random() * 14;
      p.push({x: w / 2, y: h * 0.4, vx: Math.cos(a) * s, vy: Math.sin(a) * s - 5,
              r: 3 + Math.random() * 5, c: cols[i % 5], rot: Math.random() * 6, life: 1});
    }
    var t0 = performance.now();
    (function step(now) {
      g.clearRect(0, 0, w, h);
      p.forEach(function (q) {
        q.vy += 0.28; q.vx *= 0.985; q.x += q.vx; q.y += q.vy; q.rot += 0.2; q.life -= 0.006;
        g.save(); g.globalAlpha = Math.max(q.life, 0); g.translate(q.x, q.y); g.rotate(q.rot);
        g.fillStyle = q.c; g.shadowColor = q.c; g.shadowBlur = 8; g.fillRect(-q.r, -q.r / 2, q.r * 2, q.r); g.restore();
      });
      if (now - t0 < 3200) requestAnimationFrame(step); else c.remove();
    })(t0);
  } catch (e) {}
})();
</script>
"""


def celebrate():
    """Call right after a successful analysis."""
    components.html(_CONFETTI_JS, height=0)



# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="RecallAI | Meeting Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_URL = "http://127.0.0.1:8000"
API_URL = BASE_URL + "/analyze"

# A ready-made transcript so judges can try the app in one click.
SAMPLE_TRANSCRIPT = transcript = (
    "Usman: Hey everyone, let's review our progress. We have two days "
    "left before the Open Agent Hackathon 2026 submission deadline. "
    "Today we need to finalize the main features, identify blockers, "
    "and assign the remaining tasks. Azizullah, can you start with "
    "the backend update?\n"

    "Azizullah: The FastAPI backend is mostly ready. The /analyze "
    "endpoint can process meeting transcripts and return summaries, "
    "key points, decisions, and action items. I still need to test "
    "edge cases, especially missing deadlines and unclear task owners. "
    "I also need to verify how the frontend handles API errors.\n"

    "Usman: Can you finish the remaining tests by Thursday evening "
    "and deploy the backend by Friday afternoon? We need time to test "
    "the complete application before recording the demo.\n"

    "Azizullah: I can finish testing by Thursday evening. Friday "
    "afternoon is my deployment target, provided there are no "
    "environment or configuration issues. I'll also document the "
    "API endpoint and verify the production URL.\n"

    "Palwasha: The main Streamlit dashboard is complete. Users can "
    "paste a meeting transcript, analyze it, and view the insights. "
    "I've also added PDF report downloads. I'm fixing the mobile "
    "layout because some action-item cards are too wide on small "
    "screens. I also need to improve the loading state.\n"

    "Usman: Please prioritize the mobile layout and loading state. "
    "Can you finish those by Thursday evening? After that, test the "
    "PDF download and confirm it includes the summary, decisions, "
    "topics, and action items.\n"

    "Palwasha: Yes, I'll finish the layout fixes by Thursday evening "
    "and test the PDF export. I'll also check how long action items "
    "wrap in the PDF because some formatting needs improvement.\n"

    "Muhammad Anis: For the demo, I suggest using a realistic meeting "
    "transcript, showing how RecallAI extracts responsibilities and "
    "deadlines, and then downloading the PDF report. We should also "
    "explain how the memory feature connects information across "
    "meetings.\n"

    "Usman: Agreed. I'll prepare the two-minute demo script and pitch "
    "slides covering the problem, solution, workflow, and technology "
    "stack. Anis, please review the script and check whether it "
    "clearly explains the value of RecallAI.\n"

    "Muhammad Anis: I'll review the script and prepare a final QA "
    "checklist. I'll test a longer transcript with several speakers, "
    "multiple deadlines, and unresolved questions to identify "
    "problems in the extracted insights.\n"

    "Azizullah: One concern is that if a transcript says a task is "
    "due Friday without specifying the date, the system might treat "
    "it as a definite calendar deadline. We should preserve that "
    "ambiguity instead of inventing an exact date.\n"

    "Usman: That's important. RecallAI should only report information "
    "supported by the transcript. If a deadline is unclear, it "
    "should flag it instead of making assumptions.\n"

    "Palwasha: Should the PDF include the full transcript or only "
    "the insights? Including the full transcript could make the "
    "report very long for larger meetings.\n"

    "Muhammad Anis: I recommend an insights-only PDF for the "
    "hackathon demo. It should contain the meeting summary, key "
    "decisions, action items with owners and deadlines, and "
    "unresolved questions. Full transcript export can be considered "
    "later.\n"

    "Azizullah: That works. We also need to decide how long user "
    "transcripts will be stored. We shouldn't leave the retention "
    "policy unclear if we're presenting this as a usable product.\n"

    "Usman: Agreed, but we don't have enough time to finalize that "
    "policy before submission. Let's record it as an open question "
    "and avoid claiming a retention period we haven't implemented. "
    "After the hackathon, we can discuss retention controls and "
    "deletion options.\n"

    "Palwasha: We should also verify that the deployed frontend "
    "connects to the deployed backend, not a local API URL. "
    "Otherwise, it might work on our laptops but fail during "
    "the demo.\n"

    "Azizullah: I'll confirm the backend deployment URL and share "
    "it with the team. Palwasha can then update the frontend "
    "configuration and test the live connection.\n"

    "Muhammad Anis: I'll prepare a QA checklist covering transcript "
    "analysis, API connectivity, action-item extraction, PDF "
    "formatting, and the complete demo flow. We should rehearse "
    "the entire demo at least once before recording.\n"

    "Usman: Let's confirm the plan. Azizullah will complete backend "
    "testing by Thursday evening and target deployment for Friday "
    "afternoon. Palwasha will finish the mobile layout and loading "
    "state by Thursday evening, then verify PDF formatting and "
    "the live API connection. Anis will test realistic transcripts, "
    "review the demo script, and prepare the QA checklist. I'll "
    "finish the demo script and pitch slides. We'll keep the PDF "
    "insights-only for now, while transcript retention remains "
    "an open question after the hackathon.\n"

    "Muhammad Anis: Sounds good. I'll share the checklist in the "
    "group tonight so everyone can track progress.\n"

    "Usman: Perfect. Please update the group when you finish your "
    "tasks or encounter a blocker. We need the final integration "
    "tested before recording the demo. Thanks, everyone."
)

# Used by Demo Mode, so the app still works if the backend is down.
DEMO_RESULT = {
    "summary": (
        "The team reviewed progress two days before the hackathon demo. "
        "The backend API is nearly done, the dashboard needs final polish, "
        "and a demo script is still missing. They confirmed FastAPI and "
        "Streamlit as the stack and agreed to keep the PDF report "
        "insights-only for now."
    ),
    "topics": [
        "Hackathon demo",
        "Backend API",
        "Dashboard polish",
        "Demo script",
        "PDF report",
        "Data storage",
    ],
    "key_points": [
        "Two days remain before the hackathon demo.",
        "The /analyze endpoint is almost ready.",
        "The mobile layout still needs fixing.",
    ],
    "decisions": [
        "Use FastAPI for the backend and Streamlit for the frontend.",
        "Keep the PDF report insights-only for now.",
        "Revisit transcript storage after the hackathon.",
    ],
    "action_items": [
        {
            "task": "Finish and deploy the /analyze endpoint",
            "owner": "Azizullah",
            "due": "Friday",
        },
        {
            "task": "Complete the dashboard and fix the mobile layout",
            "owner": "Palwasha",
            "due": "Thursday evening",
        },
        {
            "task": "Write the two-minute demo script and pitch slides",
            "owner": "Usman",
        },
    ],
    "open_questions": [
        "Should the PDF include the full transcript?",
        "How long should user transcripts be stored?",
    ],
}


# =========================================================
# PDF REPORT GENERATOR
# =========================================================
def create_pdf(result):
    """Create a formatted PDF report from RecallAI meeting insights."""
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="RecallAI Meeting Report",
        author="RecallAI",
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RecallTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#5145A8"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "RecallSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=18,
    )
    heading_style = ParagraphStyle(
        "RecallHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#5145A8"),
        spaceBefore=12,
        spaceAfter=7,
    )
    body_style = ParagraphStyle(
        "RecallBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=7,
        wordWrap="CJK",
    )

    def escape_pdf_text(value):
        # Make text safe for ReportLab and keep line breaks.
        return (
            html.escape(str(value))
            .replace("\r\n", "\n")
            .replace("\n", "<br/>")
        )

    story = [
        Paragraph("RecallAI", title_style),
        Paragraph("Meeting Intelligence Report", subtitle_style),
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=colors.HexColor("#63D9E8"),
            spaceAfter=14,
        ),
    ]

    def add_section(title, value):
        story.append(Paragraph(escape_pdf_text(title), heading_style))

        if value is None or value == "":
            story.append(Paragraph("Not available.", body_style))
            return

        if isinstance(value, (list, tuple)):
            if not value:
                story.append(Paragraph("No items identified.", body_style))
                return

            for item in value:
                if isinstance(item, dict):
                    item = " | ".join(
                        f"{key}: {val}"
                        for key, val in item.items()
                        if val is not None and val != ""
                    ) or "Item"

                story.append(
                    Paragraph(
                        "&#8226;&nbsp; " + escape_pdf_text(item),
                        body_style,
                    )
                )
        else:
            story.append(Paragraph(escape_pdf_text(value), body_style))

    add_section("Executive Summary", result.get("summary"))

    if result.get("key_points"):
        add_section("Important Points", result["key_points"])

    add_section("Topics Discussed", result.get("topics", []))
    add_section("Decisions Made", result.get("decisions", []))
    add_section("Action Items", result.get("action_items", []))
    add_section("Open Questions", result.get("open_questions", []))

    story.extend(
        [
            Spacer(1, 18),
            HRFlowable(
                width="100%",
                thickness=0.6,
                color=colors.HexColor("#CBD5E1"),
            ),
            Spacer(1, 8),
            Paragraph("Generated by RecallAI", subtitle_style),
        ]
    )

    document.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# =========================================================
# THEME: CSS + ANIMATIONS
# =========================================================
st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap'
    );

    :root {
        --bg: #060a14;
        --panel: #0d1526;
        --panel-2: #111c33;
        --line: #1f2f4d;
        --text: #e8f0ff;
        --muted: #8fa3c4;
        --cyan: #35e0f2;
        --violet: #8b7cff;
        --mint: #4df0b0;
        --amber: #ffc857;
        --rose: #ff6b9a;
    }

    .stApp {
        color: var(--text);
        font-family: 'DM Sans', sans-serif;
        background-color: var(--bg);
        background-image:
            linear-gradient(rgba(53,224,242,0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(53,224,242,0.035) 1px, transparent 1px),
            radial-gradient(ellipse 700px 420px at 10% 0%, rgba(139,124,255,0.22), transparent 70%),
            radial-gradient(ellipse 650px 400px at 92% 8%, rgba(53,224,242,0.16), transparent 70%);
        background-size: 46px 46px, 46px 46px, 100% 100%, 100% 100%;
        background-repeat: repeat, repeat, no-repeat, no-repeat;
        animation: driftGlow 18s ease-in-out infinite alternate;
    }

    @keyframes driftGlow {
        0% { background-position: 0 0, 0 0, 0% 0%, 100% 0%; }
        100% { background-position: 46px 46px, 46px 46px, 6% 14%, 94% 10%; }
    }

    header[data-testid="stHeader"] { background: transparent; }
    footer { visibility: hidden; }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--text);
        letter-spacing: -0.5px;
    }

    p, label, span, li { font-family: 'DM Sans', sans-serif; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1122 0%, #070c18 100%);
        border-right: 1px solid var(--line);
    }

    section[data-testid="stSidebar"] .block-container { padding-top: 1.4rem; }

    .brand { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }

    .brand-icon {
        width: 42px;
        height: 42px;
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 21px;
        background: linear-gradient(135deg, var(--cyan), var(--violet));
        animation: logoGlow 3s ease-in-out infinite;
    }

    @keyframes logoGlow {
        0%, 100% { box-shadow: 0 0 12px rgba(53,224,242,0.35); }
        50% { box-shadow: 0 0 26px rgba(139,124,255,0.7); }
    }

    .brand-name {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: var(--text);
        line-height: 1.1;
    }

    .brand-tag { font-size: 12px; color: var(--muted); }

    .side-title {
        font-size: 12px;
        color: var(--muted);
        margin: 18px 0 8px;
        font-weight: 600;
    }

    .status-box {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 11px 13px;
        border: 1px solid var(--line);
        border-radius: 12px;
        background: var(--panel);
        font-size: 13px;
    }

    .status-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
    .status-dot.online { background: var(--mint); animation: dotPulse 1.8s ease-out infinite; }
    .status-dot.offline { background: var(--rose); }
    .status-dot.demo { background: var(--amber); animation: dotPulseAmber 1.8s ease-out infinite; }

    @keyframes dotPulse {
        0% { box-shadow: 0 0 0 0 rgba(77,240,176,0.6); }
        100% { box-shadow: 0 0 0 10px rgba(77,240,176,0); }
    }

    @keyframes dotPulseAmber {
        0% { box-shadow: 0 0 0 0 rgba(255,200,87,0.6); }
        100% { box-shadow: 0 0 0 10px rgba(255,200,87,0); }
    }

    .side-note {
        font-size: 12px;
        color: var(--muted);
        line-height: 1.6;
        margin-top: 22px;
        padding-top: 14px;
        border-top: 1px solid var(--line);
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 6px; }

    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 12px;
        padding: 10px 14px;
        width: 100%;
        transition: background 0.2s ease, border-color 0.2s ease;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: var(--panel-2); }

    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(100deg, rgba(53,224,242,0.14), rgba(139,124,255,0.14));
        border-color: rgba(139,124,255,0.55);
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none; }

    .hero {
        position: relative;
        padding: 36px 36px 30px;
        border: 1px solid var(--line);
        border-radius: 26px;
        background: linear-gradient(135deg, rgba(17,28,51,0.92), rgba(9,15,29,0.92));
        overflow: hidden;
        margin-bottom: 22px;
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(32px, 5vw, 54px);
        font-weight: 700;
        letter-spacing: -2px;
        line-height: 1.08;
        margin: 0 0 12px;
        background: linear-gradient(95deg, #ffffff 10%, #b8aeff 55%, #6be8f5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-description {
        color: var(--muted);
        font-size: 16px;
        line-height: 1.7;
        max-width: 560px;
        margin-bottom: 26px;
    }

    .wave { display: flex; align-items: center; gap: 4px; height: 90px; }

    .wave span {
        flex: 1;
        height: var(--h);
        border-radius: 99px;
        background: linear-gradient(180deg, var(--cyan), var(--violet));
        transform-origin: center;
        animation: waveBar 2s ease-in-out infinite;
        opacity: 0.9;
    }

    .wave.busy span { animation-duration: 0.7s; }

    @keyframes waveBar {
        0%, 100% { transform: scaleY(0.3); }
        50% { transform: scaleY(1); }
    }

    .panel {
        background: rgba(13,21,38,0.9);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 16px;
    }

    .panel-heading {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .panel-subtitle { font-size: 13px; line-height: 1.6; color: var(--muted); }

    .step { display: flex; gap: 14px; align-items: flex-start; padding: 12px 0; }
    .step + .step { border-top: 1px solid var(--line); }

    .step-num {
        width: 30px;
        height: 30px;
        flex-shrink: 0;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 13px;
        color: #06101f;
        background: linear-gradient(135deg, var(--cyan), var(--violet));
    }

    .step-title { font-weight: 600; font-size: 14px; }
    .step-text { font-size: 13px; color: var(--muted); line-height: 1.55; }

    .scanner {
        border: 1px solid rgba(139,124,255,0.5);
        border-radius: 18px;
        padding: 22px;
        background: rgba(17,28,51,0.9);
        margin: 14px 0;
    }

    .scanner-text {
        margin-top: 14px;
        font-size: 14px;
        color: var(--cyan);
        animation: blink 1.4s ease-in-out infinite;
    }

    @keyframes blink {
        0%, 100% { opacity: 0.55; }
        50% { opacity: 1; }
    }

    @property --num {
        syntax: '<integer>';
        initial-value: 0;
        inherits: false;
    }

    .metric-card {
        background: linear-gradient(150deg, var(--panel-2), var(--panel));
        border: 1px solid var(--line);
        border-top: 3px solid var(--accent, var(--cyan));
        border-radius: 16px;
        padding: 16px 18px;
        min-height: 112px;
    }

    .metric-top { display: flex; justify-content: space-between; align-items: center; }
    .metric-label { color: var(--muted); font-size: 13px; font-weight: 500; }
    .metric-icon { font-size: 18px; }

    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 38px;
        font-weight: 700;
        margin-top: 8px;
        color: var(--accent, var(--cyan));
        animation: countUp 1.3s ease-out;
        counter-reset: num var(--num);
    }

    .metric-value::after { content: counter(num); }

    @keyframes countUp { from { --num: 0; } }

    .summary-card {
        position: relative;
        background: linear-gradient(120deg, rgba(33,28,66,0.95), rgba(14,38,56,0.95));
        border: 1px solid rgba(139,124,255,0.45);
        border-radius: 20px;
        padding: 26px;
        height: 100%;
        min-height: 250px;
        overflow: hidden;
    }

    .summary-card::after {
        content: "";
        position: absolute;
        top: 0;
        left: -60%;
        width: 40%;
        height: 100%;
        background: linear-gradient(100deg, transparent, rgba(255,255,255,0.09), transparent);
        animation: sweep 1.8s ease-out 0.3s 1 forwards;
    }

    @keyframes sweep { to { left: 130%; } }

    .summary-label { color: #b9aaff; font-size: 14px; font-weight: 600; margin-bottom: 10px; }

    .summary-text {
        color: #f0f4ff;
        font-size: 16px;
        line-height: 1.85;
        overflow-wrap: anywhere;
    }

    .ring-card {
        background: linear-gradient(150deg, var(--panel-2), var(--panel));
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 20px;
        min-height: 250px;
        display: flex;
        gap: 18px;
        align-items: center;
    }

    .ring-box { position: relative; width: 130px; height: 130px; flex-shrink: 0; }
    .ring-box svg { width: 130px; height: 130px; }

    .ring-bg { fill: none; stroke: #1b2a47; stroke-width: 10; }

    .ring-fg {
        fill: none;
        stroke: url(#ringGrad);
        stroke-width: 10;
        stroke-linecap: round;
        stroke-dasharray: 351.86;
        stroke-dashoffset: var(--final);
        transform: rotate(-90deg);
        transform-origin: 70px 70px;
        animation: ringFill 1.8s cubic-bezier(.2,.8,.2,1);
        filter: drop-shadow(0 0 6px rgba(53,224,242,0.6));
    }

    @keyframes ringFill { from { stroke-dashoffset: 351.86; } }

    .ring-center {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .ring-num {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 34px;
        font-weight: 700;
        color: var(--text);
        animation: countUp 1.8s ease-out;
        counter-reset: num var(--num);
    }

    .ring-num::after { content: counter(num); }
    .ring-of { font-size: 11px; color: var(--muted); }

    .ring-title { font-family: 'Space Grotesk', sans-serif; font-size: 17px; font-weight: 600; }
    .ring-verdict { font-size: 13px; color: var(--cyan); margin: 2px 0 10px; }
    .ring-row { font-size: 13px; color: var(--muted); line-height: 1.9; }
    .ring-row b { color: var(--text); font-weight: 600; }
    .ring-note { font-size: 11px; color: #6d7f9f; margin-top: 8px; line-height: 1.5; }

    .item {
        background: var(--panel);
        border: 1px solid var(--line);
        border-left: 3px solid var(--accent, var(--cyan));
        border-radius: 12px;
        padding: 14px 16px;
        margin: 10px 0;
        line-height: 1.6;
        overflow-wrap: anywhere;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .item:hover { transform: translateX(4px); border-color: var(--accent, var(--cyan)); }

    .item-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }

    .chip {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-size: 12px;
        color: #d9e3ff;
        background: rgba(139,124,255,0.14);
        border: 1px solid rgba(139,124,255,0.4);
        border-radius: 99px;
        padding: 3px 11px 3px 4px;
    }

    .chip.plain {
        padding: 3px 11px;
        background: rgba(53,224,242,0.1);
        border-color: rgba(53,224,242,0.35);
    }

    .avatar {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
        color: #06101f;
        background: linear-gradient(135deg, var(--cyan), var(--violet));
    }

    .topic-chip {
        display: inline-block;
        background: rgba(139,124,255,0.14);
        border: 1px solid rgba(139,124,255,0.45);
        color: #e2dcff;
        border-radius: 99px;
        padding: 8px 15px;
        margin: 4px 6px 6px 0;
        font-size: 13px;
    }

    .empty-state { color: var(--muted); font-size: 14px; line-height: 1.7; padding: 10px 0; }

    .col-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 18px;
        font-weight: 600;
        margin: 6px 0 2px;
    }

    .bar-row { margin: 14px 0; }
    .bar-top { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px; }
    .bar-top span:last-child { color: var(--muted); }

    .bar-track { height: 10px; border-radius: 99px; background: #14213b; overflow: hidden; }

    .bar-fill {
        height: 100%;
        width: var(--w);
        border-radius: 99px;
        background: linear-gradient(90deg, var(--cyan), var(--violet));
        animation: barGrow 1.4s cubic-bezier(.2,.8,.2,1);
    }

    @keyframes barGrow { from { width: 0; } }

    .team-card {
        background: linear-gradient(150deg, var(--panel-2), var(--panel));
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 22px 18px;
        min-height: 190px;
        text-align: center;
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    }

    .team-card:hover {
        transform: translateY(-6px);
        border-color: var(--violet);
        box-shadow: 0 12px 30px rgba(139,124,255,0.2);
    }

    .team-avatar {
        width: 62px;
        height: 62px;
        margin: 0 auto 14px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        background: linear-gradient(135deg, rgba(53,224,242,0.25), rgba(139,124,255,0.25));
        border: 1px solid rgba(139,124,255,0.5);
    }

    .team-name { font-family: 'Space Grotesk', sans-serif; font-size: 17px; font-weight: 600; }
    .team-role { font-size: 13px; color: var(--cyan); margin-top: 6px; line-height: 1.5; }

    div[data-testid="stTextArea"] textarea {
        background: #0a1222;
        color: var(--text);
        border: 1px solid #2a3c5e;
        border-radius: 14px;
        line-height: 1.7;
        font-size: 15px;
    }

    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--cyan);
        box-shadow: 0 0 0 1px var(--cyan), 0 0 22px rgba(53,224,242,0.18);
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        border: none;
        border-radius: 12px;
        min-height: 50px;
        font-weight: 700;
        font-size: 16px;
        color: #05101f;
        background: linear-gradient(100deg, var(--cyan), var(--violet));
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        color: #05101f;
        transform: translateY(-2px);
        box-shadow: 0 10px 28px rgba(53,224,242,0.3);
    }

    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"],
    .stDownloadButton > button {
        border: 1px solid #34486f;
        border-radius: 12px;
        min-height: 46px;
        font-weight: 600;
        color: var(--text);
        background: var(--panel-2);
        transition: border-color 0.2s ease, transform 0.2s ease;
    }

    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover,
    .stDownloadButton > button:hover {
        color: var(--text);
        border-color: var(--cyan);
        transform: translateY(-1px);
    }

    div[data-testid="stAlert"] { border-radius: 12px; }
    div[data-testid="stTabs"] button { font-weight: 600; font-size: 15px; }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: var(--cyan); }
    hr { border-color: var(--line); }

    .footer { text-align: center; padding: 30px 0 6px; color: #6d7f9f; font-size: 12px; }

    @media (max-width: 700px) {
        .hero { padding: 22px; }
        .wave { height: 64px; gap: 2px; }
        .ring-card { flex-direction: column; text-align: center; }
    }

    @media (prefers-reduced-motion: reduce) {
        * { animation: none !important; transition: none !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# NEW: upload zone, replay, workload and hero upgrades
inject_extras()


# =========================================================
# KNOWLEDGE GRAPH (interactive canvas, pure JavaScript)
# =========================================================
GRAPH_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { box-sizing: border-box; }
body { margin: 0; background: transparent; font-family: 'Segoe UI', system-ui, sans-serif; color: #e8f0ff; }
#wrap {
    position: relative;
    border: 1px solid #1f2f4d;
    border-radius: 20px;
    overflow: hidden;
    background: radial-gradient(ellipse at 50% 40%, #101b36 0%, #070d1c 75%);
}
#legend { display: flex; flex-wrap: wrap; gap: 8px; padding: 12px 14px; border-bottom: 1px solid #1f2f4d; }
.lg {
    display: flex; align-items: center; gap: 8px; cursor: pointer; user-select: none;
    font-size: 13px; padding: 5px 12px; border: 1px solid #2a3c5e; border-radius: 99px;
    background: #0d1526; color: #e8f0ff; transition: opacity .2s, border-color .2s;
}
.lg:hover { border-color: #35e0f2; }
.lg.off { opacity: .35; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
canvas { display: block; cursor: grab; touch-action: none; }
#tip {
    position: absolute; pointer-events: none; max-width: 290px; padding: 10px 12px;
    border-radius: 12px; background: rgba(7,13,28,.96); border: 1px solid #35e0f2;
    font-size: 13px; line-height: 1.5; display: none; z-index: 5; white-space: pre-wrap;
}
#tip b { display: block; font-size: 11px; margin-bottom: 3px; }
#hint { position: absolute; right: 14px; bottom: 10px; font-size: 12px; color: #8fa3c4; pointer-events: none; }
</style>
</head>
<body>
<div id="wrap">
    <div id="legend"></div>
    <canvas id="c"></canvas>
    <div id="tip"></div>
    <div id="hint">Drag nodes · Click to focus</div>
</div>
<script>
(function () {
    var DATA = __DATA__;

    var COLORS = {
        hub: '#b8aeff', person: '#35e0f2', action: '#8b7cff',
        decision: '#4df0b0', question: '#ffc857', topic: '#ff6b9a'
    };
    var LABELS = {
        person: 'People', action: 'Actions', decision: 'Decisions',
        question: 'Questions', topic: 'Topics'
    };
    var TYPE_NAMES = {
        hub: 'Meeting', person: 'Person', action: 'Action item',
        decision: 'Decision', question: 'Open question', topic: 'Topic'
    };

    var wrap = document.getElementById('wrap');
    var canvas = document.getElementById('c');
    var ctx = canvas.getContext('2d');
    var tip = document.getElementById('tip');
    var legend = document.getElementById('legend');

    var W = 800, H = 540, dpr = 1;

    function resize() {
        W = wrap.clientWidth;
        H = W < 520 ? 440 : 540;
        dpr = window.devicePixelRatio || 1;
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        canvas.style.width = W + 'px';
        canvas.style.height = H + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener('resize', resize);

    var t0 = performance.now();
    var nodes = DATA.nodes.map(function (n, i) {
        return {
            id: n.id, type: n.type, label: n.label, full: n.full,
            x: W / 2 + (Math.random() - 0.5) * 10,
            y: H / 2 + (Math.random() - 0.5) * 10,
            vx: 0, vy: 0,
            r: n.type === 'hub' ? 24 : (n.type === 'person' ? 15 : 11),
            birth: t0 + (n.type === 'hub' ? 0 : 350 + i * 45),
            phase: Math.random() * 6.28,
            nb: {}
        };
    });

    var byId = {};
    nodes.forEach(function (n) { byId[n.id] = n; });

    var links = DATA.links.map(function (l) {
        return { a: byId[l.s], b: byId[l.t], len: l.len || 140, off: Math.random() };
    });

    links.forEach(function (l) {
        l.a.nb[l.b.id] = true;
        l.b.nb[l.a.id] = true;
    });

    var hidden = {};
    var hover = null, selected = null, drag = null, moved = false;

    function vis(n) { return n.type === 'hub' || !hidden[n.type]; }
    function born(n, now) { return now >= n.birth; }

    var counts = {};
    nodes.forEach(function (n) { counts[n.type] = (counts[n.type] || 0) + 1; });

    Object.keys(LABELS).forEach(function (type) {
        if (!counts[type]) { return; }
        var el = document.createElement('div');
        el.className = 'lg';
        var dot = document.createElement('span');
        dot.className = 'dot';
        dot.style.background = COLORS[type];
        dot.style.boxShadow = '0 0 8px ' + COLORS[type];
        var text = document.createElement('span');
        text.textContent = LABELS[type] + ' ' + counts[type];
        el.appendChild(dot);
        el.appendChild(text);
        el.onclick = function () {
            hidden[type] = !hidden[type];
            el.className = hidden[type] ? 'lg off' : 'lg';
            if (selected && !vis(selected)) { selected = null; }
        };
        legend.appendChild(el);
    });

    function ease(t) {
        var c = 1.70158;
        return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2);
    }

    function tick(now) {
        var vs = nodes.filter(function (n) { return vis(n) && born(n, now); });

        for (var i = 0; i < vs.length; i++) {
            for (var j = i + 1; j < vs.length; j++) {
                var a = vs[i], b = vs[j];
                var dx = b.x - a.x, dy = b.y - a.y;
                var d2 = dx * dx + dy * dy;
                if (d2 < 150) { d2 = 150; }
                var d = Math.sqrt(d2);
                var f = Math.min(6500 / d2, 3);
                var fx = dx / d * f, fy = dy / d * f;
                a.vx -= fx; a.vy -= fy;
                b.vx += fx; b.vy += fy;
            }
        }

        links.forEach(function (l) {
            if (!vis(l.a) || !vis(l.b) || !born(l.a, now) || !born(l.b, now)) { return; }
            var dx = l.b.x - l.a.x, dy = l.b.y - l.a.y;
            var d = Math.sqrt(dx * dx + dy * dy) || 1;
            var k = (d - l.len) * 0.02;
            var fx = dx / d * k, fy = dy / d * k;
            l.a.vx += fx; l.a.vy += fy;
            l.b.vx -= fx; l.b.vy -= fy;
        });

        vs.forEach(function (n) {
            var g = n.type === 'hub' ? 0.03 : 0.004;
            n.vx += (W / 2 - n.x) * g;
            n.vy += (H / 2 - n.y) * g;
            if (n === drag) { return; }
            n.vx *= 0.84;
            n.vy *= 0.84;
            n.x += n.vx + Math.sin(now / 1100 + n.phase) * 0.12;
            n.y += n.vy + Math.cos(now / 1300 + n.phase) * 0.12;
            n.x = Math.max(24, Math.min(W - 24, n.x));
            n.y = Math.max(24, Math.min(H - 24, n.y));
        });
    }

    function truncate(text, max) {
        return text.length > max ? text.slice(0, max - 1) + '…' : text;
    }

    function draw(now) {
        ctx.clearRect(0, 0, W, H);
        var sel = selected;
        var showAll = nodes.length <= 22;

        links.forEach(function (l) {
            if (!vis(l.a) || !vis(l.b) || !born(l.a, now) || !born(l.b, now)) { return; }
            var dim = sel && !(l.a === sel || l.b === sel);

            ctx.globalAlpha = dim ? 0.08 : 0.35;
            ctx.strokeStyle = COLORS[l.b.type];
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.moveTo(l.a.x, l.a.y);
            ctx.lineTo(l.b.x, l.b.y);
            ctx.stroke();

            if (!dim) {
                var t = ((now / 2600) + l.off) % 1;
                var px = l.a.x + (l.b.x - l.a.x) * t;
                var py = l.a.y + (l.b.y - l.a.y) * t;
                ctx.globalAlpha = 0.95;
                ctx.fillStyle = COLORS[l.b.type];
                ctx.shadowColor = COLORS[l.b.type];
                ctx.shadowBlur = 10;
                ctx.beginPath();
                ctx.arc(px, py, 2.2, 0, 6.2832);
                ctx.fill();
                ctx.shadowBlur = 0;
            }
        });

        nodes.forEach(function (n) {
            if (!vis(n) || !born(n, now)) { return; }

            var p = Math.min(1, (now - n.birth) / 600);
            var s = ease(p);
            var r = n.r * s;
            var active = (n === hover || n === sel);
            var dim = sel && n !== sel && !sel.nb[n.id];

            ctx.globalAlpha = dim ? 0.2 : 1;

            if (n.type === 'hub') {
                var pulse = (now / 1800) % 1;
                ctx.globalAlpha = (dim ? 0.2 : 1) * (1 - pulse) * 0.6;
                ctx.strokeStyle = '#b8aeff';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(n.x, n.y, r + pulse * 34, 0, 6.2832);
                ctx.stroke();
                ctx.globalAlpha = dim ? 0.2 : 1;
            }

            ctx.shadowColor = COLORS[n.type];
            ctx.shadowBlur = active ? 32 : 16;

            if (n.type === 'hub') {
                var grad = ctx.createLinearGradient(n.x - r, n.y - r, n.x + r, n.y + r);
                grad.addColorStop(0, '#35e0f2');
                grad.addColorStop(1, '#8b7cff');
                ctx.fillStyle = grad;
            } else {
                ctx.fillStyle = COLORS[n.type];
            }

            ctx.beginPath();
            ctx.arc(n.x, n.y, r, 0, 6.2832);
            ctx.fill();
            ctx.shadowBlur = 0;

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            if (n.type === 'hub') {
                ctx.font = '22px sans-serif';
                ctx.fillStyle = '#06101f';
                ctx.fillText('🧠', n.x, n.y + 1);
            } else if (n.type === 'person') {
                ctx.font = 'bold ' + Math.round(14 * s) + 'px sans-serif';
                ctx.fillStyle = '#06101f';
                ctx.fillText(n.label.charAt(0).toUpperCase(), n.x, n.y + 1);
            }

            var near = sel && (n === sel || sel.nb[n.id]);
            if (n.type === 'person' || showAll || active || near) {
                ctx.font = '12px sans-serif';
                ctx.fillStyle = '#d6e0fa';
                ctx.textBaseline = 'alphabetic';
                ctx.fillText(
                    truncate(n.label, active || near ? 40 : 24),
                    n.x, n.y + r + 16
                );
            }
        });

        ctx.globalAlpha = 1;
    }

    function pos(e) {
        var rect = canvas.getBoundingClientRect();
        return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    }

    function pick(p) {
        var best = null, bestDist = 1e9, now = performance.now();
        nodes.forEach(function (n) {
            if (!vis(n) || !born(n, now)) { return; }
            var d = Math.hypot(n.x - p.x, n.y - p.y);
            if (d < n.r + 8 && d < bestDist) { best = n; bestDist = d; }
        });
        return best;
    }

    function showTip(n, p) {
        if (!n) { tip.style.display = 'none'; return; }
        tip.innerHTML = '';
        var title = document.createElement('b');
        title.textContent = TYPE_NAMES[n.type];
        title.style.color = COLORS[n.type];
        tip.appendChild(title);
        tip.appendChild(document.createTextNode(n.full));
        tip.style.display = 'block';
        tip.style.left = Math.max(8, Math.min(p.x + 16, W - 300)) + 'px';
        tip.style.top = (canvas.offsetTop + p.y + 16) + 'px';
    }

    canvas.addEventListener('pointerdown', function (e) {
        var n = pick(pos(e));
        if (n) {
            drag = n;
            moved = false;
            canvas.setPointerCapture(e.pointerId);
            canvas.style.cursor = 'grabbing';
        }
    });

    canvas.addEventListener('pointermove', function (e) {
        var p = pos(e);
        if (drag) {
            drag.x = p.x; drag.y = p.y;
            drag.vx = 0; drag.vy = 0;
            moved = true;
            showTip(drag, p);
        } else {
            hover = pick(p);
            canvas.style.cursor = hover ? 'pointer' : 'grab';
            showTip(hover, p);
        }
    });

    canvas.addEventListener('pointerup', function () {
        if (drag && !moved) {
            selected = (selected === drag) ? null : drag;
        } else if (!drag) {
            selected = null;
        }
        drag = null;
        canvas.style.cursor = hover ? 'pointer' : 'grab';
    });

    canvas.addEventListener('pointerleave', function () {
        hover = null;
        tip.style.display = 'none';
    });

    function frame(now) {
        tick(now);
        draw(now);
        requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
})();
</script>
</body>
</html>
"""


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def safe_text(value):
    """Escape dynamic text before inserting it into HTML."""
    return html.escape(str(value))


def render(html_text):
    """Show an HTML block (indentation stripped so markdown won't treat it as code)."""
    lines = []
    for line in html_text.strip().splitlines():
        if line.strip():
            lines.append(line.strip())
    st.markdown("\n".join(lines), unsafe_allow_html=True)


def wave_html(busy=False, bars=48):
    """Build the animated waveform used in the hero and loader."""
    spans = []
    for i in range(bars):
        height = 22 + int(abs(math.sin(i * 0.55)) * 55
                          + abs(math.sin(i * 0.17)) * 23)
        delay = i * 0.05
        spans.append(
            f'<span style="--h:{height}%;animation-delay:{delay:.2f}s"></span>'
        )

    css_class = "wave busy" if busy else "wave"
    return f'<div class="{css_class}">{"".join(spans)}</div>'


@st.cache_data(ttl=10, show_spinner=False)
def check_backend():
    """Return True if the FastAPI backend answers (checked every 10s)."""
    try:
        response = requests.get(BASE_URL + "/docs", timeout=1.5)
        return response.status_code < 500
    except requests.exceptions.RequestException:
        return False


def get_item_details(item):
    """Support both dictionary and plain-text insight items."""
    if isinstance(item, dict):
        text = (
            item.get("task")
            or item.get("title")
            or item.get("decision")
            or item.get("question")
            or item.get("text")
            or item.get("description")
            or "Untitled item"
        )
        owner = item.get("owner") or item.get("assignee")
        due = item.get("due") or item.get("deadline") or item.get("due_date")
        return (
            str(text),
            str(owner) if owner else None,
            str(due) if due else None,
        )

    return str(item), None, None


def to_list(value):
    """Make sure a field is always a list."""
    if not value:
        return []
    if isinstance(value, (str, dict)):
        return [value]
    return list(value)


def render_items(items, accent="#35e0f2", empty_message="Nothing to show yet."):
    """Render insight cards with an accent colour, owner and due date."""
    if not items:
        render(f'<div class="empty-state">{safe_text(empty_message)}</div>')
        return

    for item in items:
        text, owner, due = get_item_details(item)

        meta_html = ""
        if owner or due:
            chips = ""
            if owner:
                initial = safe_text(owner.strip()[:1].upper() or "?")
                chips += (
                    f'<span class="chip"><span class="avatar">{initial}</span>'
                    f'{safe_text(owner)}</span>'
                )
            if due:
                chips += f'<span class="chip plain">⏱ {safe_text(due)}</span>'
            meta_html = f'<div class="item-meta">{chips}</div>'

        render(
            f"""
            <div class="item" style="--accent:{accent};">
                <div>{safe_text(text)}</div>
                {meta_html}
            </div>
            """
        )


def get_speakers(text):
    """Count how many words each speaker said ("Name: words...")."""
    counts = {}
    for line in str(text).splitlines():
        match = re.match(r"^\s*([A-Za-z][A-Za-z .'\-]{0,28}?)\s*:\s*(.+)$", line)
        if not match:
            continue

        name = match.group(1).strip()
        if len(name.split()) > 3:
            continue

        words = len(match.group(2).split())
        counts[name] = counts.get(name, 0) + words

    return counts


def find_person_key(owner, persons):
    """Match an owner name to a known speaker (first name is enough)."""
    key = owner.strip().lower()
    if key in persons:
        return key

    first_name = key.split()[0] if key.split() else key
    for existing_key in persons:
        if existing_key.split()[0] == first_name:
            return existing_key

    return None


def build_graph_data(topics, decisions, actions, questions, speakers):
    """Turn the meeting results into nodes and links for the graph."""
    nodes = [
        {
            "id": "hub",
            "type": "hub",
            "label": "Meeting",
            "full": "The meeting. Everything connects here.",
        }
    ]
    links = []

    def short(text, size=28):
        return text if len(text) <= size else text[: size - 1] + "…"

    persons = {}
    for name in speakers:
        persons[name.lower()] = name

    action_owner_keys = []
    for item in actions:
        text, owner, due = get_item_details(item)
        key = None
        if owner:
            key = find_person_key(owner, persons)
            if key is None:
                key = owner.strip().lower()
                persons[key] = owner.strip()
        action_owner_keys.append(key)

    for key, display in persons.items():
        words = speakers.get(display, 0)
        detail = f"{words} words spoken" if words else "Task owner"
        nodes.append(
            {
                "id": "p_" + key,
                "type": "person",
                "label": display,
                "full": f"{display}\n{detail}",
            }
        )
        links.append({"s": "hub", "t": "p_" + key, "len": 130})

    for index, topic in enumerate(topics):
        text, owner, due = get_item_details(topic)
        node_id = f"t{index}"
        nodes.append({"id": node_id, "type": "topic", "label": short(text), "full": text})
        links.append({"s": "hub", "t": node_id, "len": 150})

    for index, decision in enumerate(decisions):
        text, owner, due = get_item_details(decision)
        node_id = f"d{index}"
        nodes.append({"id": node_id, "type": "decision", "label": short(text), "full": text})
        links.append({"s": "hub", "t": node_id, "len": 170})

    for index, question in enumerate(questions):
        text, owner, due = get_item_details(question)
        node_id = f"q{index}"
        nodes.append({"id": node_id, "type": "question", "label": short(text), "full": text})
        links.append({"s": "hub", "t": node_id, "len": 190})

    for index, item in enumerate(actions):
        text, owner, due = get_item_details(item)
        node_id = f"a{index}"

        full = text
        if owner:
            full += f"\nOwner: {owner}"
        if due:
            full += f"\nDue: {due}"

        nodes.append({"id": node_id, "type": "action", "label": short(text), "full": full})

        key = action_owner_keys[index]
        if key:
            links.append({"s": "p_" + key, "t": node_id, "len": 95})
        else:
            links.append({"s": "hub", "t": node_id, "len": 160})

    return {"nodes": nodes, "links": links}


def graph_html(data):
    """Put the graph data into the HTML template."""
    data_json = json.dumps(data).replace("</", "<\\/")
    return GRAPH_TEMPLATE.replace("__DATA__", data_json)


def compute_readiness(actions, decisions, questions):
    """
    Score how ready the team is to execute (0 to 100):
      50 points - action items that have an owner
      20 points - action items that have a deadline
      30 points - decisions made vs questions still open
    """
    total_actions = len(actions)
    with_owner = 0
    with_due = 0

    for item in actions:
        text, owner, due = get_item_details(item)
        if owner:
            with_owner += 1
        if due:
            with_due += 1

    owner_ratio = with_owner / total_actions if total_actions else 0
    due_ratio = with_due / total_actions if total_actions else 0

    answered_total = len(decisions) + len(questions)
    resolved_ratio = len(decisions) / answered_total if answered_total else 0

    score = round(50 * owner_ratio + 20 * due_ratio + 30 * resolved_ratio)

    if score >= 80:
        verdict = "Ready to execute"
    elif score >= 55:
        verdict = "A few answers needed"
    else:
        verdict = "Needs follow-up"

    return {
        "score": score,
        "verdict": verdict,
        "with_owner": with_owner,
        "with_due": with_due,
        "total_actions": total_actions,
        "decisions": len(decisions),
        "questions": len(questions),
    }


def make_share_text(summary, decisions, actions, questions):
    """Build a plain message the user can paste into Slack or WhatsApp."""
    lines = ["Meeting recap (RecallAI)", "", summary, ""]

    if decisions:
        lines.append("Decisions:")
        for item in decisions:
            text, owner, due = get_item_details(item)
            lines.append(f"- {text}")
        lines.append("")

    if actions:
        lines.append("Action items:")
        for item in actions:
            text, owner, due = get_item_details(item)
            extra = ""
            if owner:
                extra += f" ({owner}"
                extra += f", {due})" if due else ")"
            elif due:
                extra += f" ({due})"
            lines.append(f"- {text}{extra}")
        lines.append("")

    if questions:
        lines.append("Open questions:")
        for item in questions:
            text, owner, due = get_item_details(item)
            lines.append(f"- {text}")

    return "\n".join(lines).strip()


def load_sample():
    """Button callback: fill the box with the sample transcript."""
    st.session_state["meeting_transcript"] = SAMPLE_TRANSCRIPT
    st.session_state["transcript_saved"] = SAMPLE_TRANSCRIPT


def clear_all():
    """Button callback: clear transcript and results."""
    st.session_state["meeting_transcript"] = ""
    st.session_state["transcript_saved"] = ""
    st.session_state.pop("recallai_result", None)
    st.session_state.pop("analyzed_transcript", None)
    reset_upload()  # NEW: also clears the uploaded file chip


# Streamlit forgets a text box when you leave its page,
# so we keep a saved copy and restore it here.
if "meeting_transcript" not in st.session_state:
    st.session_state["meeting_transcript"] = st.session_state.get(
        "transcript_saved", ""
    )


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    render(
        """
        <div class="brand">
            <div class="brand-icon">🧠</div>
            <div>
                <div class="brand-name">RecallAI</div>
                <div class="brand-tag">Meeting intelligence</div>
            </div>
        </div>
        """
    )

    render('<div class="side-title">Navigate</div>')
    page = st.radio(
        "Navigation",
        ["🧠  Workspace", "👥  Team NOVAMIND"],
        label_visibility="collapsed",
    )

    render('<div class="side-title">Quick actions</div>')
    st.button(
        "✦ Load sample meeting",
        on_click=load_sample,
        use_container_width=True,
    )
    st.button(
        "↺ Clear everything",
        on_click=clear_all,
        use_container_width=True,
    )

    render('<div class="side-title">System</div>')
    demo_mode = st.toggle(
    "Demo mode (no backend needed)",
    value=True,
    key="demo_mode",
    help="Uses built-in sample results. Handy if the backend or Wi-Fi fails during the presentation.",
     )

    backend_online = check_backend()
    if demo_mode:
        render(
            """
            <div class="status-box">
                <span class="status-dot demo"></span>
                <span>Demo mode is on</span>
            </div>
            """
        )
    elif backend_online:
        render(
            """
            <div class="status-box">
                <span class="status-dot online"></span>
                <span>AI backend online</span>
            </div>
            """
        )
    else:
        render(
            """
            <div class="status-box">
                <span class="status-dot offline"></span>
                <span>Backend offline. Start FastAPI or turn on Demo mode.</span>
            </div>
            """
        )

    render(
        """
        <div class="side-note">
            Built for the Open Agent Hackathon 2026.<br>
            Always verify AI results before acting on them.
        </div>
        """
    )


# =========================================================
# PAGE 1: WORKSPACE
# =========================================================
def show_workspace():
    render(
        f"""
        <div class="hero">
            <div class="hero-title">Every meeting, remembered.</div>
            <div class="hero-description">
                Paste or upload a transcript. RecallAI pulls out the decisions,
                the owners, and the questions nobody answered.
            </div>
            {wave_html()}
        </div>
        """
    )

    input_column, guide_column = st.columns([1.7, 1], gap="large")

    with input_column:
        render_upload_zone()  # NEW: drag-and-drop upload

        render(
            """
            <div class="panel-heading" style="margin-top:14px;">✍️ Meeting transcript</div>
            <div class="panel-subtitle" style="margin-bottom:10px;">
                Paste notes or a full transcript. Lines like "Name: text"
                let RecallAI show who spoke and who owns each task.
            </div>
            """
        )

        transcript = st.text_area(
            "Meeting transcript",
            placeholder=(
                "Example:\n"
                "He: I will complete the backend API by Friday.\n"
                "She: I will finish the dashboard.\n"
                "The team decided to use FastAPI for the backend."
            ),
            height=260,
            label_visibility="collapsed",
            key="meeting_transcript",
        )

        st.session_state["transcript_saved"] = transcript

        st.caption(f"{len(transcript.split())} words")

        process_clicked = st.button(
            "✦  Analyze meeting",
            type="primary",
            use_container_width=True,
        )

    with guide_column:
        render(
            """
            <div class="panel">
                <div class="panel-heading">How it works</div>
                <div class="step">
                    <div class="step-num">1</div>
                    <div>
                        <div class="step-title">Upload or paste</div>
                        <div class="step-text">Drop a .txt, .vtt, .srt, .pdf or .docx, or load the sample.</div>
                    </div>
                </div>
                <div class="step">
                    <div class="step-num">2</div>
                    <div>
                        <div class="step-title">Analyze</div>
                        <div class="step-text">The AI backend reads the whole conversation.</div>
                    </div>
                </div>
                <div class="step">
                    <div class="step-num">3</div>
                    <div>
                        <div class="step-title">Explore and export</div>
                        <div class="step-text">Replay the meeting, dive into the graph, share a PDF.</div>
                    </div>
                </div>
            </div>
            """
        )

    # ---------------- Run the analysis ----------------
    if process_clicked:
        if not transcript.strip() and not demo_mode:
            st.warning(
                "Paste or upload a meeting transcript first, or load the "
                "sample meeting from the sidebar."
            )
        else:
            loader = st.empty()
            loader.markdown(
                (
                    '<div class="scanner">'
                    + wave_html(busy=True)
                    + '<div class="scanner-text">RecallAI is reading your meeting...</div>'
                    + "</div>"
                ),
                unsafe_allow_html=True,
            )

            try:
                if demo_mode:
                    time.sleep(1.8)
                    result = DEMO_RESULT
                    if not transcript.strip():
                        transcript_used = SAMPLE_TRANSCRIPT
                    else:
                        transcript_used = transcript
                else:
                    response = requests.post(
                        API_URL,
                        json={"transcript": transcript},
                        timeout=120,
                    )
                    response.raise_for_status()
                    result = response.json()
                    transcript_used = transcript

                    if not isinstance(result, dict):
                        raise ValueError(
                            "The backend response must be a JSON object."
                        )

                st.session_state["recallai_result"] = result
                st.session_state["analyzed_transcript"] = transcript_used
                st.toast("Analysis ready", icon="✅")
                celebrate()  # NEW: confetti burst

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to the backend. Make sure FastAPI is "
                    "running at http://127.0.0.1:8000, or turn on Demo mode "
                    "in the sidebar."
                )

            except requests.exceptions.Timeout:
                st.error("Analysis took too long. Please try again.")

            except requests.exceptions.HTTPError as error:
                st.error(f"The backend returned an HTTP error: {error}")

            except requests.exceptions.RequestException as error:
                st.error(f"Request failed: {error}")

            except (ValueError, json.JSONDecodeError) as error:
                st.error(f"Could not read the backend response: {error}")

            finally:
                loader.empty()

    # ---------------- Results ----------------
    result = st.session_state.get("recallai_result")

    if not result:
        render(
            """
            <div class="panel" style="text-align:center;padding:34px 20px;margin-top:14px;">
                <div class="panel-heading" style="font-size:21px;">Your results will appear here</div>
                <div class="panel-subtitle">
                    Add a transcript and select Analyze meeting.
                    You will get a summary, a readiness score, an interactive
                    knowledge graph, a meeting replay, decisions and action items.
                </div>
            </div>
            """
        )
        return

    topics = to_list(result.get("topics"))
    decisions = to_list(result.get("decisions"))
    actions = to_list(result.get("action_items"))
    questions = to_list(result.get("open_questions"))
    key_points = to_list(result.get("key_points"))
    summary = result.get("summary") or "No summary returned."
    analyzed_text = st.session_state.get("analyzed_transcript", "")
    speakers = get_speakers(analyzed_text)

    st.markdown("## 🧠 Meeting intelligence")
    st.caption("Your conversation, organized into decisions, tasks and insights.")

    metrics = [
        ("Key topics", len(topics), "🎯", "#35e0f2"),
        ("Decisions", len(decisions), "✅", "#4df0b0"),
        ("Action items", len(actions), "⚡", "#8b7cff"),
        ("Open questions", len(questions), "❓", "#ffc857"),
    ]

    metric_columns = st.columns(4)
    for column, (label, value, icon, accent) in zip(metric_columns, metrics):
        with column:
            render(
                f"""
                <div class="metric-card" style="--accent:{accent};">
                    <div class="metric-top">
                        <div class="metric-label">{safe_text(label)}</div>
                        <div class="metric-icon">{icon}</div>
                    </div>
                    <div class="metric-value" style="--num:{int(value)};"></div>
                </div>
                """
            )

    st.write("")

    summary_column, ring_column = st.columns([1.5, 1], gap="large")

    with summary_column:
        render(
            f"""
            <div class="summary-card">
                <div class="summary-label">✦ Executive summary</div>
                <div class="summary-text">{safe_text(summary)}</div>
            </div>
            """
        )

    with ring_column:
        health = compute_readiness(actions, decisions, questions)
        offset = 351.86 * (1 - health["score"] / 100)

        render(
            f"""
            <div class="ring-card">
                <div class="ring-box">
                    <svg viewBox="0 0 140 140">
                        <defs>
                            <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#35e0f2"/>
                                <stop offset="100%" stop-color="#8b7cff"/>
                            </linearGradient>
                        </defs>
                        <circle class="ring-bg" cx="70" cy="70" r="56"/>
                        <circle class="ring-fg" cx="70" cy="70" r="56" style="--final:{offset:.2f};"/>
                    </svg>
                    <div class="ring-center">
                        <div class="ring-num" style="--num:{health['score']};"></div>
                        <div class="ring-of">out of 100</div>
                    </div>
                </div>
                <div>
                    <div class="ring-title">Execution readiness</div>
                    <div class="ring-verdict">{safe_text(health['verdict'])}</div>
                    <div class="ring-row">
                        Owners assigned: <b>{health['with_owner']}/{health['total_actions']}</b><br>
                        Deadlines set: <b>{health['with_due']}/{health['total_actions']}</b><br>
                        Decisions vs open questions: <b>{health['decisions']} / {health['questions']}</b>
                    </div>
                    <div class="ring-note">Calculated from the extracted results, not guessed by the AI.</div>
                </div>
            </div>
            """
        )

    # ---------------- Knowledge graph ----------------
    st.write("")
    render('<div class="col-title">🕸️ Meeting knowledge graph</div>')
    st.caption(
        "Drag nodes around. Click one to focus on its connections. "
        "Click a legend chip to hide a group."
    )

    graph_data = build_graph_data(topics, decisions, actions, questions, speakers)
    components.html(graph_html(graph_data), height=640, scrolling=False)

    # ---------------- Tabs ----------------
    st.write("")
    (
        tab_actions,
        tab_overview,
        tab_questions,
        tab_speakers,
        tab_replay,
        tab_load,
    ) = st.tabs(
        [
            "⚡ Actions & decisions",
            "🎯 Topics & key points",
            "❓ Open questions",
            "🎙️ Who spoke",
            "🎬 Replay",
            "⚖️ Workload",
        ]
    )

    with tab_actions:
        left, right = st.columns(2, gap="large")

        with left:
            render('<div class="col-title">⚡ Action items</div>')
            st.caption("Who needs to do what.")
            render_items(
                actions,
                accent="#8b7cff",
                empty_message="No action items were detected.",
            )

        with right:
            render('<div class="col-title">✅ Decisions made</div>')
            st.caption("What the team agreed on.")
            render_items(
                decisions,
                accent="#4df0b0",
                empty_message="No decisions were detected.",
            )

    with tab_overview:
        left, right = st.columns(2, gap="large")

        with left:
            render('<div class="col-title">🎯 Topics discussed</div>')
            if topics:
                chips = "".join(
                    f'<span class="topic-chip">{safe_text(get_item_details(topic)[0])}</span>'
                    for topic in topics
                )
                render(f"<div>{chips}</div>")
            else:
                st.info("No topics were detected.")

        with right:
            render('<div class="col-title">💡 Important points</div>')
            render_items(
                key_points,
                accent="#35e0f2",
                empty_message="The backend returned no separate key points.",
            )

    with tab_questions:
        render('<div class="col-title">❓ Still unanswered</div>')
        st.caption("Questions to settle before the next meeting.")
        render_items(
            questions,
            accent="#ffc857",
            empty_message="No open questions were detected.",
        )

    with tab_speakers:
        render('<div class="col-title">🎙️ Speaking share</div>')
        st.caption("Share of words spoken, counted from lines like \"Name: text\".")

        total_words = sum(speakers.values())
        if total_words == 0:
            st.info(
                "No speaker names found. Write the transcript as "
                "\"Name: what they said\" to see this chart."
            )
        else:
            ranked = sorted(speakers.items(), key=lambda pair: pair[1], reverse=True)
            for name, words in ranked:
                percent = round(words / total_words * 100)
                render(
                    f"""
                    <div class="bar-row">
                        <div class="bar-top">
                            <span>{safe_text(name)}</span>
                            <span>{percent}% · {words} words</span>
                        </div>
                        <div class="bar-track">
                            <div class="bar-fill" style="--w:{percent}%;"></div>
                        </div>
                    </div>
                    """
                )

    with tab_replay:  # NEW
        texts = lambda items: [get_item_details(i)[0] for i in items]
        render_replay(
            analyzed_text,
            {
                "action": texts(actions),
                "decision": texts(decisions),
                "question": texts(questions),
            },
        )

    with tab_load:  # NEW
        render_workload(actions, get_item_details)

    # ---------------- Export ----------------
    st.divider()
    render('<div class="col-title">📥 Export meeting insights</div>')

    export_data = {
        "summary": summary,
        "topics": topics,
        "key_points": key_points,
        "decisions": decisions,
        "action_items": actions,
        "open_questions": questions,
    }

    pdf_column, json_column, note_column = st.columns([1, 1, 1.4], gap="large")

    with pdf_column:
        try:
            pdf_data = create_pdf(export_data)
            st.download_button(
                label="↓ Download PDF report",
                data=pdf_data,
                file_name="RecallAI_Meeting_Report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as error:
            st.error(f"Could not generate the PDF report: {error}")

    with json_column:
        st.download_button(
            label="↓ Download JSON data",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name="RecallAI_Meeting_Data.json",
            mime="application/json",
            use_container_width=True,
        )

    with note_column:
        st.caption(
            "The PDF includes the summary, topics, decisions, action items "
            "and open questions. Verify AI-generated results before acting on them."
        )

    with st.expander("📋 Copy as a message (Slack, WhatsApp, email)"):
        st.code(
            make_share_text(summary, decisions, actions, questions),
            language=None,
        )


# =========================================================
# PAGE 2: TEAM
# =========================================================
def show_team():
      render(
        """
        <div class="hero">
            <div class="hero-title">Team NOVAMIND</div>
            <div class="hero-description" style="margin-bottom:0;">
                Four people building RecallAI for the
                Open Agent Hackathon 2026.
            </div>
        </div>
        """
        )
  
    team_members = [
    (
        "Usman Shakir",
        "Team Lead · AI/ML Developer",
        "🧠",
        "https://linkedin.com/in/usman-shakir7/",
        "https://github.com/Usmanshakir7",
    ),
    (
        "Azizullah Asad",
        "Backend Developer",
        "⚙️",
        "",
        "",
    ),
    (
        "Palwasha Sajjad",
        "Frontend Developer",
        "🎨",
        "https://www.linkedin.com/in/palwasheyqureshi/",
        "https://github.com/Palwasha-48",
    ),
    (
        "Muhammad Anis",
        "Technical Guider",
        "📋",
        "",
        "",
    ),
]

team_columns = st.columns(4, gap="medium")

for column, (name, role, icon, linkedin_url, github_url) in zip(
    team_columns, team_members
):
    with column:
        social_links = ""

        if linkedin_url:
            social_links += (
                f'<a href="{linkedin_url}" target="_blank" '
                'rel="noopener noreferrer">LinkedIn</a>'
            )

        if github_url:
            social_links += (
                f'<a href="{github_url}" target="_blank" '
                'rel="noopener noreferrer">GitHub</a>'
            )

        render(
            f"""
            <div class="team-card">
                <div class="team-avatar">{icon}</div>
                <div class="team-name">{safe_text(name)}</div>
                <div class="team-role">{safe_text(role)}</div>
                <div class="team-links">{social_links}</div>
            </div>
            """
        )
            render(
                f"""
                <div class="team-card">
                    <div class="team-avatar">{icon}</div>
                    <div class="team-name">{safe_text(name)}</div>
                    <div class="team-role">{safe_text(role)}</div>
                </div>
                """
            )

    st.write("")
    render(
        """
        <div class="panel">
            <div class="panel-heading">What RecallAI does</div>
            <div class="panel-subtitle">
                Most meetings end with good intentions and no record.
                RecallAI turns a raw transcript into a summary, clear
                decisions, tasks with owners, and the questions that
                are still open, so work moves forward right after the call.
            </div>
        </div>
        """
      )


# =========================================================
# ROUTER + FOOTER
# =========================================================
if "Team" in page:
    show_team()
else:
    show_workspace()

render(
    """
    <div class="footer">
        RecallAI · From conversations to execution · Open Agent Hackathon 2026
    </div>
    """
)
