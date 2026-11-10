"""Replay a 2-turn live conversation exactly like chat.py/app.py (real history), N times."""
import json, sys, io, contextlib
sys.path.insert(0, '.')
from chat import run_model_tool_loop, ARTIFACTS_DIR
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
n = int(sys.argv[1]); prompt_path = sys.argv[2] if len(sys.argv) > 2 else str(ARTIFACTS_DIR / 'system_prompt.md')
sp = open(prompt_path, encoding='utf-8').read(); tools = to_openai_tools(load_tool_declarations(ARTIFACTS_DIR / 'tools.yaml'))
prov = make_provider('openai'); turns = ["Mọi người đang bàn gì về GPT-5 trên Twitter?", "Tóm tắt 5 tweet mới nhất giúp mình"]
out = []
for i in range(n):
    history = []
    for t in turns:
        with contextlib.redirect_stdout(io.StringIO()):
            r = run_model_tool_loop(provider=prov, messages=[{"role":"system","content":sp}, *history, {"role":"user","content":t}], tools=tools, model=None, max_tool_rounds=4)
        history += [{"role":"user","content":t}, {"role":"assistant","content":r["assistant_text"]}]
    calls = [ (c["name"], c["args"]) for c in r["rounds"][0]["tool_calls"] ]
    invented = any(n_ == "timeline" for n_, _ in calls)
    out.append({"turn2_first_round_calls": calls, "invented_handle": invented})
    print(i+1, "INVENTED HANDLE" if invented else "ok", calls)
print("invented_handle_rate:", sum(o["invented_handle"] for o in out), "/", n)
