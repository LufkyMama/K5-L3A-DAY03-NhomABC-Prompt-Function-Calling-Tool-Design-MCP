# Báo cáo cá nhân — HoVaTen-MSSV

Đổi tên file theo quy tắc `MSSV_HoTen.md`.

Ví dụ: `20241234_NguyenVanAn.md`.

## 1. Thông tin thành viên

- Họ tên: Bùi Hữu Phúc
- MSSV: 2A202603572
- Email: phucbh.66.24@gmail.com

## 2. Phần việc phụ trách
- Kiểm tra hoạt động của Research Agent sau khi nhóm hoàn thành các chức năng chính.

- Kiểm thử khả năng lựa chọn tool và xử lý hội thoại nhiều lượt.

- Tìm lỗi khi Agent xử lý yêu cầu lấy tweet trên Twitter.

- Chỉnh sửa System Prompt để hạn chế Agent tự đoán thông tin người dùng chưa cung cấp.

- Bổ sung testcase và chạy lại bộ đánh giá Group Eval bằng Gemini.

- Cập nhật kết quả kiểm thử vào báo cáo chung của nhóm.

## 3. Đóng góp cụ thể

### 3.1. Kiểm tra và phát hiện lỗi

Trong quá trình kiểm thử, em phát hiện Agent có trường hợp tự đoán tài khoản Twitter khi người dùng chưa cung cấp.

Ví dụ:

Lượt 1: "Lấy tweet mới nhất giúp mình".

Lượt 2: "Lấy 3 cái thôi nhé".

Trong trường hợp này, Agent cần hỏi lại tài khoản Twitter. Tuy nhiên, ở phiên bản trước, Agent có lúc tự sử dụng tài khoản @karpathy để gọi tool timeline.

### 3.2. Chỉnh sửa System Prompt

Em chỉnh sửa file artifacts/system_prompt.md, bổ sung các quy tắc:

Không tự đoán Twitter handle.

Chỉ sử dụng tài khoản đã được người dùng cung cấp.

Nếu thiếu tài khoản thì gọi tool clarify để hỏi lại.

Khi người dùng chỉ thay đổi số lượng tweet, Agent vẫn phải kiểm tra xem đã có tài khoản hay chưa.

Phân biệt chủ đề tìm kiếm Twitter với tài khoản Twitter cụ thể.

### 3.3. Bổ sung testcase

Em bổ sung testcase M_G12_clarify_then_timeline vào data/eval_group.json.

Testcase kiểm tra trường hợp người dùng yêu cầu lấy 3 tweet nhưng chưa cung cấp tài khoản, sau đó bổ sung tài khoản ở lượt tiếp theo.

Kết quả mong muốn là Agent gọi đúng tool timeline với screenname="karpathy" và limit=3.

Sau khi bổ sung, bộ Group Eval có tổng cộng 12 testcase, gồm 5 single-turn và 7 multi-turn.

### 3.4. Chạy kiểm thử

Em sử dụng Gemini với model gemini-3.5-flash-lite để chạy lại bộ Group Eval sau khi chỉnh sửa System Prompt và bổ sung testcase M_G12.

Bộ kiểm thử gồm tổng cộng 12 testcase, trong đó có 5 single-turn và 7 multi-turn. Kết quả đạt 12/12 PASS, 0 FAIL và 0 provider error, tương đương tỷ lệ PASS 100%.

Kết quả cho thấy Agent đã xử lý đúng các testcase trong lần kiểm thử này, bao gồm trường hợp thiếu Twitter handle và trường hợp người dùng bổ sung tài khoản ở lượt tiếp theo.
## 4. Bằng chứng
- Commit : `2ef9437`
File đã chỉnh sửa:

- `artifacts/system_prompt.md` — bổ sung quy tắc xử lý Twitter handle.

- `data/eval_group.json` — bổ sung testcase M_G12.

- `artifacts/version_log.csv` — ghi nhận phiên bản kiểm thử mới.

- `artifacts/REPORT.md` — cập nhật báo cáo chung của nhóm.

File kết quả kiểm thử:

`runs/v9-gemini-12cases_B_group_gemini_20261110T190940936093.json`

AI/công cụ đã sử dụng:

- ChatGPT: Hỗ trợ phân tích lỗi, đề xuất cách chỉnh sửa System Prompt và viết báo cáo.

- Gemini 3.5 Flash Lite: Chạy kiểm thử Agent.

- Python: Chạy run_eval.py để đánh giá các testcase.

-  VS Code và PowerShell: Chỉnh sửa file, chạy lệnh kiểm thử và kiểm tra kết quả.

- Git/GitHub: Quản lý các thay đổi trong dự án nhóm.

Cách tự kiểm tra kết quả:

- Chạy lại Group Eval sau khi chỉnh sửa System Prompt.

- Kiểm tra số testcase PASS/FAIL trong kết quả.

- Kiểm tra các trường hợp thiếu Twitter handle và việc lựa chọn tool clarify hoặc timeline.

- Đối chiếu kết quả với các testcase đã khai báo trong data/eval_group.json.

## 5. Tự đánh giá
Qua bài thực hành, em hiểu rõ hơn cách System Prompt ảnh hưởng đến việc Agent lựa chọn tool và xử lý thông tin trong hội thoại.

Em đã phát hiện và chỉnh sửa được lỗi Agent tự đoán tài khoản Twitter khi chưa có đủ thông tin. Sau khi bổ sung quy tắc và testcase, kết quả Group Eval trên Gemini đạt 12/12 PASS.

Em cũng học được cách tạo testcase, chạy đánh giá và đọc kết quả để kiểm tra các thay đổi có hoạt động đúng hay không.

Tuy nhiên, kết quả hiện tại mới được kiểm chứng trên một lần chạy Gemini với bộ Group Eval. Em cần kiểm thử thêm trên các model khác và trong hội thoại thực tế để đánh giá độ ổn định.

- Tự đánh giá: Em đã hoàn thành phần kiểm thử, phát hiện lỗi, chỉnh sửa System Prompt, bổ sung testcase và cập nhật kết quả vào báo cáo nhóm.
