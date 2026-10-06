# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| (nhóm demo) | - | Toàn bộ |

- Nhà cung cấp và mô hình: `LAB_MODEL=google_genai:gemini-3.1-flash-lite`, `LAB_TEMPERATURE=0`, `recursion_limit` 40–60 (tuỳ tác vụ).
- Phiên bản Deep Agents: 0.7.21; chạy trong Docker (`python:3.12-slim`), Linux.
- Commit của tag `freeze`: (điền sau khi freeze)

## 2. Giả thuyết (commit TRƯỚC tag `freeze`)

- H1 (subagents so với baseline): subagents không cải thiện điểm bền vững; nhiều khả năng ngang hoặc thấp hơn baseline và tốn token hơn hẳn, vì mô hình flash-lite hay lặp khi dùng công cụ `task` và giao việc làm mất ngữ cảnh.
- H2 (skills-auto so với baseline): skill tự sinh giúp nhóm check “house rule” (rule_) của tác vụ học, nhưng ít hoặc không cải thiện tác vụ đánh giá, do curator học được quy ước đã thấy ở tác vụ học (quá khớp) và description có thể quá hẹp để được đọc ở tác vụ mới.
- H3 (tác vụ học so với tác vụ đánh giá): điểm tác vụ đánh giá nhìn chung thấp hơn tác vụ học, vì tác vụ đánh giá có thêm một quy ước mới mà skill không hề biết.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có các công cụ: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute`, `task`. Công cụ chạy lệnh là `execute`.
2. Mô tả công cụ `task` nói về subagent `general-purpose` (được thêm mặc định); subagent chỉ thấy nội dung mà tác tử chính gửi trong lời giao việc, không thấy toàn bộ hội thoại.
3. System prompt mặc định rỗng. Trích từ công cụ `task`: “a subagent sees only what you send”; từ công cụ `execute`: “commands run with your user's full permissions”.

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi | Bằng chứng (trích ngắn) |
|---|---|---|---|
| code-learn | tests_not_modified | A. Bỏ qua đặc tả | “the original files in tests/ must not be modified” |
| code-learn | rule_type_hints | E. Vi phạm quy ước | “RULE: every public function … has type annotations” |
| code-learn | rule_regression_tests | E. Vi phạm quy ước | “RULE: add tests/test_regressions.py …” |
| code-learn | rule_changelog | E. Vi phạm quy ước | “RULE: record each fix in CHANGELOG.md” |
| data-learn | north_q1_revenue | D. Bỏ sót dữ liệu bẩn | “north_q1_revenue: wrong value (got 3189.59)” |
| data-learn | rule_money_in_cents | E. Vi phạm quy ước | “RULE: money values … are integer cents” |
| data-learn | rule_meta_block | E. Vi phạm quy ước | “RULE: answer.json has an object `meta`” |
| data-learn | rule_clean_csv | E. Vi phạm quy ước | “RULE: write workspace/clean.csv …” |
| logs-learn | rule_service_names | E. Vi phạm quy ước | “RULE: service names … lower-case” |
| logs-learn | rule_sorted_errors | E. Vi phạm quy ước | “RULE: `errors` is sorted by service” |
| logs-learn | rule_schema_header | E. Vi phạm quy ước | “RULE: … schema_version: 2 …” |

Nhận xét: đa số lỗi thuộc nhóm E (quy ước tổ chức Acme, check `rule_`); các check kỹ thuật A–D phần lớn đạt. Skill có thể phòng ngừa nhóm E nếu được viết đúng và được đọc.

## 5. Điều kiện `subagents` (Phần 2.3)

- Đã định nghĩa 3 subagent: `explorer` (đọc/báo cáo), `implementer` (thực hiện), `reviewer` (kiểm tra độc lập).
- `subagent_calls` (tác vụ học): xem trace; ở code-learn tác tử có gọi `task`. Ở logs-learn tác tử lặp đến hết recursion limit.
- Thông tin giao việc thường đủ, nhưng subagent chỉ thấy prompt được gửi nên dễ sót quy ước.
- Token tăng rõ rệt so với baseline (multi-agent tốn nhiều lần gọi mô hình).

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Chạy curator 2 lần; lần 1 sinh 3 skill nhưng `description` có dấu hai chấm chưa quote làm YAML hỏng (bị skip khi nạp) → xóa và chạy lại. Lần 2 sinh 3 skill hợp lệ.

| Skill | Tổng quát hay riêng | Đúng/sai | Độ dài, description, skills_read (3.4) |
|---|---|---|---|
| enforce-code-standards | Tổng quát (type hints, docstring, changelog) | Đúng | ngắn, “Use when writing or modifying code…” |
| implement-regression-testing | Tổng quát (viết test hồi quy) | Đúng | ngắn, “Use when fixing bugs…” |
| verify-requirements-checklist | Tổng quát (tự kiểm tra quy tắc) | Đúng | ngắn, “Use when starting a task…” |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

(dán table.md sau khi chạy lab.compare)

## 8. Phân tích

(điền sau khi có kết quả chính thức)

## 9. Hạn chế và tính hợp lệ

1. Chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy 1 lần.
2. Nhiễu của mô hình (temperature 0 vẫn còn ngẫu nhiên nhỏ) và mô hình flash-lite hay lặp.
3. Tác vụ do giảng viên thiết kế sẵn quy ước; chỉ một mô hình.

## 10. Kết luận

(điền sau khi có kết quả)

## Phụ lục

- Lệnh đã chạy:
  - `pytest` (offline)
  - `python -m lab.runner --condition baseline --tasks learn`
  - `python -m lab.runner --condition subagents --tasks learn`
  - `python -m lab.curator`
  - `python -m lab.runner --condition skills-auto --tasks learn`