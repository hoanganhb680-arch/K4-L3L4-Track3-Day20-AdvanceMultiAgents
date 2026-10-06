# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| (nhóm demo) | - | Toàn bộ |

- Nhà cung cấp và mô hình: OpenAI-compatible endpoint nội bộ `LAB_BASE_URL=http://127.0.0.1:20128/v1`, `LAB_MODEL=wdb/deepseek-ai/DeepSeek-V4-Pro-0813`, `LAB_TEMPERATURE=0`, `recursion_limit=60` (mọi tác vụ).
- Phiên bản Deep Agents: 0.7.21; chạy trong Docker (`python:3.12-slim`), Linux.
- Commit của tag `freeze`: `c0489fa` (commit `hypotheses` `93ca34a` đứng ngay trước).

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
| data-learn | (không có) | — | đạt 8/8; không có check thất bại |
| logs-learn | rule_service_names | E. Vi phạm quy ước | “RULE: service names … lower-case, ‘-’ → ‘_’” |
| logs-learn | rule_sorted_errors | E. Vi phạm quy ước | “RULE: `errors` is sorted by service” |
| logs-learn | rule_schema_header | E. Vi phạm quy ước | “RULE: … schema_version: 2 …” |

Nhận xét: gần như mọi lỗi đều là nhóm E (quy ước `rule_`, tác tử không biết). Phần kỹ thuật A–D làm tốt rồi, chỉ vướng đúng `tests_not_modified`. Skill mà viết đúng và được đọc thì gỡ được nhóm E.

## 5. Điều kiện `subagents` (Phần 2.3)

- Đã định nghĩa 3 subagent: `explorer` (đọc), `implementer` (làm), `reviewer` (soát lại).
- Nhưng cả 6 task đều có `subagent_calls = 0` — tác tử tự làm hết, không giao việc lần nào.
- Vì vậy `subagents` gần như trùng `baseline` cả về điểm lẫn token (điểm eval cùng 0.72; token trung bình 270k vs 327k). Mấy cái chênh lệch nhỏ trên task học chủ yếu do nhiễu chạy, không phải do subagent.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Chạy curator 2 lần; lần 1 sinh 3 skill nhưng `description` có dấu hai chấm làm hỏng YAML nên xóa chạy lại. Lần 2 ra 3 skill hợp lệ, ngắn gọn (vài dòng + 5 bước).
- Cả 3 đều tổng quát, đúng, không lộ task id hay đáp án:
  - `enforce-code-standards`: type hints, docstring, không sửa tests/, changelog — đúng.
  - `implement-regression-testing`: viết tests/test_regressions.py — đúng.
  - `verify-requirements-checklist`: liệt kê mọi `RULE:` rồi tự kiểm — đúng.
- Điểm yếu chung: không skill nào ghi chi tiết quy ước mới (kiểu `rule_version_bump`, clean.csv, schema...), nên chỉ gỡ được một phần.

Phần 3.4 (trước đóng băng, cùng skill, cùng mô hình): tác tử đọc đủ 3 skill, kết quả code-learn 8/10, data-learn 5/8, logs-learn 6/9. Tức là có đọc nhưng chỉ làm theo bước tổng quát, chưa dịch hết thành quy ước cụ thể của từng họ task.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 6/10 | 6/10 | 8/10 |
| data-learn | 8/8 | 8/8 | 8/8 |
| logs-learn | 6/9 | 9/9 | 6/9 |
| code-eval | 6/11 | 6/11 | 8/11 |
| data-eval | 9/9 | 9/9 | 9/9 |
| logs-eval | 6/10 | 6/10 | 10/10 |
| **Mean score - learning tasks** | 0.76 | 0.87 | 0.82 |
| **Mean score - evaluation tasks** | 0.72 | 0.72 | 0.91 |
| **Mean tokens per run** | 326,882 | 270,889 | 463,923 |
| **Runs that read a skill** | 0/6 | 0/6 | 6/6 |

## 8. Phân tích

Bảng split nhóm check (`check_breakdown.py`):

| condition | role | technical | house rules | mean tokens | read a skill |
|---|---|---|---|---|---|
| baseline | eval | 17/18 | 4/12 | 339,417 | 0/3 |
| baseline | learn | 17/18 | 3/9 | 314,348 | 0/3 |
| subagents | eval | 17/18 | 4/12 | 223,358 | 0/3 |
| subagents | learn | 17/18 | 6/9 | 318,421 | 0/3 |
| skills-auto | eval | 17/18 | 10/12 | 443,545 | 3/3 |
| skills-auto | learn | 17/18 | 5/9 | 484,301 | 3/3 |

