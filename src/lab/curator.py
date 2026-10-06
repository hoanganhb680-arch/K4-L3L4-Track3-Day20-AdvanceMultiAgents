"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ)."""
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems

def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md)."""
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------

PROMPT_TEMPLATE = (
    "You write SKILLs for a coding and data-analysing agent.\n"
    "Below are the FAILED checks (name and feedback from the review bot) and the end of the run trace.\n"
    "Find the GENERAL process mistakes (not task-specific answers) and write at most {max_skills} short skills "
    "that help avoid those mistakes on NEW tasks of the same kind.\n\n"
    "Rules:\n"
    "- Skills must be general: no task id, no file names specific to one task, no answers or numbers.\n"
    "- Every skill is a YAML frontmatter block followed by a checklist body.\n"
    "- The `name:` value MUST be lower-case ASCII letters, digits and hyphens only, with NO spaces and NO upper-case "
    "letters (for example `check-data-quality`). It must be exactly the same as the text right after `=== SKILL: `.\n"
    "- The `description:` value MUST be a single plain sentence starting exactly with `Use when ` (for example "
    "`description: Use when analysing a tabular file before computing any number.`). Do not put any other colon inside "
    "the description value, and do not prefix it with words like `WHEN TO USE:`.\n"
    "- The body must be at most 40 lines of numbered, imperative, self-checkable steps. Do not write a literal "
    "`<body>` placeholder line; write the real step list directly.\n"
    "- Output format, exactly, with `=== SKILL:` and a lowercase name on the first line:\n"
    "=== SKILL: <name> ===\n"
    "---\n"
    "name: <name>\n"
    "description: Use when <trigger situation>\n"
    "---\n"
    "<numbered step list>\n"
    "=== END ===\n\n"
    "{runs}"
)
def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file."""
    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    out_dir = Path(out_dir)
    results_dir = Path(results_dir)

    runs = []
    for run_file in sorted((results_dir / source_condition).glob("*/run.json")):
        r = json.loads(run_file.read_text(encoding="utf-8"))
        if r.get("role") != "learn":
            continue
        trace_file = run_file.parent / "trace.md"
        trace = ""
        if trace_file.exists():
            trace = trace_file.read_text(encoding="utf-8")[-6000:]
        failed = [
            {"name": c["name"], "detail": c.get("detail", "")}
            for c in r.get("checks", [])
            if not c.get("passed")
        ]
        runs.append({
            "task": r.get("task", run_file.parent.name),
            "failed": failed,
            "trace": trace,
        })

    if not any(run["failed"] for run in runs):
        print("warning: no failed checks in the learning runs (not calling the model)")
        return []

    model = model if model is not None else make_model()

    runs_text = []
    for run in runs:
        if not run["failed"]:
            continue
        lines = [f"## Run: {run['task']}"]
        for f in run["failed"]:
            lines.append(f"- FAILED check `{f['name']}`: {f['detail']}")
        if run["trace"]:
            lines.append(f"Trace tail:\n```\n{run['trace']}\n```")
        runs_text.append("\n".join(lines))

    prompt = PROMPT_TEMPLATE.format(max_skills=max_skills, runs="\n\n".join(runs_text))
    reply = model.invoke(prompt).content
    if isinstance(reply, list):
        reply = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in reply)
    reply = str(reply)

    written = []
    for name, text in parse_skill_blocks(reply):
        if len(written) >= max_skills:
            break
        if validate_skill(text, expected_name=name):
            continue
        skill_dir = out_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        path = skill_dir / "SKILL.md"
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written

if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)