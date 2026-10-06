# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Bùi Hoàng Anh | 2A2020602697 | Toàn bộ (làm cá nhân) |

- Mô hình: `wdb/deepseek-ai/DeepSeek-V4-Pro-0813` qua endpoint nội bộ `http://127.0.0.1:20128/v1`.
- `LAB_TEMPERATURE=0`, `recursion_limit=60`.
- Deep Agents 0.7.21, chạy trong Docker (`python:3.12-slim`), Linux.
- Tag `freeze` = commit `c0489fa` (commit `hypotheses` `93ca34a` nằm ngay trước nó).

## 2. Giả thuyết (viết trước khi thấy điểm đánh giá, commit trước tag `freeze`)

- **H1 (subagents so baseline):** subagents không làm điểm tăng. Khả năng cao điểm ngang hoặc thấp hơn baseline và tốn nhiều token hơn, vì mô hình nhỏ hay bị lặp khi gọi `task`, và giao việc làm mất ngữ cảnh.
- **H2 (skills-auto so baseline):** skill tự sinh giúp làm đúng mấy `rule_` (house rule) ở tác vụ học, nhưng ít hoặc không giúp được tác vụ đánh giá. Lý do: curator chỉ học được quy ước đã thấy ở tác vụ học (overfit), và `description` hẹp nên dễ không được đọc ở tác vụ mới.
- **H3 (tác vụ học so đánh giá):** điểm tác vụ đánh giá thường thấp hơn tác vụ học, vì tác vụ đánh giá có thêm một quy ước mới mà skill chưa biết.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Công cụ mặc định của tác tử: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute`, `task`. Công cụ để chạy lệnh là `execute`.
2. Công cụ `task` nói về một subagent `general-purpose` (có sẵn). Subagent chỉ thấy những gì tác tử chính gửi trong lời giao việc, không thấy toàn bộ hội thoại.
3. System prompt mặc định rỗng. Trích câu hành vi: từ `task` — "a subagent sees only what you send"; từ `execute` — "commands run with your user's full permissions".

## 4. Baseline và phân loại lỗi (Phần 2.2)

| Tác vụ | Check fail | Nhóm lỗi | Bằng chứng (trích ngắn) |
|---|---|---|---|
| code-learn | tests_not_modified | A. Bỏ sót đặc tả | "the original files in tests/ must not be modified" |
| code-learn | rule_type_hints | E. Vi phạm quy ước | "RULE: every public function … has type annotations" |
| code-learn | rule_regression_tests | E. Vi phạm quy ước | "RULE: add tests/test_regressions.py …" |
| code-learn | rule_changelog | E. Vi phạm quy ước | "RULE: record each fix in CHANGELOG.md" |
| data-learn | (không fail) | — | đạt 8/8 |
| logs-learn | rule_service_names | E. Vi phạm quy ước | "RULE: service names … lower-case, '-' → '_'" |
| logs-learn | rule_sorted_errors | E. Vi phạm quy ước | "RULE: `errors` is sorted by service" |
| logs-learn | rule_schema_header | E. Vi phạm quy ước | "RULE: … schema_version: 2 …" |

Nhận xét: gần như mọi lỗi nằm ở nhóm E (quy ước `rule_`, tác tử không biết). Phần kỹ thuật A–D làm tốt rồi, chỉ vướng đúng `tests_not_modified`. Skill nếu viết đúng và được đọc thì sẽ gỡ được nhóm E.

## 5. Điều kiện subagents (Phần 2.3)

- Đã định nghĩa 3 subagent: `explorer` (đọc), `implementer` (làm), `reviewer` (soát lại).
- Nhưng cả 6 tác vụ đều `subagent_calls = 0`, tức tác tử tự làm hết, không giao việc lần nào.
- Vì vậy `subagents` gần như giống hệt `baseline` (điểm đánh giá cùng 0.72; token trung bình 270k so 327k). Chênh lệch nhỏ ở tác vụ học chủ yếu là nhiễu chạy, không phải nhờ subagent.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Chạy curator 2 lần. Lần 1 ra 3 skill nhưng `description` có dấu hai chấm làm hỏng YAML nên xoá chạy lại. Lần 2 ra 3 skill hợp lệ, ngắn (vài dòng + 5 bước).
- Cả 3 đều tổng quát, đúng, không để lộ id hay đáp án của tác vụ:
  - `enforce-code-standards`: thêm type hints, docstring, không sửa tests/, thêm changelog.
  - `implement-regression-testing`: viết tests/test_regressions.py.
  - `verify-requirements-checklist`: liệt kê mọi `RULE:` rồi tự kiểm.
- Điểm yếu chung: không skill nào ghi chi tiết quy ước mới (như `rule_version_bump`, clean.csv, schema...), nên chỉ gỡ được một phần.

Thử trước đóng băng (cùng bộ skill, cùng mô hình): tác tử đọc đủ 3 skill, kết quả code-learn 8/10, data-learn 5/8, logs-learn 6/9. Nghĩa là có đọc nhưng chỉ làm theo bước tổng quát, chưa dịch hết thành quy ước cụ thể của từng họ tác vụ.

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

Tách check kỹ thuật và check quy ước (`check_breakdown.py`):

| condition | role | technical | house rules | mean tokens | read a skill |
|---|---|---|---|---|---|
| baseline | eval | 17/18 | 4/12 | 339,417 | 0/3 |
| baseline | learn | 17/18 | 3/9 | 314,348 | 0/3 |
| subagents | eval | 17/18 | 4/12 | 223,358 | 0/3 |
| subagents | learn | 17/18 | 6/9 | 318,421 | 0/3 |
| skills-auto | eval | 17/18 | 10/12 | 443,545 | 3/3 |
| skills-auto | learn | 17/18 | 5/9 | 484,301 | 3/3 |

- Cả 3 điều kiện đều gần trọn phần kỹ thuật (17/18). Mọi chênh lệch nằm ở nhóm quy ước (`rule_`).
- `subagents` không khác `baseline` vì tác tử không giao việc lần nào (`subagent_calls = 0`). Đúng với H1.
- `skills-auto` là cái duy nhất có lợi thật: 6/6 run đều đọc skill, check quy ước ở đánh giá tăng 4/12 → 10/12. H2 đoán "chỉ giúp tác vụ học" hoá ra sai — skill giúp tác vụ đánh giá nhiều hơn (0.72 → 0.91) vì 3 skill đều tổng quát, không bị overfit vào tác vụ học.
- H3 cũng sai: có skill thì điểm đánh giá (0.91) cao hơn tác vụ học (0.82). Khác biệt không phải do độ khó cố định mà do quy ước mới, và skill có che được hay không.
- Cái giá là token: skills-auto tốn ~464k/run, gấp ~1.4 lần baseline và ~1.7 lần subagents (vì đọc 3 skill và làm thêm mấy file quy ước).

Nhiễu: cùng bộ skill chạy 2 lần (trước/sau đóng băng) thì data-learn 5/8 so 8/8, còn lại trùng. Vậy mấy chênh lệch nhỏ chỉ là nhiễu, đừng đọc là hiệu quả.

## 9. Hạn chế và tính hợp lệ

1. Chỉ 3 tác vụ mỗi loại, mỗi điều kiện chạy đúng 1 lần (n=1), nên khó tách hiệu quả thật với nhiễu.
2. Dù `LAB_TEMPERATURE=0` điểm vẫn dao động giữa các lần (data-learn 5/8 rồi 8/8 cùng 1 bộ skill), và mô hình đôi khi lặp đến hết `recursion_limit`.
3. Tác vụ do giảng viên làm quy ước sẵn; chỉ chạy một mô hình (DeepSeek-V4-Pro-0813).
4. `subagent_calls` đều bằng 0, nên nhận xét về đa tác tử chỉ đúng cho trường hợp "có subagent mà không dùng", chưa nói gì khi nó được gọi thật.

## 10. Kết luận

- H1 đúng: thêm subagent không cải thiện điểm hay tăng token, vì tác tử không giao việc lần nào.
- H2 sai: skill sinh ra giúp tác vụ đánh giá nhiều hơn tác vụ học (0.72 → 0.91), vì 3 skill đều tổng quát chứ không overfit.
- H3 sai: có skill thì điểm đánh giá (0.91) cao hơn tác vụ học (0.82).
- Nói chung: hầu hết lỗi thuộc nhóm quy ước (`rule_`), phần kỹ thuật gần hết rồi (17/18). Skill tự sinh là cách rẻ để gỡ nhóm quy ước, chỉ tốn thêm token (~1.4–1.7 lần).

## Phụ lục: lệnh đã chạy

- `pytest` (offline)
- `python -m lab.runner --condition baseline --tasks learn`
- `python -m lab.runner --condition subagents --tasks learn`
- `python -m lab.curator`
- `python -m lab.runner --condition skills-auto --tasks learn`  (lưu vào `results/skills-auto-dev`)
- `git commit -m "hypotheses"` trước, rồi `git commit --allow-empty -m "freeze skills"` + `git tag freeze`
- `python -m lab.runner --condition baseline --tasks eval`
- `python -m lab.runner --condition subagents --tasks eval`
- `python -m lab.runner --condition skills-auto --tasks all`
- `python -m lab.compare > report/table.md`
- `python scripts/check_breakdown.py`

Chạy trong Docker và verify trên Linux (LF) vì shell của tác tử dùng `/bin/sh`; nếu chạy `verify_freeze.py`/`git diff freeze` trên Windows phải để file là LF (đã đặt `.gitattributes`).
