# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần:
> - **PHẦN A — Giới thiệu agent** (1 trang, dùng khi demo).
> - **PHẦN B — Chi tiết / Bằng chứng** (mọi số liệu lấy từ `runs/*.json`, `artifacts/version_log.csv`, `transcripts/*.json`).

## Team

- Team: NhomABC 
- Members: minhh, Phuc
- Provider/model: OpenAI `gpt-4o-mini` (`--provider openai`, temperature 0), Gemini `gemini-3.5-flash-lite`(`--provider gemini`)
- Final artifacts: **v5**(Minh) — `system_prompt.md` sha256 `83d93e245760…`, `tools.yaml` sha256 `facc86aff20c…`,Kết quả Group Eval: 10/11 PASS.
                   **v9**(Phúc) — `system_prompt.md` sha256 `1773d3413560…`, `tools.yaml` sha256 `facc86aff20c…`. Bổ sung quy tắc xử lý Twitter handle và testcase M_G12. Kết quả Group Eval: 12/12 PASS trên Gemini.

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent tiếng Việt/Anh: tìm tin tức trên web, đọc tweet của một tài khoản hoặc theo chủ đề, đọc nội dung một URL, tra định nghĩa/tiểu sử trên Wikipedia, gom kết quả thành digest — và **luôn hỏi lại** khi thiếu tài khoản/URL hoặc trước khi đăng gì lên Telegram.

**Link dùng thử (deploy):**

> URL: **https://pts-mentor-plots-agrees.trycloudflare.com**
>
> Cloudflare quick tunnel → Streamlit `app.py` tại `localhost:8501`. Đã kiểm tra 2026-11-10: `/_stcore/health` và `/` trả HTTP 200 qua link public. Link tạm thời, chỉ sống khi máy demo còn chạy `cloudflared` + Streamlit.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin / xin xác nhận yes-no trước khi gửi | không |
| timeline | lấy tweet mới nhất của MỘT tài khoản X (RapidAPI) | không |
| social_search | tìm tweet theo chủ đề, `Latest` hoặc `Top` (RapidAPI) | không |
| lookup | tìm web / tin tức theo `topic` + `timeframe` (Tavily) | không |
| fetch | đọc nội dung một URL cụ thể (Firecrawl) | không |
| format | trình bày item đã có thành digest markdown | không |
| send | đăng lên Telegram — chỉ khi `confirmed=true` (code chặn nếu chưa xác nhận) | không (bonus) |
| policy / papers / paper_text | chính sách nội bộ / tìm paper arXiv / đọc text paper arXiv | không (bonus) |
| **wiki** | tóm tắt bách khoa một khái niệm/nhân vật từ Wikipedia (không cần API key) | **có** |

