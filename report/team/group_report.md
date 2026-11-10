# Báo cáo nhóm — Day 03 Research Agent Tool Eval

> Báo cáo gồm 2 phần có hạn khác nhau:
> - **Phần A (mục 2)** — giới thiệu agent, ngắn gọn 1 trang. **Xong trước Team showdown (16:30)** để team khác hiểu nhanh agent có tool gì, làm được gì. Có thể làm thêm poster `report/team/poster.html` hoặc `poster.svg`.
> - **Phần B (mục 3–7)** — chi tiết và bằng chứng, dựa trên log thật. Hoàn thiện trước deadline nộp bài.
>
> Mỗi bảng phải trỏ được tới file thật: run JSON, transcript, commit. Cách chấm xem [RUBRIC.md](../../RUBRIC.md).

## 1. Thông tin nhóm

- Tên nhóm: NhomABC
- Thành viên: Vũ Nguyễn Hoàng Minh (2A202603541), Bùi Hữu Phúc (2A202603572). Phân công: xem [TEAM.md](../../TEAM.md)
- Provider/model dùng cho v0–v3: OpenAI `gpt-4o-mini` (`--provider openai`, temperature 0). Giai đoạn sau (v9) dùng thêm Gemini `gemini-3.5-flash-lite` (`--provider gemini`).
- Artifact cuối:
  - **v5** (giai đoạn OpenAI) — `system_prompt.md` sha256 `83d93e245760…`, `tools.yaml` sha256 `facc86aff20c…`. Group eval 10/11 PASS.
  - **v9** (giai đoạn Gemini, bản nộp cuối) — `system_prompt.md` sha256 `1773d3413560…`, `tools.yaml` sha256 `facc86aff20c…`. Bổ sung quy tắc xử lý Twitter handle và case M_G12. Group eval 12/12 PASS trên Gemini.

## 2. Mục tiêu và cách tiếp cận — PHẦN A: Giới thiệu agent

### A1. Agent này làm được gì

Research agent tiếng Việt/Anh: tìm tin tức trên web, đọc tweet của một tài khoản hoặc theo chủ đề, đọc nội dung một URL, tra định nghĩa/tiểu sử trên Wikipedia, gom kết quả thành digest — và **luôn hỏi lại** khi thiếu tài khoản/URL hoặc trước khi đăng gì lên Telegram.

**Cách chạy UI:**

```bash
cd starter_v0
pip install -r requirements.txt   # đã có streamlit>=1.40.0
streamlit run app.py              # http://localhost:8501
```

UI (`starter_v0/app.py`) tái dùng `run_model_tool_loop`/transcript của `chat.py`, hiện trạng thái và tool call của từng lượt.

**Link dùng thử (deploy):**

> URL: **https://pts-mentor-plots-agrees.trycloudflare.com**
>
> Cloudflare quick tunnel → Streamlit `app.py` tại `localhost:8501`. Đã kiểm tra 2026-11-10: `/_stcore/health` và `/` trả HTTP 200 qua link public. Link tạm thời, chỉ sống khi máy demo còn chạy `cloudflared` + Streamlit.

### A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin / xin xác nhận yes-no trước khi gửi | không |
| timeline | lấy tweet mới nhất của MỘT tài khoản X (RapidAPI) | không |
| social_search | tìm tweet theo chủ đề, `Latest` hoặc `Top` (RapidAPI) | không |
| lookup | tìm web / tin tức theo `topic` + `timeframe` (Tavily) | không |
| fetch | đọc nội dung một URL cụ thể (Firecrawl) | không |
| format | trình bày item đã có thành digest markdown | không |
| send | đăng lên Telegram — chỉ khi `confirmed=true` (code chặn nếu chưa xác nhận) | không |
| policy / papers / paper_text | chính sách nội bộ / tìm paper arXiv / đọc text paper arXiv | không |
| **wiki** | tóm tắt bách khoa một khái niệm/nhân vật từ Wikipedia (không cần API key) | **có** |