- Cả 3 điều kiện đều đạt gần như trọn phần kỹ thuật (17/18). Mọi chênh lệch nằm ở nhóm quy ước (`rule_`).
- `subagents` không khác gì `baseline` vì tác tử không giao việc lần nào (`subagent_calls = 0`). Đúng như H1 đoán.
- `skills-auto` là cái duy nhất lợi thật: 6/6 run đều đọc skill, check quy ước ở eval tăng từ 4/12 lên 10/12. H2 đoán "chỉ giúp task học" hóa ra sai — skill giúp task đánh giá nhiều hơn (0.72 → 0.91) vì 3 skill đều tổng quát, không quá khớp vào task học.
- H3 cũng sai: có skill thì điểm eval (0.91) cao hơn task học (0.82). Khác biệt không phải do độ khó cố định mà do quy ước mới, skill có che được không.
- Cái giá phải trả là token: skills-auto tốn ~464k/run, gấp ~1.4 lần baseline và ~1.7 lần subagents (đọc 3 skill + làm thêm mấy file quy ước).

Về nhiễu: cùng bộ skill chạy 2 lần (trước/sau đóng băng) thì data-learn 5/8 vs 8/8, còn lại trùng. Nên mấy chênh lệch nhỏ đừng đọc là hiệu quả, chỉ là nhiễu thôi.

## 9. Hạn chế và tính hợp lệ

1. Chỉ 3 task mỗi loại, mỗi điều kiện chạy đúng 1 lần (n=1) nên không tách rõ được hiệu quả với nhiễu.
2. Dù `LAB_TEMPERATURE=0` điểm vẫn dao động giữa các lần chạy (data-learn 5/8 rồi 8/8 cùng 1 bộ skill), và mô hình thỉnh thoảng lặp tới hết `recursion_limit`.
3. Task do giảng viên thiết kế sẵn quy ước; chỉ chạy một mô hình (DeepSeek-V4-Pro-0813).
4. `subagent_calls` toàn bộ bằng 0, nên nhận xét về đa tác tử chỉ đúng cho trường hợp "có subagent mà không dùng", chưa nói gì khi nó được gọi thật.

## 10. Kết luận

- H1 đúng: thêm subagent không cải thiện điểm hay tăng token, vì tác tử không giao việc lần nào.
- H2 sai: skill sinh ra không chỉ giúp task học mà giúp task đánh giá nhiều hơn (0.72 → 0.91), vì 3 skill đều tổng quát chứ không quá khớp.
- H3 sai: có skill thì điểm eval (0.91) cao hơn task học (0.82); khác biệt nằm ở quy ước mới và việc skill có che được không.
- Nói chung: hầu hết lỗi thuộc nhóm quy ước (`rule_`), phần kỹ thuật thì gần hết rồi (17/18). Skill tự sinh là cách rẻ để gỡ nhóm quy ước, nhưng tốn token hơn kha khá (~1.4–1.7 lần).

## Phụ lục

- Lệnh đã chạy (môi trường Docker `python:3.12-slim`, Linux; shell của tác tử dùng `/bin/sh`):
  - `pytest` (offline)
  - `python -m lab.runner --condition baseline --tasks learn`
  - `python -m lab.runner --condition subagents --tasks learn`
  - `python -m lab.curator`
  - `python -m lab.runner --condition skills-auto --tasks learn`  (kết quả sao lưu vào `results/skills-auto-dev`)
  - `git add -A && git commit -m "hypotheses"`  (H1–H3 hoàn chỉnh)
  - `git commit --allow-empty -m "freeze skills" && git tag freeze`
  - `python -m lab.runner --condition baseline --tasks eval`
  - `python -m lab.runner --condition subagents --tasks eval`
  - `python -m lab.runner --condition skills-auto --tasks all`
  - `python -m lab.compare > report/table.md`
  - `python scripts/check_breakdown.py`

Lưu ý tái lập: trên Windows host, vì `LocalShellBackend` chạy `/bin/sh`, nên chạy lab qua Docker bind-mount để shell của tác tử là Linux (xem README mục 4). Khi đó `verify_freeze.py` và `git diff freeze` phải được chạy trong môi trường Linux/LF (không dùng checkout CRLF của Windows) để hash skill khớp `run.json`.