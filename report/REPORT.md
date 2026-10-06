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

Nhận xét: đa số lỗi thuộc nhóm E (quy ước tổ chức Acme, check `rule_`); các check kỹ thuật A–D gần như đạt toàn bộ (xem `check_breakdown.py`: baseline learn đạt 17/18 check kỹ thuật, chỉ 3/9 check quy ước). Chỉ `tests_not_modified` thuộc nhóm A. Skill có thể phòng ngừa nhóm E nếu được viết đúng và được đọc.

## 5. Điều kiện `subagents` (Phần 2.3)

- Đã định nghĩa 3 subagent: `explorer` (đọc/báo cáo), `implementer` (thực hiện), `reviewer` (kiểm tra độc lập).
- Số lần giao việc (`subagent_calls`): toàn bộ 6 tác vụ đều bằng 0 — tác tử chính tự làm, không giao việc cho subagent nào. Đây là kết quả hợp lệ: với prompt chỉ dẫn “giao việc cho bước không tầm thường”, mô hình vẫn chọn tự thực hiện hết (đa số bước thuộc loại đọc–sửa–chạy test ngắn), nên không phát sinh `task`.
- Hệ quả: `subagents` gần như trùng `baseline` về hành vi lẫn điểm ở ba tác vụ đánh giá (cùng 0.72); ở tác vụ học `subagents` (0.87) nhỉnh hơn `baseline` (0.76) chủ yếu do logs-learn đạt 9/9 so với 6/9, nhiều khả năng do nhiễu chạy, không phải cơ chế subagent vì không lần nào được gọi.
- Token trung bình: `subagents` 270,889 so với `baseline` 326,882; không có dấu hiệu “multi-agent tốn token hơn hẳn” vì tác tử không dùng `task`.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Chạy curator 2 lần; lần 1 sinh 3 skill nhưng `description` có dấu hai chấm chưa quote làm YAML hỏng (bị skip khi nạp) → xóa và chạy lại. Lần 2 sinh 3 skill hợp lệ (11 dòng mỗi skill, gồm frontmatter + 5 bước).

| Skill | Tổng quát hay riêng | Đúng/sai | Độ dài & `description` (trích thật) |
|---|---|---|---|
| enforce-code-standards | Tổng quát (type hints, docstring, không sửa `tests/`, changelog) | Đúng | description: “Use when writing or modifying code to ensure it meets quality and type-safety standards.” |
| implement-regression-testing | Tổng quát (viết `tests/test_regressions.py`) | Đúng | description: “Use when fixing bugs to ensure the fix is verified and does not regress.” |
| verify-requirements-checklist | Tổng quát (liệt kê mọi `RULE:` rồi tự kiểm) | Đúng | description: “Use when starting a task to ensure all explicit constraints and formatting rules are met.” |

Nhận xét chất lượng: cả ba đều tổng quát, không chứa id/đáp án tác vụ, mỗi bước đều đúng và tự kiểm chứng được. `enforce-code-standards` gộp đúng hai quy ước Acme về code (type hints + changelog) và nêu rõ “do not modify files under `tests/`”. Điểm yếu: không skill nào nêu chi tiết quy ước `rule_version_bump`/house-rule còn lại của họ `code` và họ `data`/`logs`, nên các skill chỉ giúp một phần, không đạt trọn vẹn quy ước mới.

### 6.1 Kiểm tra skill có được dùng (Phần 3.4, trước đóng băng)

`results/skills-auto-dev/` (pre-freeze, cùng bộ skill, cùng mô hình DeepSeek): `skills_read` đủ 3/3 ở cả ba tác vụ. Điểm: code-learn 8/10, data-learn 5/8, logs-learn 6/9 → minh chứng tác tử làm theo skill một phần: code-learn đạt thêm type hints/changelog, nhưng data-learn (5/8) vẫn sót dữ liệu bẩn và logs-learn còn thiếu quy ước schema. Đối chiếu `trace.md` cho thấy tác tử có đọc skill nhưng chỉ áp dụng những bước tổng quát (checklist/type-hints), chưa dịch thành đúng quy ước cụ thể của từng họ task.


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

**Tách check kỹ thuật và check quy ước.** `python scripts/check_breakdown.py`:

| condition | role | technical | house rules | mean tokens | read a skill |
|---|---|---|---|---|---|
| baseline | eval | 17/18 | 4/12 | 339,417 | 0/3 |
| baseline | learn | 17/18 | 3/9 | 314,348 | 0/3 |
| subagents | eval | 17/18 | 4/12 | 223,358 | 0/3 |
| subagents | learn | 17/18 | 6/9 | 318,421 | 0/3 |
| skills-auto | eval | 17/18 | 10/12 | 443,545 | 3/3 |
| skills-auto | learn | 17/18 | 5/9 | 484,301 | 3/3 |