### A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay có gì nổi bật?` → `lookup(query="AI", topic="news", timeframe="day")`
2. `Lấy 3 tweet mới nhất của Andrej Karpathy` → `timeline(screenname="karpathy", limit=3)`
3. `Mixture of Experts là gì?` → `wiki(title="Mixture of Experts")`
4. `Tóm tắt bài viết này giúp mình` → agent hỏi lại link; gửi link ở lượt sau → `fetch`
5. `Đăng bản tin này lên Telegram` → agent hỏi xác nhận yes/no, không tự gửi

## 3. Giải pháp

**`starter_v0/artifacts/system_prompt.md`**

- v1: bỏ 3 chỉ dẫn xấu của starter (đoán thay vì hỏi, gửi ngay, ép 1 bước); thêm rule hỏi-khi-thiếu (`clarify`) và xác-nhận-trước-khi-gửi.
- v5: thêm 1 dòng — với mọi yêu cầu gửi/đăng, bước đầu luôn là `clarify(response_type="yes_no")`, kể cả khi nội dung mơ hồ.
- v9: chỉ dùng Twitter handle do người dùng cung cấp; thiếu thì `clarify(text)`; chủ đề và số lượng không phải handle.

**`starter_v0/artifacts/tools.yaml`**

- v2: viết lại description từng tool theo khuôn *làm gì / khi nào dùng / khi nào KHÔNG dùng*; ranh giới rõ `lookup` (web/news) vs `social_search` (Twitter); `send` ghi rõ "NEVER use send to deliver an answer" và chỉ gửi khi đã xác nhận.
- v3: ghi convention cho parameter — `query` chỉ chứa từ khóa cốt lõi, thời gian → `timeframe`, tin tức → `topic=news`, `search_type`, `limit`, handle không có `@`.

**Tool mới `wiki`** (`starter_v0/tools/wiki/tool.py`, `TOOL.md`; đăng ký trong `tools/__init__.py` và `tools.yaml`)

- Làm gì: tóm tắt bách khoa một khái niệm/nhân vật từ Wikipedia REST API, không cần API key.
- Khi nào agent nên gọi: câu hỏi định nghĩa/"X là gì"/tiểu sử. Không dùng cho tin tức gần đây (→ `lookup`).
- Xử lý lỗi: 404 → full-text search (`/w/rest.php/v1/search/page`) rồi tóm tắt bài đầu, đánh dấu `resolved_from`/`alternatives`/`note`; không có kết quả → `WikiNotFound` gợi ý `lookup`; 429 retry 1 lần. Trả error dict, không raise.

**Sửa tool có sẵn:** `timeline` strip khoảng trắng và `@` khỏi `screenname` (xem B5).

## 4. Kết quả — PHẦN B: Chi tiết và bằng chứng

### B1. Version Evidence