## A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay có gì nổi bật?` → `lookup(query="AI", topic="news", timeframe="day")`
2. `Lấy 3 tweet mới nhất của Andrej Karpathy` → `timeline(screenname="karpathy", limit=3)`
3. `Mixture of Experts là gì?` → `wiki(title="Mixture of Experts")`
4. `Tóm tắt bài viết này giúp mình` → agent hỏi lại link; gửi link ở lượt sau → `fetch`
5. `Đăng bản tin này lên Telegram` → agent hỏi xác nhận yes/no, không tự gửi

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: `artifacts/version_log.csv`. Metric = `case_accuracy` trên `data/eval_base.json` (20 case) trừ khi ghi khác. Mỗi version đổi **một** giả thuyết.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (starter) | — | — | case 0.70 · routing 0.75 · args 0.70 · multi 1.00 | `runs/v0_B_base_openai_20261110T122635455139.json` |
| v1 | `system_prompt.md` | Chỉ dẫn xấu của starter (đoán thay vì hỏi, gửi ngay, ép 1 bước) gây lỗi; thay bằng rule hỏi-khi-thiếu + xác-nhận-trước-khi-gửi | 0.70 | case 0.90 · routing 0.95 · args 0.90 · multi 0.83 | `runs/v1_B_base_openai_20261110T123716299760.json` |
| v2 | `tools.yaml` (chỉ tool description) | Description 1 dòng mơ hồ gây sai routing; viết lại làm-gì / khi-nào-dùng / khi-nào-không | 0.90 | case 0.90 · **routing 1.00** · args 0.90 · multi 1.00 | `runs/v2_B_base_openai_20261110T124125137289.json` |
| v3 | `tools.yaml` (chỉ parameter description) | Thiếu convention args; ghi rõ query = từ khóa cốt lõi, topic/timeframe/search_type/limit/handle | 0.90 | **case 1.00** · routing 1.00 · args 1.00 · multi 1.00 | `runs/v3_B_base_openai_20261110T124258138149.json` |
| v4 | + tool mới `wiki` | Thêm `wiki` với ranh giới rõ vs `lookup` không làm hỏng routing base | 1.00 | base 0.95 (R12 dao động) · group 10/10 | `runs/v4_B_base_…124729660557.json`, `runs/v4_B_group_…124932573963.json` |
| v5 | `system_prompt.md` (+1 dòng) | Rule xác nhận chưa phủ trường hợp nội dung mơ hồ → yes_no luôn là bước đầu của yêu cầu gửi | 0.95 | base **1.00 / 1.00** (2 lần) · group 10/10 | `runs/v5_B_base_…125725753667.json`, `runs/v5_B_base_…130151902291.json`, `runs/v5_B_group_…130237286963.json` |
| v6 ✗ | `system_prompt.md` (+1 rule) | "Chủ đề ở lượt trước không phải tài khoản" chặn bịa handle trong chat live | live 5/5 bịa handle | live vẫn 5/5 (đổi kiểu lỗi) | replay, xem B4 |
| v7 ✗ | `tools.yaml` `timeline.screenname` | Đặt ràng buộc ở chỗ model điền arg | live 5/5 | live **1/5**, nhưng base 0.95 · group 0.91; R12 0/5, M_G06 2/5 | `runs/v7_B_base_…131940655341.json`, `runs/v7_B_group_…131902941777.json`, `runs/diagnostics/diag-v7-*` |
| v8 ✗ | ablation: prompt v5 + tools v7 | Chỉ ràng buộc cấp tool là đủ, dòng prompt v6 gây hỏng R12 | R12 0/5 | R12 4/5 · M_G06 5/5 nhưng live lại 5/5 | `runs/diagnostics/diag-v8-*` |
| v9 | `system_prompt.md`, thêm M_G12 vào `eval_group.json` |Không tự đoán Twitter handle khi thiếu; khi user bổ sung handle ở lượt sau thì dùng đúng handle và số lượng |OpenRouter với prompt sửa: 9/11 (lần thử khác model) | Gemini group 12/12 PASS, 0 provider error| `runs/v9-gemini-12cases_B_group_gemini_20261110T190940936093.json`|

**Bản nộp cuối = v9.** Phiên bản ổn định được chọn ở giai đoạn đánh giá OpenAI = v5. v6–v8 bị loại (✗) vì sửa được lỗi live thì làm hỏng boundary gửi (xem B6). Held-out check trên `eval_research_extension.json` (không tối ưu cho nó) với v3: 0.80 (8/10) — `runs/v3_B_extension_openai_20261110T124359497841.json`.
Ở giai đoạn tiếp theo, v9-gemini dùng prompt hash `1773d3413560…`, tools hash `facc86aff20c…`, đạt 12/12 trên Gemini. Kết quả này chưa phải so sánh cùng model với v5; chưa có bằng chứng v9 thắng trên toàn bộ base eval OpenAI.
**Độ dao động (cùng cấu hình, chạy riêng 5 lần, `runs/diagnostics/`):** R12 trên v3 5/5, v4 5/5, v5 3/5, v7 0/5, v8 4/5. Một run eval đơn lẻ có thể lệch ±1 case — vì vậy v5 được chạy base 2 lần.

## B2. Failure Analysis

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
| M_G08_still_missing_handle (group) | missing_info | `timeline(screenname="@karpathy")` (v5 final run) | Bịa handle khi user chưa nêu tài khoản | v5 :Known issue (B6); tool fix `@` stripping không giải quyết routing v5: known issue; v9-gemini: bổ sung rule chỉ dùng handle đã được cung cấp, thiếu thì clarify(text); M_G08 PASS trên Gemini |

## B3. Team Eval Cases

`data/eval_group.json` — 12 case (5 single + 7 multi). Kết quả lấy từ run cuối v5 `runs/v5_B_group_openai_20261110T132546014603.json` (10/11, 0.909) và run v5 trước đó `runs/v5_B_group_openai_20261110T130237286963.json` (10/10, khi chưa có M_G11).

| Case ID | What It Tests | Expected Tool/Behavior | Result (v5 cuối) |
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

Ghi chú trung thực: M_G11 ban đầu được viết với kỳ vọng `clarify`; sau khi thấy model hiểu hợp lý là "5 tweet mới nhất về GPT-5", kỳ vọng được đổi thành `social_search(GPT-5)` **trước** khi dùng làm metric (case do mình tự viết, không phải base).

