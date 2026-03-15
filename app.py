"""
InvestiCore — Streamlit Frontend v4
Clean dark UI — no CSS fighting Streamlit's textarea wrapper.
"""

import os
import uuid
import json
import requests
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────

def _cfg(key: str, default: str) -> str:
    try:
        return st.secrets[key]
    except (FileNotFoundError, KeyError):
        return os.getenv(key, default)

INVESTIGATION_URL = _cfg("INVESTIGATION_URL", "http://localhost:5000").rstrip("/")
APP_ENV           = _cfg("APP_ENV", "development")
IS_DEV            = APP_ENV == "development"
REQUEST_TIMEOUT   = 120

st.set_page_config(
    page_title="InvestiCore",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {"result": None, "error": None, "trace_id": None, "loading": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"], .stApp {
    background-color: #0d1117 !important;
    color: #c9d1d9 !important;
    font-family: 'Inter', sans-serif !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 3rem 4rem 5rem !important; max-width: 920px !important; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

/* ── Force textarea dark — target every nesting level Streamlit uses ── */
.stTextArea textarea,
.stTextArea > div > div > textarea,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="base-input"] textarea {
    background-color: #161b22 !important;
    color: #c9d1d9 !important;
    border: 1.5px solid #30363d !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.65 !important;
    padding: 14px 16px !important;
    caret-color: #58a6ff !important;
    resize: vertical !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextArea textarea:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.12) !important;
    outline: none !important;
    background-color: #161b22 !important;
}
.stTextArea textarea::placeholder { color: #484f58 !important; }
/* Kill Streamlit wrapper borders */
.stTextArea > div,
.stTextArea > div > div,
div[data-baseweb="textarea"],
div[data-baseweb="base-input"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* ── Buttons — base (secondary) ── */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    padding: 0.55rem 1.4rem !important;
    white-space: nowrap !important;
    letter-spacing: 0.02em !important;
    transition: all 0.15s !important;
    background: transparent !important;
    color: #8b949e !important;
    border: 1px solid #30363d !important;
}
.stButton > button:hover {
    background: #21262d !important;
    color: #c9d1d9 !important;
    border-color: #484f58 !important;
}
/* ── Primary button — Streamlit sets kind="primaryFormSubmit" or kind="primary" ── */
.stButton > button[kind="primary"],
.stButton > button[kind="primaryFormSubmit"] {
    background: #238636 !important;
    color: #ffffff !important;
    border: 1px solid #2ea043 !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[kind="primaryFormSubmit"]:hover {
    background: #2ea043 !important;
    border-color: #3fb950 !important;
    color: #ffffff !important;
}
.stButton > button[kind="primary"]:disabled,
.stButton > button[kind="primaryFormSubmit"]:disabled {
    opacity: 0.35 !important;
}

/* ── Warning ── */
div[data-testid="stAlert"] {
    background: #1c1a00 !important;
    border: 1px solid #3d3400 !important;
    border-radius: 8px !important;
    color: #d29922 !important;
}

/* ── Cards ── */
.ic-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.85rem;
}
.ic-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.63rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #484f58;
    margin-bottom: 0.8rem;
}
.ic-root-cause { font-size:0.97rem; color:#c9d1d9; line-height:1.65; }

.ic-conf-row { display:flex; align-items:center; gap:12px; }
.ic-conf-track { flex:1; height:4px; background:#21262d; border-radius:2px; overflow:hidden; }
.ic-conf-fill  { height:100%; border-radius:2px; }
.ic-conf-pct   { font-family:'IBM Plex Mono',monospace; font-size:0.95rem; font-weight:600; min-width:40px; text-align:right; }

.ic-row { display:flex; gap:10px; align-items:flex-start; padding:0.48rem 0; border-bottom:1px solid #21262d; font-size:0.875rem; color:#c9d1d9; line-height:1.6; }
.ic-row:last-child { border-bottom:none; padding-bottom:0; }
.ic-dot  { color:#58a6ff; flex-shrink:0; margin-top:3px; font-size:0.5rem; }
.ic-num  { font-family:'IBM Plex Mono',monospace; font-size:0.68rem; color:#d29922; min-width:20px; flex-shrink:0; padding-top:3px; }
.ic-tool-name { font-family:'IBM Plex Mono',monospace; font-size:0.78rem; }

.ic-timeline { position:relative; padding-left:1.2rem; }
.ic-timeline::before { content:''; position:absolute; left:5px; top:6px; bottom:6px; width:1px; background:#21262d; }
.ic-step { position:relative; display:flex; justify-content:space-between; align-items:center; padding:0.55rem 0; }
.ic-step-dot { position:absolute; left:-1.2rem; top:50%; transform:translateY(-50%); width:8px; height:8px; border-radius:50%; border:1.5px solid; background:#161b22; }
.ic-step-dot.success { border-color:#3fb950; }
.ic-step-dot.failed  { border-color:#f85149; }
.ic-step-dot.timeout { border-color:#d29922; }
.ic-step-info { display:flex; flex-direction:column; gap:1px; }
.ic-step-name { font-family:'IBM Plex Mono',monospace; font-size:0.8rem; color:#c9d1d9; }
.ic-step-dur  { font-size:0.7rem; color:#484f58; }
.ic-badge { font-family:'IBM Plex Mono',monospace; font-size:0.63rem; font-weight:600; padding:2px 6px; border-radius:3px; }
.ic-badge.success { background:#0d2c18; color:#3fb950; }
.ic-badge.failed  { background:#2c0f0f; color:#f85149; }
.ic-badge.timeout { background:#2c1f00; color:#d29922; }

.ic-meta { display:flex; gap:1.4rem; align-items:center; flex-wrap:wrap; margin-bottom:1.25rem; }
.ic-pill { font-family:'IBM Plex Mono',monospace; font-size:0.65rem; font-weight:600; padding:3px 9px; border-radius:4px; letter-spacing:0.06em; text-transform:uppercase; }
.ic-pill.Success { background:#0d2c18; color:#3fb950; border:1px solid #1a4728; }
.ic-pill.Failed  { background:#2c0f0f; color:#f85149; border:1px solid #4a1919; }
.ic-pill.Partial { background:#2c1f00; color:#d29922; border:1px solid #4a3500; }
.ic-kv { font-family:'IBM Plex Mono',monospace; font-size:0.67rem; color:#484f58; }
.ic-kv span { color:#8b949e; }

.ic-err { background:#160d0d; border:1px solid #4a1919; border-radius:10px; padding:1.2rem 1.4rem; }
.ic-err-label { font-family:'IBM Plex Mono',monospace; font-size:0.63rem; font-weight:600; letter-spacing:0.2em; text-transform:uppercase; color:#f85149; margin-bottom:0.5rem; }
.ic-err-msg   { font-size:0.875rem; color:#ffa0a0; line-height:1.6; margin-bottom:0.4rem; }
.ic-err-trace { font-family:'IBM Plex Mono',monospace; font-size:0.67rem; color:#484f58; }

.ic-divider { height:1px; background:linear-gradient(90deg,#58a6ff,#21262d 45%,transparent); margin:0.3rem 0 2.5rem; opacity:0.45; }

.ic-chips { display:flex; flex-wrap:wrap; gap:6px; margin-top:9px; margin-bottom:1.6rem; }
.ic-chip { font-family:'IBM Plex Mono',monospace; font-size:0.68rem; color:#8b949e; background:#161b22; border:1px solid #21262d; border-radius:4px; padding:3px 8px; }
</style>
""", unsafe_allow_html=True)


# ── API client ────────────────────────────────────────────────────────────────

class InvestigationClient:
    def __init__(self, base_url: str, timeout: int = REQUEST_TIMEOUT):
        self.base_url = base_url
        self.timeout  = timeout

    def investigate(self, query: str, trace_id: str, case_id: str) -> dict:
        r = requests.post(
            f"{self.base_url}/api/Investigation/query",
            json={"traceId": trace_id, "caseId": case_id,
                  "query": query, "context": {}, "userId": "investicore-ui"},
            headers={"X-Correlation-ID": trace_id},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def health_check(self) -> bool:
        try:
            return requests.get(f"{self.base_url}/health", timeout=5).ok
        except Exception:
            return False

@st.cache_resource
def get_client():
    return InvestigationClient(INVESTIGATION_URL)

def _conf_color(c: float) -> str:
    return "#3fb950" if c >= 0.8 else "#d29922" if c >= 0.5 else "#f85149"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Connection")
    if get_client().health_check():
        st.success("Investigation Service — online")
    else:
        st.error("Unreachable")
        st.caption(f"`{INVESTIGATION_URL}`")
    if IS_DEV:
        st.divider()
        st.caption(f"URL: `{INVESTIGATION_URL}`")
        st.caption(f"Env: `{APP_ENV}`")


# ── Header ────────────────────────────────────────────────────────────────────
dev_badge = ""
if IS_DEV:
    dev_badge = '<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.58rem;background:#1c1a00;color:#d29922;border:1px solid #3d3400;border-radius:3px;padding:2px 7px;margin-left:10px;vertical-align:middle;letter-spacing:0.06em;">DEV</span>'

st.markdown(f"""
<div style="display:flex;align-items:baseline;gap:14px;margin-bottom:5px;">
    <span style="font-family:'IBM Plex Mono',monospace;font-size:1.5rem;font-weight:600;color:#58a6ff;letter-spacing:-0.02em;">InvestiCore</span>
    <span style="font-size:0.7rem;color:#484f58;letter-spacing:0.18em;text-transform:uppercase;">Kubernetes Investigation Platform</span>
    {dev_badge}
</div>
<div class="ic-divider"></div>
""", unsafe_allow_html=True)


# ── Query input ───────────────────────────────────────────────────────────────
st.markdown('<p style="font-family:\'IBM Plex Mono\',monospace;font-size:0.65rem;font-weight:600;letter-spacing:0.2em;text-transform:uppercase;color:#484f58;margin-bottom:7px;margin-top:0;">Investigation Query</p>', unsafe_allow_html=True)

query = st.text_area(
    label="query",
    height=115,
    placeholder="Describe the problem in plain English…\ne.g.  Why is payment-service crashing?\ne.g.  What's causing high memory in the auth namespace?",
    label_visibility="collapsed",
    disabled=st.session_state.loading,
)

st.markdown("""
<div class="ic-chips">
    <span class="ic-chip">Why is &lt;service&gt; crashing?</span>
    <span class="ic-chip">What's causing high CPU in &lt;namespace&gt;?</span>
    <span class="ic-chip">Why did &lt;deployment&gt; fail to start?</span>
    <span class="ic-chip">Why are pods restarting in &lt;namespace&gt;?</span>
    <span class="ic-chip">What's wrong with &lt;service&gt;?</span>
</div>
""", unsafe_allow_html=True)


# ── Buttons ───────────────────────────────────────────────────────────────────
col_run, col_clear, _ = st.columns([1.1, 0.75, 5])

with col_run:
    run_clicked = st.button(
        "▶  Investigate",
        use_container_width=True,
        disabled=st.session_state.loading,
        type="primary",
        key="btn_run",
    )

with col_clear:
    if st.button("Clear", use_container_width=True,
                 disabled=st.session_state.loading,
                 type="secondary",
                 key="btn_clear"):
        st.session_state.update(result=None, error=None, trace_id=None)
        st.rerun()


# ── Submit ────────────────────────────────────────────────────────────────────
if run_clicked and not st.session_state.loading:
    if not query.strip():
        st.warning("Please describe what you want to investigate.")
    else:
        trace_id = str(uuid.uuid4())
        case_id  = str(uuid.uuid4())
        st.session_state.update(loading=True, error=None, result=None, trace_id=trace_id)

        with st.spinner("Investigating…"):
            try:
                st.session_state.result = get_client().investigate(query.strip(), trace_id, case_id)
            except requests.exceptions.ConnectionError:
                st.session_state.error = f"Cannot reach Investigation Service at `{INVESTIGATION_URL}`."
            except requests.exceptions.Timeout:
                st.session_state.error = f"Timed out after {REQUEST_TIMEOUT}s. Check service logs."
            except requests.exceptions.HTTPError as e:
                code = e.response.status_code if e.response is not None else "?"
                st.session_state.error = f"Service returned HTTP {code}: {e}"
            except Exception as e:
                st.session_state.error = f"{type(e).__name__}: {e}"

        st.session_state.loading = False
        st.rerun()


# ── Output ────────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)

if st.session_state.error:
    trace = f'<div class="ic-err-trace">traceId: {st.session_state.trace_id}</div>' if st.session_state.trace_id else ""
    st.markdown(f"""
    <div class="ic-err">
        <div class="ic-err-label">Investigation failed</div>
        <div class="ic-err-msg">{st.session_state.error}</div>
        {trace}
    </div>""", unsafe_allow_html=True)

elif st.session_state.result:
    data       = st.session_state.result
    result     = data.get("result") or {}
    tool_calls = data.get("toolCalls") or []
    status     = data.get("status", "Unknown")
    sc         = status if status in ("Success", "Failed", "Partial") else "Failed"

    st.markdown(f"""
    <div class="ic-meta">
        <span class="ic-pill {sc}">{status}</span>
        <span class="ic-kv">trace <span>{data.get('traceId','—')}</span></span>
        <span class="ic-kv">case <span>{data.get('caseId','—')}</span></span>
        <span class="ic-kv">duration <span>{data.get('durationMs',0):,}ms</span></span>
    </div>""", unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2], gap="large")

    with col_l:
        root_cause = result.get("rootCause") or data.get("summary") or "No root cause identified."
        st.markdown(f'<div class="ic-card"><div class="ic-label">Root Cause</div><div class="ic-root-cause">{root_cause}</div></div>', unsafe_allow_html=True)

        conf = float(result.get("confidence") or 0.0)
        col  = _conf_color(conf)
        st.markdown(f"""
        <div class="ic-card">
            <div class="ic-label">Confidence</div>
            <div class="ic-conf-row">
                <div class="ic-conf-track"><div class="ic-conf-fill" style="width:{int(conf*100)}%;background:{col};"></div></div>
                <span class="ic-conf-pct" style="color:{col};">{int(conf*100)}%</span>
            </div>
        </div>""", unsafe_allow_html=True)

        evidence = result.get("evidence") or []
        if evidence:
            rows = "".join(f'<div class="ic-row"><span class="ic-dot">●</span><span>{e}</span></div>' for e in evidence)
            st.markdown(f'<div class="ic-card"><div class="ic-label">Evidence</div>{rows}</div>', unsafe_allow_html=True)

        actions = result.get("recommendedActions") or []
        if actions:
            rows = "".join(f'<div class="ic-row"><span class="ic-num">{i+1:02d}</span><span>{a}</span></div>' for i, a in enumerate(actions))
            st.markdown(f'<div class="ic-card"><div class="ic-label">Recommended Actions</div>{rows}</div>', unsafe_allow_html=True)

    with col_r:
        if tool_calls:
            steps = ""
            for tc in tool_calls:
                name = tc.get("toolName", "unknown")
                s    = (tc.get("status") or "unknown").lower()
                cls  = s if s in ("success", "failed", "timeout") else "failed"
                dur  = tc.get("durationMs", 0)
                steps += f"""<div class="ic-step">
                    <div class="ic-step-dot {cls}"></div>
                    <div class="ic-step-info"><span class="ic-step-name">{name}</span><span class="ic-step-dur">{dur:,}ms</span></div>
                    <span class="ic-badge {cls}">{s}</span>
                </div>"""
            st.markdown(f'<div class="ic-card"><div class="ic-label">Tool Execution</div><div class="ic-timeline">{steps}</div></div>', unsafe_allow_html=True)

        tools_used = result.get("toolsUsed") or []
        if tools_used:
            rows = "".join(f'<div class="ic-row"><span class="ic-dot" style="color:#30363d;">◆</span><span class="ic-tool-name">{t}</span></div>' for t in tools_used)
            st.markdown(f'<div class="ic-card"><div class="ic-label">Tools Used</div>{rows}</div>', unsafe_allow_html=True)

        if IS_DEV:
            with st.expander("Raw JSON"):
                st.code(json.dumps(data, indent=2, default=str), language="json")