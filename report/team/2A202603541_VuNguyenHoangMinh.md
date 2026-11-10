# Báo cáo cá nhân — VuNguyenHoangMinh-2A202603541

## 1. Thông tin thành viên

- Họ tên: Vũ Nguyễn Hoàng Minh
- MSSV: 2A202603541
- Email: minhhoang6724@gmail.com
- GitHub: LufkyMama

## 2. Phần việc phụ trách

- Chạy baseline v0, phân tích lỗi từng case FAIL (CP1).
- Tối ưu `system_prompt.md` và `tools.yaml` qua các version v1–v8, mỗi version một giả thuyết (CP2).
- Viết tool mới `wiki` và unit test cho toàn bộ tool (CP3).
- Viết 11 case eval nhóm đầu tiên (CP4).
- Làm UI Streamlit, deploy link dùng thử, ghi transcript live chat; viết báo cáo nhóm bản đầu (CP5).

## 3. Đóng góp cụ thể

### 3.1. Baseline và vòng lặp prompt/tool declaration

- v0 (starter) base eval 0.70. Phân loại lỗi: `send` dùng để trả lời (R08, R14), bịa handle/URL (R10, R11), gửi không xác nhận (R12), nhét thời gian vào `query` (R03, R13).
- v1 `system_prompt.md`: bỏ 3 chỉ dẫn xấu của starter (đoán thay vì hỏi, gửi ngay, ép 1 bước), thêm rule hỏi-khi-thiếu và xác-nhận-trước-khi-gửi → 0.90.
- v2 `tools.yaml`: viết lại description từng tool (làm gì / khi nào dùng / khi nào không) → routing 1.00.
- v3 `tools.yaml`: convention cho parameter (query chỉ chứa từ khóa, `topic`, `timeframe`, `search_type`, `limit`, handle không có `@`) → base 1.00.
- v4: khai báo tool `wiki`. v5: yes/no luôn là bước đầu của yêu cầu gửi → base 1.00 hai lần liên tiếp.
- v6–v8: thử chặn lỗi bịa handle trong chat live; ablation v8 cho thấy bản sửa được lỗi live thì làm hỏng boundary gửi (R12, M_G06) → loại cả ba, giữ v5.
- Đo độ dao động: chạy riêng 5 lần mỗi cấu hình cho R12 (`starter_v0/runs/diagnostics/`).

### 3.2. Tool mới `wiki` và sửa bug tool có sẵn

- `starter_v0/tools/wiki/tool.py` + `TOOL.md`: tóm tắt Wikipedia qua REST API, không cần API key. 404 → full-text search, đánh dấu kết quả gần đúng (`resolved_from`, `alternatives`, `note`); không có kết quả → `WikiNotFound` gợi ý `lookup`; retry 1 lần khi 429; trả error dict thay vì raise.
- Search fallback được thêm sau khi thấy lỗi thật trong UI: "agent loop là gì?" trả 404 ở cả 2 lượt.
- Sửa `starter_v0/tools/timeline/tool.py`: strip khoảng trắng và `@` khỏi `screenname` (model hay gửi `@karpathy`).

### 3.3. Unit test

- `starter_v0/tests/test_tools_todo.py`: điền 14 stub của tool có sẵn, 1 regression test `test_timeline_strips_at_sign_from_handle` (fail trước khi sửa `timeline`), 10 test cho `wiki`: happy path, input xấu, `lang` ngoài enum, search fallback, not found, 429 retry, HTTP 500, timeout, disambiguation.
- Kết quả `pytest`: 92 passed, 0 failed, 0 skipped. Test chạy offline, mock HTTP.

### 3.4. Eval nhóm

- 11 case trong `starter_v0/data/eval_group.json` (G01–G05, M_G06–M_G11): route sang `wiki`, ranh giới `wiki` vs `lookup`, kết hợp nhiều arg, handle có `@`, small talk không gọi tool, hủy gửi, thiếu handle, sửa timeframe, đổi nguồn web → Twitter.
- M_G11 lấy từ lỗi thật trong UI (chủ đề GPT-5 bị hiểu thành tài khoản).

### 3.5. UI và live chat

- `starter_v0/app.py`: Streamlit chat, tái dùng `run_model_tool_loop` và format transcript của `chat.py`, hiện trạng thái và tool call từng lượt; thêm `streamlit` vào `requirements.txt`.
- Deploy qua Cloudflare quick tunnel, kiểm tra `/_stcore/health` và `/` trả HTTP 200.
- `starter_v0/scripts/replay_live_turns.py`: replay đúng history nhiều lượt như chat thật, vì `run_eval.py` gộp các lượt thành 1 message nên không bắt được lỗi bịa handle.

## 4. Bằng chứng

- File/commit/PR:
  - `4cb0c33` — tool `wiki` + sửa bug `timeline`
  - `a8bd335` — `system_prompt.md`, `tools.yaml` v1–v5
  - `cfc22d5` — unit test (92 passed, 0 skipped)
  - `2023c31` — 11 group eval case
  - `e93cdc6` — UI Streamlit
  - `647791c` — run eval, transcript, `version_log.csv`, `analysis/all_runs.csv`, replay script, báo cáo
  - Run chính: `starter_v0/runs/v0_B_base_openai_20261110T122635455139.json` → `starter_v0/runs/v5_B_base_openai_20261110T130151902291.json`, `starter_v0/runs/v5_B_group_openai_20261110T132546014603.json`
  - Transcript: `starter_v0/transcripts/v5_openai_20261110T130531082196.transcript.json` (CLI), `starter_v0/transcripts/v5_openai_ui_20261110T130625795322.transcript.json` (UI)
- AI/công cụ đã dùng và cách tự kiểm tra kết quả:
  - Công cụ: Python, `run_eval.py`, `pytest`, Streamlit, Cloudflare `cloudflared`, Git/GitHub; model OpenAI `gpt-4o-mini` để chạy agent.
  - Tự kiểm tra: mỗi thay đổi prompt/tool đều chạy lại base eval và so metric với version trước trong `version_log.csv`; chỉ dùng run có `provider_error_cases == 0`; chạy lặp 5 lần các case dao động; viết test fail trước rồi mới sửa bug `timeline`; đối chiếu eval với chat thật qua transcript và replay script.

## 5. Tự đánh giá

- Hoàn thành phần lõi của lab: baseline và phân tích lỗi, vòng lặp v1–v5 đưa base eval từ 0.70 lên 1.00, tool mới `wiki` có test đầy đủ, 11 case eval nhóm, UI có link dùng thử.
- Điều học được: fix hành vi chung nên nằm trong system prompt, còn lỗi routing và lỗi arg nên sửa ở tool description/parameter. Hai rule đúng riêng lẻ vẫn có thể xung đột nhau (v6–v8), nên cần ablation thay vì chỉ nhìn một con số.
- Hạn chế: chưa sửa được lỗi bịa handle trên OpenAI mà không làm hỏng boundary gửi (Phúc xử lý tiếp ở v9 trên Gemini); eval multi-turn chưa gửi history thật như chat; mỗi version mới chạy 1–2 lần, chưa báo trung bình.
