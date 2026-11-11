"""Run the whole test suite and write the four Part-3 reports into docs/.

    python scripts/generate_test_reports.py

Writes: docs/UNIT_TEST_REPORT.md, docs/SYSTEM_VALIDATION_REPORT.md,
        docs/CODE_COVERAGE_REPORT.md, docs/BRANCH_COVERAGE_REPORT.md
Every number comes from a fresh run, nothing is typed in by hand.
"""
import csv, datetime, json, re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
tmp = Path.home() / "pytest_reports_tmp"
tmp.mkdir(exist_ok=True)
junit, covjson = tmp / "junit.xml", tmp / "cov.json"

proc = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--basetemp={tmp / 'pt'}", f"--junitxml={junit}",
     "--cov=app", "--cov-branch", f"--cov-report=json:{covjson}"],
    cwd=ROOT, capture_output=True, text=True)
STAMP = datetime.date.today().isoformat()

# ---------- test results ----------
cases = []
for tc in ET.parse(junit).getroot().iter("testcase"):
    status = "PASS"
    if tc.find("failure") is not None or tc.find("error") is not None:
        status = "FAIL"
    elif tc.find("skipped") is not None:
        status = "SKIP"
    mod = tc.get("classname").split(".")
    kind = "unit" if "unit" in mod else "integration" if "integration" in mod else "smoke"
    cases.append(dict(kind=kind, file=mod[-1] + ".py", name=tc.get("name"),
                      time=float(tc.get("time") or 0), status=status))

def summary(rows):
    p = sum(r["status"] == "PASS" for r in rows)
    return len(rows), p, len(rows) - p

# traceability: requirement -> TC ids (backlog), TC id -> test files that mention it
trace = OrderedDict()
with open(DOCS / "backlog.tsv", encoding="utf-8") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        trace[row["key"]] = (row["title"], row["test_cases"])
tc_files = {}
for py in (ROOT / "tests").rglob("*.py"):
    for name, first, tail in re.findall(r"TC-([A-Za-z]+)-(\d+)((?:\.\.\d+|(?:/\d+)+)?)", py.read_text(encoding="utf-8")):
        nums = [int(first)]
        if tail.startswith(".."):
            nums = range(int(first), int(tail[2:]) + 1)
        elif tail:
            nums += [int(x) for x in tail.split("/") if x]
        for n in nums:
            tc_files.setdefault(f"TC-{name}-{n:02d}", set()).add(py.name)

def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)

def by_file(rows):
    files = OrderedDict()
    for r in sorted(rows, key=lambda r: (r["file"], r["name"])):
        files.setdefault(r["file"], []).append(r)
    return files

# ---------- 1. unit ----------
unit = [c for c in cases if c["kind"] == "unit"]
t, p, f = summary(unit)
lines = [f"# Unit Test Report", "", f"Date of run: {STAMP}  ",
         "Command: `python scripts/generate_test_reports.py` (pytest, tests/unit)", "",
         "## Summary", "", table(["Total", "Passed", "Failed"], [[t, p, f]]), "",
         "Unit tests check one function or service on its own: password hashing, price and discount rules, "
         "payment signature, inventory rules and catalogue helpers.", "", "## Results by file", ""]
for fn, rows in by_file(unit).items():
    a, b, c = summary(rows)
    lines += [f"### {fn} ({b}/{a} passed)", "",
              table(["Test", "Result"], [[r["name"], r["status"]] for r in rows]), ""]
(DOCS / "UNIT_TEST_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

# ---------- 2. system validation ----------
sysr = [c for c in cases if c["kind"] != "unit"]
t, p, f = summary(sysr)
lines = ["# System Validation Report", "", f"Date of run: {STAMP}  ",
         "Scope: integration and system tests (tests/integration, tests/test_smoke.py). Each test calls the real "
         "API with a fresh temporary database, so the router, rules and database work together.", "",
         "## Summary", "", table(["Total", "Passed", "Failed"], [[t, p, f]]), "",
         "## Requirement traceability (SRS -> test case -> automated result)", ""]
rows = []
for key, (title, tcs) in trace.items():
    ids = [x.strip() for x in re.split(r"[,;/ ]+", tcs) if x.strip().startswith("TC-")]
    if not ids:
        rows.append([key, title, tcs or "-", "-", "Not automated (see Test Summary)"]); continue
    files = sorted({fn for i in ids for fn in tc_files.get(i, [])})
    res = {c["status"] for c in cases if c["file"] in files}
    rows.append([key, title, ", ".join(ids), ", ".join(files) or "-",
                 "PASS" if res == {"PASS"} else ("FAIL" if "FAIL" in res else "Not automated (see Test Summary)")])
lines += [table(["Requirement", "Title", "Test case(s)", "Automated in", "Result"], rows), "",
          "## Results by file", ""]
for fn, rs in by_file(sysr).items():
    a, b, c = summary(rs)
    lines += [f"### {fn} ({b}/{a} passed)", "", table(["Test", "Result"], [[r["name"], r["status"]] for r in rs]), ""]
lines += ["## Limits", "",
          "Usability results with real people are recorded in docs/USABILITY_TEST.md. "
          "Automated tests cannot prove the absence of every defect."]
(DOCS / "SYSTEM_VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

# ---------- 3 and 4. coverage ----------
cov = json.loads(covjson.read_text())
files = cov["files"]
tot = cov["totals"]
def pct(a, b): return "100.0%" if b == 0 else f"{100 * a / b:.1f}%"
rows_l, rows_b = [], []
for name, d in sorted(files.items()):
    s = d["summary"]
    if s["num_statements"] == 0 and s["num_branches"] == 0: continue
    rows_l.append([name, s["num_statements"], s["missing_lines"], pct(s["covered_lines"], s["num_statements"]),
                   ", ".join(map(str, d["missing_lines"])) or "-"])
    rows_b.append([name, s["num_branches"], s["covered_branches"], s["missing_branches"],
                   pct(s["covered_branches"], s["num_branches"])])
lines = ["# Code Coverage Report", "", f"Date of run: {STAMP}  ", "Tool: coverage.py through pytest-cov, `--cov=app`.", "",
         "## Summary", "",
         table(["Statements", "Missed", "Line coverage"],
               [[tot["num_statements"], tot["missing_lines"], pct(tot["covered_lines"], tot["num_statements"])]]), "",
         "Line coverage = the share of program lines that ran at least once during the tests.", "",
         "## Per file", "", table(["File", "Statements", "Missed", "Covered", "Missed line numbers"], rows_l), "",
         "## Reading the gaps", "",
         "Missed lines are mostly defensive error paths (for example a database error branch) and the audit "
         "log helper that is exercised through the admin features."]
(DOCS / "CODE_COVERAGE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

lines = ["# Branch Coverage Report", "", f"Date of run: {STAMP}  ", "Tool: coverage.py with `--cov-branch`.", "",
         "## Summary", "",
         table(["Branches", "Covered", "Missed", "Branch coverage"],
               [[tot["num_branches"], tot["covered_branches"], tot["missing_branches"],
                 pct(tot["covered_branches"], tot["num_branches"])]]), "",
         "Branch coverage counts each side of every if/else and loop decision. A line can run while only one "
         "side of its decision was taken, so branch coverage is the stricter measure.", "",
         "## Per file", "", table(["File", "Branches", "Covered", "Missed", "Branch coverage"], rows_b)]
(DOCS / "BRANCH_COVERAGE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

print(proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr[-300:])
print("reports written to", DOCS)
sys.exit(0 if proc.returncode == 0 else 1)