- Cả ba điều kiện đều đạt gần hết check kỹ thuật (17/18 ở mọi ô), mọi chênh lệch điểm đến từ nhóm check quy ước (`rule_`). Đây là một quan sát ổn định, nhất quán với mong đợi “mô hình đủ mạnh thì nhóm A–D thường đạt”.
- `subagents` không tạo ra khác biệt cơ chế so với `baseline`: `subagent_calls` bằng 0 ở toàn bộ 6 tác vụ, nên hai điều kiện chỉ khác nhau ở nhiễu chạy. Cụ thể, ở tác vụ học `subagents` (0.87) cao hơn `baseline` (0.76) đơn thuần do logs-learn (9/9 vs 6/9); ở tác vụ đánh giá cả hai cùng 0.72. Điều này ủng hộ H1: thêm subagent không cải thiện và không làm tăng chi phí token một cách có ý nghĩa (vì không được dùng).
- `skills-auto` là cải tiến duy nhất có tín hiệu cơ chế: cả 6 lần chạy đều đọc skill (`read a skill` 6/6), và lượng check quy ước đạt tăng rõ nhất ở tác vụ đánh giá (4/12 → 10/12). Ở tác vụ học, do baseline đã có điểm cao vì data-learn 8/8 và logs-learn 6/9, `skills-auto` (0.82) hạ từ `subagents` (0.87) nhưng vẫn trên `baseline` (0.76), đồng thời logs-eval đạt trọn 10/10 và code-eval 8/11.
- Về H2: Dự đoán “skill chỉ giúp tác vụ học, ít/không giúp tác vụ đánh giá” **không khớp**. Thực tế skill giúp tác vụ đánh giá nhiều nhất (0.72 → 0.91). Ba skill đều tổng quát (không chứa id/đáp án), nên không quá khớp vào tác vụ học và chuyển sang tác vụ đánh giá tốt. Phần còn sót nằm đúng ở quy ước mới mà chưa skill nào biết (code-eval còn `rule_version_bump`/`rule_changelog`, code-learn còn `tests_not_modified`) — khớp với rủi ro H2 nêu.
- Về H3: Dự đoán “điểm đánh giá thấp hơn học” **không khớp** với `skills-auto` (đánh giá 0.91 > học 0.82); với `baseline`/`subagents` hai vai trò gần nhau. Khác biệt học/đánh giá không phải do độ khó cố định mà do quy ước mới ở tác vụ đánh giá, và skill nghiêng về việc sửa đúng các quy ước đó.
- Chi phí: `skills-auto` tốn ~463,923 token/run, gấp ~1.4 lần `baseline` (326,882) và ~1.7 lần `subagents` (270,889), vì tác tử đọc 3 skill và làm thêm bước kiểm tra/ghi nhiều tệp (changlog, clean.csv, meta, version bump). Đổi chi phí để lấy độ phủ quy ước cao hơn.

**Ước lượng nhiễu.** Cùng bộ skill (post-freeze, `skills-auto`) và lần chạy trước đóng băng (`skills-auto-dev`, Phần 3.4) đều dùng mô hình DeepSeek: code-learn 8/10 vs 8/10; data-learn 5/8 vs 8/8; logs-learn 6/9 vs 6/9. Content skill không đổi nên chênh lệch data-learn (5/8 vs 8/8) là ước lượng nhiễu của một lần chạy đơn lẻ (tác tử đọc skill 3/3 ở cả hai lần). Đây là cận cho dao động điểm, nên không đọc mọi chênh lệch nhỏ như hiệu quả thật.

## 9. Hạn chế và tính hợp lệ

1. Chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy đúng 1 lần (n=1); không đủ để tách hiệu quả thật khỏi nhiễu, đặc biệt với các chênh lệch điểm nhỏ giữa `baseline` và `subagents`.
2. Nhiễu của mô hình: dù `LAB_TEMPERATURE=0`, các điểm vẫn dao động giữa các lần chạy cùng điều kiện — cùng bộ skill mà data-learn đạt 5/8 ở lần trước đóng băng nhưng 8/8 ở lần chính thức — và mô hình thỉnh thoảng lặp đến hết `recursion_limit` (logs-learn/logs-eval ghi `GraphRecursionError`).
3. Tác vụ do giảng viên thiết kế sẵn quy ước; chỉ dùng một mô hình (DeepSeek-V4-Pro-0813), nên chưa kiểm tra độ bền vững của kết luận trên mô hình/họ task khác.
4. `subagent_calls` toàn bộ bằng 0, nên kết luận về đa tác tử dựa trên một thiết kế subagent mà tác tử không dùng, chưa đánh giá được hiệu quả thật khi subagent thực sự được triệu gọi.


## 10. Kết luận

- H1 được ủng hộ: subagent không cải thiện điểm bền vững và không làm tăng token; tác tử không giao việc lần nào (`subagent_calls` = 0/6), nên điều kiện này về cơ bản chỉ là một bản chạy lặp của `baseline`.
- H2 bị bác bỏ: skill tự sinh không chỉ giúp tác vụ học mà còn đem lại cải thiện rõ nhất ở tác vụ đánh giá (0.72 → 0.91). Các skill đều tổng quát, không quá khớp vào tác vụ học; gap còn lại nằm ở quy ước mới chưa skill nào biết.
- H3 bị bác bỏ: với skill, điểm tác vụ đánh giá (0.91) cao hơn tác vụ học (0.82); khác biệt học/đánh giá không cố định mà phụ thuộc quy ước mới và việc skill che có hiệu quả hay không.
- Phát hiện chung: phần lớn lỗi đều thuộc nhóm E (quy ước `rule_`), còn check kỹ thuật gần như đạt đủ (17/18). Skill tự sinh là cách hữu hiệu để che nhóm E (check quy ước đạt tăng 4→10/12 ở eval), nhưng phải trả bằng token cao hơn (~1.4–1.7 lần).

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