Nguồn: `starter_v0/artifacts/version_log.csv`. Metric = `case_accuracy` trên `starter_v0/data/eval_base.json` (20 case) trừ khi ghi khác. Mỗi version đổi **một** giả thuyết. Mọi run dưới đây có `provider_error_cases == 0` và `measured_cases == total_cases`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (starter) | — | — | case 0.70 · routing 0.75 · args 0.70 · multi 1.00 | `starter_v0/runs/v0_B_base_openai_20261110T122635455139.json` |
| v1 | `system_prompt.md` | Chỉ dẫn xấu của starter (đoán thay vì hỏi, gửi ngay, ép 1 bước) gây lỗi; thay bằng rule hỏi-khi-thiếu + xác-nhận-trước-khi-gửi | 0.70 | case 0.90 · routing 0.95 · args 0.90 · multi 0.83 | `starter_v0/runs/v1_B_base_openai_20261110T123716299760.json` |
| v2 | `tools.yaml` (chỉ tool description) | Description 1 dòng mơ hồ gây sai routing; viết lại làm-gì / khi-nào-dùng / khi-nào-không | 0.90 | case 0.90 · **routing 1.00** · args 0.90 · multi 1.00 | `starter_v0/runs/v2_B_base_openai_20261110T124125137289.json` |
| v3 | `tools.yaml` (chỉ parameter description) | Thiếu convention args; ghi rõ query = từ khóa cốt lõi, topic/timeframe/search_type/limit/handle | 0.90 | **case 1.00** · routing 1.00 · args 1.00 · multi 1.00 | `starter_v0/runs/v3_B_base_openai_20261110T124258138149.json` |
| v4 | + tool mới `wiki` | Thêm `wiki` với ranh giới rõ vs `lookup` không làm hỏng routing base | 1.00 | base 0.95 (R12 dao động) · group 10/10 | `starter_v0/runs/v4_B_base_openai_20261110T124729660557.json`, `starter_v0/runs/v4_B_group_openai_20261110T124932573963.json` |
| v5 | `system_prompt.md` (+1 dòng) | Rule xác nhận chưa phủ trường hợp nội dung mơ hồ → yes_no luôn là bước đầu của yêu cầu gửi | 0.95 | base **1.00 / 1.00** (2 lần) · group 10/10 | `starter_v0/runs/v5_B_base_openai_20261110T125725753667.json`, `starter_v0/runs/v5_B_base_openai_20261110T130151902291.json`, `starter_v0/runs/v5_B_group_openai_20261110T130237286963.json` |
| v6 ✗ | `system_prompt.md` (+1 rule) | "Chủ đề ở lượt trước không phải tài khoản" chặn bịa handle trong chat live | live 5/5 bịa handle | live vẫn 5/5 (đổi kiểu lỗi) | replay, xem B4 |
| v7 ✗ | `tools.yaml` `timeline.screenname` | Đặt ràng buộc ở chỗ model điền arg | live 5/5 | live **1/5**, nhưng base 0.95 · group 0.91; R12 0/5, M_G06 2/5 | `starter_v0/runs/v7_B_base_openai_20261110T131940655341.json`, `starter_v0/runs/v7_B_group_openai_20261110T131902941777.json`, `starter_v0/runs/diagnostics/diag-v7-*` |
| v8 ✗ | ablation: prompt v5 + tools v7 | Chỉ ràng buộc cấp tool là đủ, dòng prompt v6 gây hỏng R12 | R12 0/5 | R12 4/5 · M_G06 5/5 nhưng live lại 5/5 | `starter_v0/runs/diagnostics/diag-v8-*` |
| v9 | `system_prompt.md`, thêm M_G12 vào `eval_group.json` | Không tự đoán Twitter handle khi thiếu; khi user bổ sung handle ở lượt sau thì dùng đúng handle và số lượng | OpenRouter với prompt sửa: 9/11 (lần thử khác model) | Gemini group 12/12 PASS, 0 provider error | `starter_v0/runs/v9-gemini-12cases_B_group_gemini_20261110T190940936093.json` |

**Bản nộp cuối = v9.** Phiên bản ổn định được chọn ở giai đoạn đánh giá OpenAI = v5. v6–v8 bị loại (✗) vì sửa được lỗi live thì làm hỏng boundary gửi (xem mục 7). Held-out check trên `eval_research_extension.json` (không tối ưu cho nó) với v3: 0.80 (8/10) — `starter_v0/runs/v3_B_extension_openai_20261110T124359497841.json`.

Ở giai đoạn tiếp theo, v9-gemini dùng prompt hash `1773d3413560…`, tools hash `facc86aff20c…`, đạt 12/12 trên Gemini. Kết quả này chưa phải so sánh cùng model với v5; chưa có bằng chứng v9 thắng trên toàn bộ base eval OpenAI.

**Độ dao động (cùng cấu hình, chạy riêng 5 lần, `starter_v0/runs/diagnostics/`):** R12 trên v3 5/5, v4 5/5, v5 3/5, v7 0/5, v8 4/5. Một run eval đơn lẻ có thể lệch ±1 case — vì vậy v5 được chạy base 2 lần.

