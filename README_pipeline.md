# Resume Analysis Pipeline

Re-runnable pipeline for batch resume analysis against a job description.

## Files

| File | Purpose |
|---|---|
| `extract_resumes.py` | Extract raw text from PDF/DOCX resumes → JSON |
| `generate_html_report.py` | Render per-candidate HTML reports from analysis JSON |
| `_job-description.md` | Job description for the role |
| `_schedule.md` | Interview schedule |
| `reports/candidates/` | Individual B&W HTML analysis per candidate |
| `reports/Shortlist_Report.html` | Master ranked shortlist with tech comparison |

## How to Re-run for a New Batch

### Step 1 — Install dependencies
```bash
pip install pdfplumber python-docx
```

### Step 2 — Extract resume text
```bash
python extract_resumes.py \
  --folder /path/to/new/resumes \
  --output extracted_resumes.json
```

### Step 3 — Author analysis data
Open Claude (Cowork or Claude Code) and provide:
- The extracted JSON from Step 2
- The job description markdown
- The interview schedule markdown

Ask Claude to produce `candidates_analysis.json` using the same schema
as the existing reports (see `generate_html_report.py` docstring for the full format).

### Step 4 — Generate HTML reports
```bash
python generate_html_report.py \
  --data candidates_analysis.json \
  --output ./reports/candidates
```

### Step 5 — Open and print
Open any HTML file in Chrome/Safari → Cmd+P → Print (B&W, optimised for paper).

## Report Design Notes
- All reports use outline-only borders (no fill colours) for ink-efficient B&W printing.
- Individual reports: one page per candidate with fit score, strengths, gaps, skills matrix.
- Shortlist report: ranked table, tech coverage comparison, interview schedule, hiring decision framework.
