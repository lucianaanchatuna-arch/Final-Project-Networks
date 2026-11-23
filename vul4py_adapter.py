"""Small, defensive adapter around the official Vul4Py workspace layout."""
from __future__ import annotations

import json
import csv
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Case:
    case_id: str
    workspace: Path


def eligible_cases(vul4py_root: Path) -> list[Case]:
    """Return only workspaces explicitly marked OK by Vul4Py's scan report."""
    report = vul4py_root / "workspaces" / "scan_report.tsv"
    if not report.exists():
        return []
    cases: list[Case] = []
    with report.open(encoding="utf-8", errors="replace", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            # Vul4Py currently writes named columns: cve_id, status, verdict_src, ...
            case_id = row.get("cve_id", "").strip()
            if case_id and row.get("status", "").strip().upper() == "OK":
                workspace = vul4py_root / "workspaces" / case_id
                if (workspace / "vulnerable").is_dir() and (workspace / "meta.json").is_file():
                    cases.append(Case(case_id, workspace))
    return sorted(cases, key=lambda item: item.case_id)


def source_context(case: Case, limit: int = 120_000) -> str:
    """Use metadata changed-code paths first; never read fixed/ or test results."""
    meta = json.loads((case.workspace / "meta.json").read_text(encoding="utf-8"))
    vulnerable = case.workspace / "vulnerable"
    requested = meta.get("new_code_files") or []
    paths = [vulnerable / item for item in requested]
    paths = [path for path in paths if path.is_file() and path.suffix == ".py"]
    if not paths:
        paths = sorted(path for path in vulnerable.rglob("*.py") if "test" not in str(path.relative_to(vulnerable)).lower())
    chunks, used = [], 0
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        block = f"\n### {path.relative_to(vulnerable)}\n```python\n{text}\n```\n"
        if used + len(block) > limit:
            break
        chunks.append(block)
        used += len(block)
    if not chunks:
        raise RuntimeError("No Python source selected from vulnerable workspace")
    return "".join(chunks)


def run_evaluator(vul4py_root: Path, case_id: str) -> tuple[bool, str]:
    command = [sys.executable, "scripts/evaluate.py", "--agent", "student", "--vuln-id", case_id]
    completed = subprocess.run(command, cwd=vul4py_root, text=True, capture_output=True, timeout=1800)
    return completed.returncode == 0, completed.stdout + completed.stderr


def normalize_eval(eval_path: Path) -> dict:
    """Map the real evaluator schema, preserving unavailable values as None."""
    if not eval_path.exists():
        return {"patch_applied": None, "functional_test_pass": None, "security_test_pass": None, "evaluation_error": "eval.json missing"}
    raw = json.loads(eval_path.read_text(encoding="utf-8"))
    functional_rc, exploit_rc = raw.get("functional_rc"), raw.get("exploit_rc")
    return {
        "patch_applied": raw.get("apply_ok"),
        "functional_test_pass": functional_rc in (0, 999) if functional_rc is not None else None,
        "security_test_pass": exploit_rc == 0 if exploit_rc is not None else None,
        "evaluation_error": raw.get("notes", ""),
        "raw": raw,
    }
