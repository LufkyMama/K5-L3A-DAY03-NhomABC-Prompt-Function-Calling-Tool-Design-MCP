"""Streamlit UI for the Research Agent.

Reuses the multi-round tool loop and transcript format of chat.py (no duplicated agent logic).
Run:  streamlit run app.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from typing import Any

import streamlit as st

# chat.py prints tool calls with emoji; Windows consoles (cp125x) would crash on that.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from chat import (  # noqa: E402  (after stdout fix)
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider  # noqa: E402
from tools import load_tool_declarations, to_openai_tools  # noqa: E402
from versioning import artifact_version_dict, build_artifact_version  # noqa: E402

PROVIDERS = ["openai", "openrouter", "anthropic", "gemini", "ollama"]
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="centered")


@st.cache_resource(show_spinner=False)
def load_agent_config() -> tuple[str, list[dict[str, Any]], list[str]]:
    declarations = load_tool_declarations(TOOLS_PATH)
    return (
        SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
        to_openai_tools(declarations),
        [item["name"] for item in declarations],
    )


def new_transcript(provider_name: str, model: str | None, version: str) -> dict[str, Any]:
    artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), "ui", datetime.now().strftime("%Y%m%dT%H%M%S%f")])
    return {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model,
        "source": "streamlit_ui",
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def reset_session() -> None:
    for key in ("history", "messages", "transcript"):
        st.session_state.pop(key, None)


# ---------------- sidebar ----------------
system_prompt, openai_tools, tool_names = load_agent_config()
with st.sidebar:
    st.header("Cấu hình")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0, on_change=reset_session)
    model_override = st.text_input("Model (trống = mặc định)", value="", on_change=reset_session).strip() or None
    version = st.text_input("Version label", value="v5", on_change=reset_session).strip() or "ui"
    st.caption("Tools: " + ", ".join(f"`{name}`" for name in tool_names))
    if st.button("Cuộc hội thoại mới"):
        reset_session()
        st.rerun()

try:
    provider = make_provider(provider_name)
except Exception as exc:  # unknown provider / bad config
    st.error(f"Không khởi tạo được provider: {exc}")
    st.stop()
model = model_override or getattr(provider, "default_model", None)

if "transcript" not in st.session_state:
    st.session_state.transcript = new_transcript(provider_name, model, version)
    st.session_state.history = []   # user/assistant pairs sent back to the model
    st.session_state.messages = []  # what the UI renders

transcript_path = ROOT / "transcripts" / f"{st.session_state.transcript['transcript_id']}.transcript.json"

# ---------------- main ----------------
st.title("🔎 Research Agent")
st.caption(
    f"Tìm tin web, tweet theo tài khoản/chủ đề, đọc URL, tra Wikipedia, tóm tắt digest. "
    f"Model: `{model}` · artifact `{st.session_state.transcript['artifact_version']}`"
)

STATUS_LABEL = {
    "answered": ("✅", "Đã trả lời"),
    "waiting_for_user": ("❓", "Agent đang chờ bạn trả lời"),
    "max_tool_rounds": ("⚠️", "Dừng vì quá số vòng tool"),
    "provider_error": ("❌", "Lỗi provider"),
}


def render_message(msg: dict[str, Any]) -> None:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        events = msg.get("tool_events") or []
        if msg["role"] == "assistant" and (events or msg.get("status")):
            icon, label = STATUS_LABEL.get(msg.get("status", ""), ("ℹ️", msg.get("status", "")))
            st.caption(f"{icon} {label} · {len(events)} tool call(s)")
            for event in events:
                with st.expander(f"🔧 {event.get('tool')}"):
                    st.json({"args": event.get("args"), "result": event.get("result")}, expanded=False)


for message in st.session_state.messages:
    render_message(message)

if prompt := st.chat_input("Hỏi agent, ví dụ: Tin tức AI hôm nay có gì nổi bật?"):
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    render_message(user_msg)

    turn_record: dict[str, Any] = {
        "turn_index": len(st.session_state.transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": prompt,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, HISTORY_WINDOW),
        {"role": "user", "content": prompt},
    ]
    with st.spinner("Agent đang xử lý..."):
        try:
            result = run_model_tool_loop(
                provider=provider, messages=messages, tools=openai_tools,
                model=model_override, max_tool_rounds=MAX_TOOL_ROUNDS,
            )
            turn_record.update(result)
            answer = result["assistant_text"] or "(không có nội dung)"
            st.session_state.history += [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer},
            ]
        except Exception as exc:
            turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
            answer = f"Lỗi khi gọi model: `{turn_record['error']}`"

    turn_record["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn_record)
    write_transcript(transcript_path, st.session_state.transcript)

    assistant_msg = {
        "role": "assistant", "content": answer,
        "status": turn_record["status"], "tool_events": turn_record.get("tool_events", []),
    }
    st.session_state.messages.append(assistant_msg)
    render_message(assistant_msg)

if st.session_state.transcript["turns"]:
    st.sidebar.caption(f"Transcript: `{transcript_path.relative_to(ROOT)}`")