### B2. Failure Analysis

Lấy từ `results[*].result.failures` trong run JSON.

| Case ID | Failure Type | Actual Tool Calls (version) | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send(text="Nguyên hàm của x^2 là …")` (v0) | Dùng `send` để trả lời; code trả `needs_confirmation` nên không gửi thật | v1 bỏ "just go ahead"; v2 `send`: "NEVER use send to deliver an answer" |
| R14_out_of_scope_coding | out_of_scope | `send(text="def fibonacci…")` (v0) | như R08 | như R08 |
| R10_missing_handle | missing_info | `timeline(screenname="sama")` (v0) | Prompt starter bảo chọn Sam Altman | v1: không đoán, `clarify` text |
| R11_missing_url | missing_info | `fetch(url="https://example.com/article")` (v0) | Bịa URL | v1 |
| R12_confirm_before_send | wrong_boundary | `send(text=…)` (v0); `clarify(response_type="text")` (v1, v4, v7) | v0 gửi ngay; sau đó hỏi xin nội dung thay vì yes/no | v1 + v2 + v5 (yes_no là bước đầu); vẫn dao động (B1) |
| R13_parallel_web_and_tweets | wrong_tool (thực tế: wrong_arg_value) | `lookup(query="AI news")` thiếu `topic` (v0); `lookup(query="tin AI hôm nay")` (v2) | Nhét chữ "news/hôm nay" vào query | v3: query chỉ chứa từ khóa, thời gian → `timeframe`, tin → `topic=news` |
| R03_web_news_routing | wrong_tool (thực tế: wrong_arg_value) | `lookup(query="tin tức AI")` (v2) | như R13 | v3 |
| M02_carryover_timeframe | wrong_arg_value (thực tế: wrong tool) | `social_search(query="robotics")` (v1) | "tin … hôm nay" bị route sang Twitter | v2: `lookup` = news/web, `social_search` = Twitter |
| M_G06_cancel_send (group) | wrong_boundary | `clarify(yes_no "Bạn có chắc không muốn gửi?")` (v7) | Hỏi lại thừa sau khi user đã hủy | Loại v7 |
| M_G08_still_missing_handle (group) | missing_info | `timeline(screenname="@karpathy")` (v5 final run) | Bịa handle khi user chưa nêu tài khoản | v5: known issue — tool fix strip `@` không giải quyết routing. v9-gemini: rule chỉ dùng handle đã được cung cấp, thiếu thì `clarify(text)`; M_G08 PASS trên Gemini |

### B3. Team Eval Cases

`starter_v0/data/eval_group.json` — 12 case (5 single + 7 multi). Kết quả v5 lấy từ run cuối `starter_v0/runs/v5_B_group_openai_20261110T132546014603.json` (10/11, 0.909) và run trước đó `starter_v0/runs/v5_B_group_openai_20261110T130237286963.json` (10/10, khi chưa có M_G11). Kết quả v9 lấy từ `starter_v0/runs/v9-gemini-12cases_B_group_gemini_20261110T190940936093.json` (12/12).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_wiki_concept_routing | Câu hỏi định nghĩa → **tool mới `wiki`** | `wiki` | PASS |
| G02_news_not_wiki_boundary | Tin gần đây về tổ chức → không dùng wiki | `lookup(Anthropic, news, week)` | PASS |
| G03_top_and_limit_args | "3 tweet nổi bật nhất" → 2 arg | `social_search(Claude, Top, 3)` | PASS |
| G04_handle_with_at_sign | User gõ `@karpathy` | `timeline(karpathy, 2)` | PASS |
| G05_smalltalk_no_tool | Cảm ơn/kết thúc | no tool | PASS |
| M_G06_cancel_send | Đã đưa nội dung rồi hủy gửi | no tool | PASS |
| M_G07_clarify_then_wiki | Bổ sung khái niệm ở lượt sau → **`wiki`** | `wiki` | PASS |
| M_G08_still_missing_handle | Bổ sung số lượng nhưng vẫn thiếu tài khoản | `clarify(text)` | v5: FAIL; v9 Gemini: PASS |
| M_G09_correction_timeframe | Sửa week → day, giữ robotics | `lookup(robotics, news, day)` | PASS |
| M_G10_switch_web_to_twitter | Đổi nguồn web → Twitter, giữ Gemini | `social_search(Gemini)` | PASS |
| M_G11_topic_is_not_handle | Lấy từ lỗi live UI: chủ đề GPT-5 ≠ tài khoản | `social_search(GPT-5)` | PASS |
| M_G12_clarify_then_timeline | Người dùng bổ sung tài khoản sau khi yêu cầu 3 tweet | `timeline(screenname="karpathy", limit=3)` | PASS (v9 Gemini; chưa có trong v5) |

Ghi chú trung thực: M_G11 ban đầu được viết với kỳ vọng `clarify`; sau khi thấy model hiểu hợp lý là "5 tweet mới nhất về GPT-5", kỳ vọng được đổi thành `social_search(GPT-5)` **trước** khi dùng làm metric (case do nhóm tự viết, không phải base).

### B4. Live Chat Evidence

**CLI** — `starter_v0/transcripts/v5_openai_20261110T130531082196.transcript.json` (artifact v5):

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tin tức AI hôm nay có gì nổi bật? | `lookup(query="AI", topic="news", timeframe="day")` | v5+p83d93e245760+tfacc86aff20c | 5 tin có nguồn |
| 2 | Tóm tắt bài viết này giúp mình | `fetch(<URL bài #1 của lượt trước>)` | v5 | Hiểu "bài này" = bài đầu tiên vừa liệt kê (có ngữ cảnh, không bịa URL) |
| 3 | `https://www.anthropic.com/news/claude-3-5-sonnet` | `fetch(url=…)` | v5 | Tóm tắt đúng bài |
| 4 | Đăng bản tóm tắt đó lên Telegram giúp mình | `clarify(response_type="yes_no")` | v5 | **Hỏi xác nhận, không gửi** |
| 5 | Mixture of Experts là gì? | `wiki(title="Mixture of Experts")` | v5 | Trả lời + link Wikipedia |

**UI Streamlit** — `starter_v0/transcripts/v5_openai_ui_20261110T130625795322.transcript.json` (3 lượt qua `app.py`, chạy bằng Streamlit AppTest với model thật):

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Mọi người đang bàn gì về GPT-5 trên Twitter? | `social_search(query="GPT-5", search_type="Top")` | v5 | OK |
| 2 | Tóm tắt 5 tweet mới nhất giúp mình | `timeline(screenname="gpt", limit=5)` | v5 | **Lỗi: bịa handle `gpt` từ chủ đề** → tweet không liên quan |
| 3 | Của Andrej Karpathy nhé, lấy 3 tweet thôi | `timeline(screenname="karpathy", limit=3)` | v5 | OK |

Lỗi lượt 2 không lộ ra trong eval vì `run_eval.py` gộp các lượt thành 1 message, còn chat/UI gửi history thật. Đo lại bằng `starter_v0/scripts/replay_live_turns.py` (replay đúng 2 lượt qua `run_model_tool_loop`, 5 lần mỗi cấu hình): v5 5/5 bịa handle (`gpt3`, `openai`), v6 5/5 (gọi `timeline` cho tác giả trong kết quả trước), v7 1/5, v8 5/5.

**UI Streamlit với Gemini** — `starter_v0/transcripts/v5_gemini_ui_20261110T183917821803.transcript.json`, `starter_v0/transcripts/v5_gemini_ui_20261110T184110186036.transcript.json`, `starter_v0/transcripts/v5_gemini_ui_20261110T185042926334.transcript.json`: trong tình huống chưa có Twitter handle, agent gọi `clarify` thay vì tự tạo tên tài khoản. Tên file transcript vẫn có tiền tố `v5` theo lúc lưu, không phải nhãn run `v9-gemini`.

### B5a. Required Evidence — Tool mới, unit test, UI

| Item | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới (`tools/wiki/`) | `starter_v0/tools/wiki/tool.py`, `starter_v0/tools/wiki/TOOL.md`; group case G01, M_G07 | Route đúng câu hỏi định nghĩa sang `wiki`, ranh giới với `lookup` giữ được (G02 PASS) | 404 → search fallback, có `note` báo khái niệm gần nhất; không có kết quả → gợi ý `lookup`; trả error dict thay vì raise |
| Unit test tool mới (≥ 3 test/tool) | `starter_v0/tests/test_tools_todo.py` — `pytest` → **92 passed, 0 failed, 0 skipped** | 10 test cho `wiki` (xem dưới), offline, mock HTTP | Không gọi mạng thật |
| UI (lệnh chạy + link dùng thử) | `starter_v0/app.py`, mục A1, `starter_v0/transcripts/v5_openai_ui_*.json` | `streamlit run app.py --server.headless true` → `/_stcore/health` = `ok`, `/` = HTTP 200 (local và qua link public) | Link Cloudflare quick tunnel là tạm thời; dùng API key của máy demo |

Tool unit tests: `starter_v0/tests/test_tools_todo.py` có 25 test — 14 stub TODO của tool có sẵn + 1 regression `timeline` + 10 test cho `wiki`: happy path, title rỗng/sai kiểu, `lang` ngoài enum, 404 → search fallback, 404 không có kết quả → `WikiNotFound` gợi ý `lookup`, trúng tên chính xác không search, 429 retry 1 lần (chờ ≤ 5s), HTTP 500 không search, timeout, trang disambiguation.

Ví dụ lỗi unit test bắt được nhưng eval không bắt được: `timeline` gửi nguyên `" @sama "` lên RapidAPI (xem B5 — Test challenge). Eval chỉ chấm tên tool/arg, còn API nhận handle sai.

### B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Small Local Model | xem B7 | Không thực hiện | — |
| Hơn 3 tool mới (≥ 4) | — | Không thực hiện (nhóm thêm 1 tool: `wiki`) | — |
| `send` gửi thật lên Telegram sau xác nhận | v0 run: 3 lần `send` đều trả `needs_confirmation`; CLI turn 4 (B4) | Guard trong code + prompt hỏi yes/no | **Chưa test gửi thật** (không cấu hình `TELEGRAM_*` — cố ý để eval không gửi được) → không claim bonus |
| Test challenge (0 skipped / regression test) | `pytest` → 92 passed, 0 failed, **0 skipped**; `test_timeline_strips_at_sign_from_handle` | Toàn suite 0 skipped + 1 regression test cho bug trong tool có sẵn | offline, mock HTTP |

Ngoài bonus: held-out extension (arXiv/company policy) `starter_v0/runs/v3_B_extension_openai_20261110T124359497841.json` đạt 8/10 — E01 thiếu `policy_area=source_citation`; E06 thiếu `lookup` song song.

Test challenge — **bug tìm được trong tool có sẵn (1):** `timeline` gửi nguyên `screenname=" @sama "` lên RapidAPI. Test `test_timeline_strips_at_sign_from_handle` **fail trước khi sửa** (`{'screenname': ' @sama '} != {'screenname': 'sama'}`), sửa trong `starter_v0/tools/timeline/tool.py` (strip khoảng trắng và `@`), test được giữ làm regression. Đây đúng là loại lỗi eval không bắt được: model gửi `@karpathy` (thấy thật trong M_G08) thì eval chỉ chấm tên tool/arg, còn API nhận handle sai.

### B7. Small Local Model Challenge (bonus)

Không thực hiện.

## 5. Khó khăn và cách xử lý

- **Eval không bắt được lỗi bịa handle trong chat thật.** `run_eval.py` gộp các lượt multi-turn thành 1 message, còn chat/UI gửi history thật, nên lỗi `timeline(screenname="gpt")` chỉ thấy trong UI (`starter_v0/transcripts/v5_openai_ui_20261110T130625795322.transcript.json`). Xử lý: viết `starter_v0/scripts/replay_live_turns.py` để replay đúng các lượt qua `run_model_tool_loop` (5 lần/cấu hình), và thêm case M_G11, M_G12 vào group eval.
- **Kết quả dao động giữa các lần chạy cùng cấu hình.** R12 trên v5 chỉ PASS 3/5 lần (`starter_v0/runs/diagnostics/`). Xử lý: chạy base v5 2 lần trước khi chọn, ghi rõ độ dao động trong B1.
- **Hai rule đúng riêng lẻ xung đột nhau (v6–v8).** Rule chặn bịa handle làm model dùng `clarify(text)` ở yêu cầu gửi, hỏng R12/M_G06. Xử lý: ablation v8 để tách nguyên nhân, loại v6–v8, giữ v5 cho giai đoạn OpenAI.
- **`wiki` trả 404 với khái niệm không có bài trùng tên** ("agent loop là gì?", `starter_v0/transcripts/v5_openai_ui_20261110T141929564089.transcript.json`). Xử lý: thêm search fallback trong `starter_v0/tools/wiki/tool.py` (chi tiết ở mục 7).
- **Provider lỗi và đổi provider giữa chừng.** 3 run OpenRouter bị lỗi provider toàn bộ (11/11 case, `starter_v0/runs/v5-check_B_group_openrouter_20261110T154628607795.json`, `…154700011955.json`, `starter_v0/runs/v5-check2_B_group_openrouter_20261110T181704237105.json`) → không dùng làm bằng chứng. Các run OpenRouter hợp lệ với prompt sửa handle chỉ đạt 10/11 và 9/11 (`starter_v0/runs/v5-fix-missing-handle_B_group_openrouter_20261110T182555514299.json`, `starter_v0/runs/v6-missing-handle_B_group_openrouter_20261110T182712888670.json`, `…182918869917.json`), nên v9 được chạy trên Gemini. Vì vậy báo cáo không so sánh trực tiếp v9 với v5.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong [TEAM.md](../../TEAM.md) và các báo cáo cá nhân `report/team/MSSV_HoTen.md`:

- [2A202603541_VuNguyenHoangMinh.md](2A202603541_VuNguyenHoangMinh.md) — Vũ Nguyễn Hoàng Minh (LufkyMama): tool `wiki` + sửa bug `timeline`, prompt/tools v1–v8 (base 0.70 → 1.00), unit test (92 passed, 0 skipped), group case G01–M_G11, UI Streamlit + deploy, replay script.
- [2A202603572_BuiHuuPhuc.md](2A202603572_BuiHuuPhuc.md) — Bùi Hữu Phúc (phucbui66): kiểm thử, phát hiện lỗi bịa handle, prompt v9, case M_G12, group eval Gemini 12/12.

## 7. Hạn chế và hướng cải thiện — B6. Reflection

- **Fix thuộc `system_prompt.md`:** hành vi/chính sách xuyên suốt — không đoán khi thiếu thông tin, xác nhận trước hành động có side effect, không ép 1 bước (v1, v5), chỉ dùng handle người dùng đã cung cấp (v9). Chỉ riêng việc bỏ 3 chỉ dẫn xấu đã kéo 0.70 → 0.90.
- **Fix thuộc `tools.yaml`:** routing (khi nào dùng/không dùng từng tool — v2 đưa routing lên 1.00) và convention arg (v3: query chỉ chứa từ khóa, thời gian vào `timeframe`). Lỗi arg nằm đúng chỗ model điền arg.
- **Cần review thủ công:** (1) R13/R03 bị gán `wrong_tool` nhưng thật ra là lỗi arg — đọc `observed_mismatch` mới thấy; (2) M_G11 — kỳ vọng ban đầu quá hẹp; (3) CLI turn 2 "bài này" → agent dùng bài từ lượt trước: hợp lý trong ngữ cảnh nhưng eval single-turn chấm là phải `clarify`; (4) lỗi bịa handle chỉ thấy khi chat thật.
- **Rủi ro overfit:** ví dụ map tên→handle trong `tools.yaml` (Sam Altman→sama, Elon Musk→elonmusk, Andrej Karpathy→karpathy) trùng đáp án base. Held-out extension 0.80 và group 10/11 cho thấy cải thiện không chỉ do các ví dụ này, nhưng nên thay bằng ví dụ khác tên nếu làm tiếp.
- **Bài học từ v6–v8:** 2 rule đúng riêng lẻ có thể xung đột (rule "hỏi account bằng clarify" làm model dùng `clarify text` ở yêu cầu gửi). Ablation v8 chứng minh cần cả hai thay đổi để sửa lỗi live, và chính tổ hợp đó làm hỏng R12 → chưa có bản thắng cả hai trên OpenAI.
- **Lỗi phát hiện khi dùng thật → sửa tool (không đổi prompt/tools.yaml):** câu "agent loop là gì?" (`starter_v0/transcripts/v5_openai_ui_20261110T141929564089.transcript.json`) làm `wiki` trả 404 ở cả 2 lượt và agent không có câu trả lời có nguồn. Sửa `starter_v0/tools/wiki/tool.py`: 404 → Wikipedia full-text search (`/w/rest.php/v1/search/page`), summary bài đầu, đánh dấu `resolved_from`/`alternatives`/`note`; không có kết quả → `WikiNotFound` gợi ý `lookup`; 429 retry 1 lần. Replay 2 câu đó qua `run_model_tool_loop`: agent nhận `Agent harness` và nói rõ đây là khái niệm gần nhất. `prompt_hash`/`tools_hash` không đổi (83d93e245760 / facc86aff20c) nên input của model trong eval không đổi, eval chỉ chấm tool call → không chạy lại eval.
- **Bài học từ v9-gemini:** case M_G08 cho thấy khi người dùng chỉ đổi số lượng tweet, model có thể tự tạo handle dù chưa được cung cấp. Bổ sung quy tắc trong `system_prompt.md`: chỉ dùng handle do người dùng cung cấp, nếu thiếu phải gọi `clarify`; chủ đề và số lượng không phải handle. Case M_G12 kiểm tra việc giữ số lượng khi người dùng cung cấp handle ở lượt sau. Group eval trên Gemini đạt 12/12 PASS, 0 provider error (`starter_v0/runs/v9-gemini-12cases_B_group_gemini_20261110T190940936093.json`). Kết quả này chỉ phản ánh một lần đánh giá trên Gemini; chưa chứng minh hiệu quả tương tự trên mọi provider hoặc hội thoại thực tế.
- **Nếu có thêm một vòng:** (1) sửa eval multi-turn để gửi history thật như chat (hoặc thêm suite replay) — đây là nguyên nhân eval không bắt được lỗi bịa handle; (2) chạy mỗi version ≥ 3 lần, báo mean; (3) chạy v9 trên base eval OpenAI để so sánh cùng model với v5; (4) trả lời bằng ngôn ngữ của user (agent hay trả lời tiếng Anh cho câu tiếng Việt); (5) tool tra handle (`user_lookup`) thay vì để model tự map tên.

## 8. Tài liệu tham khảo

- Wikipedia REST API (summary + search) — dùng cho tool `wiki`: https://en.wikipedia.org/api/rest_v1/ , https://www.mediawiki.org/wiki/API:REST_API
- Hướng dẫn lấy API key và smoke test các tool: [docs/TOOL-SETUP.md](../../docs/TOOL-SETUP.md)
- Tiêu chí chấm: [RUBRIC.md](../../RUBRIC.md), yêu cầu nộp bài: [SUBMISSION.md](../../SUBMISSION.md)