## B4. Live Chat Evidence

**CLI** — `transcripts/v5_openai_20261110T130531082196.transcript.json` (artifact v5):

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tin tức AI hôm nay có gì nổi bật? | `lookup(query="AI", topic="news", timeframe="day")` | v5+p83d93e245760+tfacc86aff20c | 5 tin có nguồn |
| 2 | Tóm tắt bài viết này giúp mình | `fetch(<URL bài #1 của lượt trước>)` | v5 | Hiểu "bài này" = bài đầu tiên vừa liệt kê (có ngữ cảnh, không bịa URL) |
| 3 | `https://www.anthropic.com/news/claude-3-5-sonnet` | `fetch(url=…)` | v5 | Tóm tắt đúng bài |
| 4 | Đăng bản tóm tắt đó lên Telegram giúp mình | `clarify(response_type="yes_no")` | v5 | **Hỏi xác nhận, không gửi** |
| 5 | Mixture of Experts là gì? | `wiki(title="Mixture of Experts")` | v5 | Trả lời + link Wikipedia |

**UI Streamlit** — `transcripts/v5_openai_ui_20261110T130625795322.transcript.json` (3 lượt qua `app.py`, chạy bằng Streamlit AppTest với model thật):

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | Mọi người đang bàn gì về GPT-5 trên Twitter? | `social_search(query="GPT-5", search_type="Top")` | OK |
| 2 | Tóm tắt 5 tweet mới nhất giúp mình | `timeline(screenname="gpt", limit=5)` | **Lỗi: bịa handle `gpt` từ chủ đề** → tweet không liên quan |
| 3 | Của Andrej Karpathy nhé, lấy 3 tweet thôi | `timeline(screenname="karpathy", limit=3)` | OK |

Lỗi lượt 2 không lộ ra trong eval vì `run_eval.py` gộp các lượt thành 1 message, còn chat/UI gửi history thật. Đo lại bằng `scripts/replay_live_turns.py` (replay đúng 2 lượt qua `run_model_tool_loop`, 5 lần mỗi cấu hình): v5 5/5 bịa handle (`gpt3`, `openai`), v6 5/5 (gọi `timeline` cho tác giả trong kết quả trước), v7 1/5, v8 5/5.
UI Streamlit — kiểm tra tiếp theo với Gemini: Các `transcript transcripts/v5_gemini_ui_20261110T183917821803.transcript.json`, `transcripts/v5_gemini_ui_20261110T184110186036.transcript.json` và `transcripts/v5_gemini_ui_20261110T185042926334.transcript.json` ghi nhận các lượt thử giao diện với Gemini. Trong tình huống chưa có Twitter handle, Agent gọi `clarify` thay vì tự tạo tên tài khoản. Tên file transcript vẫn có tiền tố `v5` theo lúc lưu, không phải nhãn run `v9-gemini`.
UI server: `streamlit run app.py --server.headless true` → `/_stcore/health` = `ok`, `/` = HTTP 200 (đã kiểm tra local).

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | v0 run: 3 lần `send` đều trả `needs_confirmation`; CLI turn 4 | Guard trong code + prompt hỏi yes/no | **Chưa test gửi thật** (không cấu hình `TELEGRAM_*` — cố ý để eval không gửi được) |
| arXiv/company policy | `runs/v3_B_extension_openai_20261110T124359497841.json` | 8/10 | E01 thiếu `policy_area=source_citation`; E06 thiếu `lookup` song song |
| UI | `app.py`, `transcripts/v5_openai_ui_*.json` | Tái dùng `run_model_tool_loop`/transcript của `chat.py`; hiện trạng thái + tool call | Link public qua Cloudflare quick tunnel (tạm thời; dùng API key của máy demo) |
| Tool unit tests (`tests/`) | `pytest` → **92 passed, 0 failed, 0 skipped** | 14 stub (tool có sẵn) đã điền + 1 regression + 10 test `wiki` (thay 3 stub tool mới) | offline, mock HTTP |

Tool unit tests: `tests/test_tools_todo.py` có 25 test (14 stub TODO của tool có sẵn + 1 regression `timeline` + 10 test cho `wiki`: happy path, title rỗng/sai kiểu, `lang` ngoài enum, 404 → search fallback, 404 không có kết quả → `WikiNotFound` gợi ý `lookup`, trúng tên chính xác không search, 429 retry 1 lần (chờ ≤5s), HTTP 500 không search, timeout, trang disambiguation).

**Bug tìm được trong tool có sẵn (1):** `timeline` gửi nguyên `screenname=" @sama "` lên RapidAPI. Test `test_timeline_strips_at_sign_from_handle` **fail trước khi sửa** (`{'screenname': ' @sama '} != {'screenname': 'sama'}`), sửa trong `tools/timeline/tool.py` (strip khoảng trắng và `@`), test được giữ làm regression. Đây đúng là loại lỗi eval không bắt được: model gửi `@karpathy` (thấy thật trong M_G08) thì eval chỉ chấm tên tool/arg, còn API nhận handle sai.

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** hành vi/chính sách xuyên suốt — không đoán khi thiếu thông tin, xác nhận trước hành động có side effect, không ép 1 bước (v1, v5). Chỉ riêng việc bỏ 3 chỉ dẫn xấu đã kéo 0.70 → 0.90.
- **Fix thuộc `tools.yaml`:** routing (khi nào dùng/không dùng từng tool — v2 đưa routing lên 1.00) và convention arg (v3: query chỉ chứa từ khóa, thời gian vào `timeframe`). Lỗi arg nằm đúng chỗ model điền arg.
- **Cần review thủ công:** (1) R13/R03 bị gán `wrong_tool` nhưng thật ra là lỗi arg — đọc `observed_mismatch` mới thấy; (2) M_G11 — kỳ vọng ban đầu quá hẹp; (3) CLI turn 2 "bài này" → agent dùng bài từ lượt trước: hợp lý trong ngữ cảnh nhưng eval single-turn chấm là phải `clarify`; (4) lỗi bịa handle chỉ thấy khi chat thật.
- **Rủi ro overfit:** ví dụ map tên→handle trong `tools.yaml` (Sam Altman→sama, Elon Musk→elonmusk, Andrej Karpathy→karpathy) trùng đáp án base. Held-out extension 0.80 và group 10/11 cho thấy cải thiện không chỉ do các ví dụ này, nhưng nên thay bằng ví dụ khác tên nếu làm tiếp.
- **Bài học từ v6–v8:** 2 rule đúng riêng lẻ có thể xung đột (rule "hỏi account bằng clarify" làm model dùng `clarify text` ở yêu cầu gửi). Ablation v8 chứng minh cần cả hai thay đổi để sửa lỗi live, và chính tổ hợp đó làm hỏng R12 → chưa có bản thắng cả hai.
- **Lỗi phát hiện khi dùng thật → sửa tool (không đổi prompt/tools.yaml):** câu "agent loop là gì?" (`transcripts/v5_openai_ui_20261110T141929564089.transcript.json`) làm `wiki` trả 404 ở cả 2 lượt và agent không có câu trả lời có nguồn. Sửa `tools/wiki/tool.py`: 404 → Wikipedia full-text search (`/w/rest.php/v1/search/page`), summary bài đầu, đánh dấu `resolved_from`/`alternatives`/`note`; không có kết quả → `WikiNotFound` gợi ý `lookup`; 429 retry 1 lần. Replay 2 câu đó qua `run_model_tool_loop`: agent nhận `Agent harness` và nói rõ đây là khái niệm gần nhất. `prompt_hash`/`tools_hash` không đổi (83d93e245760 / facc86aff20c) nên input của model trong eval không đổi, eval chỉ chấm tool call → không chạy lại eval.
- **Làm tiếp:** (1) sửa eval multi-turn để gửi history thật như chat (hoặc thêm suite replay) — đây là nguyên nhân eval không bắt được lỗi bịa handle; (2) chạy mỗi version ≥3 lần, báo mean; (3) trả lời bằng ngôn ngữ của user (agent hay trả lời tiếng Anh cho câu tiếng Việt); (4) tool tra handle (`user_lookup`) thay vì để model tự map tên.
- **Bài học từ v9-gemini**: Case M_G08 cho thấy khi người dùng chỉ đổi số lượng tweet, model có thể tự tạo handle dù chưa được cung cấp. Bổ sung quy tắc trong `system_prompt.md`: chỉ dùng handle do người dùng cung cấp, nếu thiếu phải gọi `clarify`; chủ đề và số lượng không phải handle. Test M_G12 kiểm tra việc giữ số lượng khi người dùng cung cấp handle ở lượt sau. Group Eval trên Gemini đạt 12/12 PASS, 0 provider error (`runs/v9-gemini-12cases_B_group_gemini_20261110T190940936093.json`). Kết quả này chỉ phản ánh một lần đánh giá trên Gemini; chưa chứng minh hiệu quả tương tự trên mọi provider hoặc hội thoại thực tế.

## B7. Small Local Model Challenge (bonus)

Không thực hiện.
