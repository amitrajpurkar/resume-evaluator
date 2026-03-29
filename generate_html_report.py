#!/usr/bin/env python3
"""
generate_html_report.py
────────────────────────
HTML report generator for the resume analysis pipeline.

Takes a JSON file of candidate analysis data and renders
B&W print-ready HTML reports (one per candidate + a master shortlist).

This is the rendering layer only — candidate analysis data is authored
separately (by Claude or a human reviewer) and passed in via JSON.

Usage:
    python generate_html_report.py --data candidates.json --output ./reports

Input JSON format:
    [
      {
        "name": "Full Name",
        "filename": "Safe_Filename",           # used for output file naming
        "current_title": "Job Title",
        "experience": "16 Years",
        "location": "City",
        "date": "March 29, 2026",
        "score": 72,                           # 0–100 fit score
        "verdict": "Short verdict string",
        "summary": "1–2 sentence summary",
        "schedule": {
          "date": "Mar 30, 2026",
          "time": "9:00 AM",
          "status": "Pending",
          "remarks": ""
        },
        "strengths": [
          {"title": "Strength Area", "points": ["bullet 1", "bullet 2"]}
        ],
        "gaps": [
          {"severity": "major|minor", "title": "Gap Title", "body": "Description"}
        ],
        "obs_good": ["observation 1", "observation 2"],
        "obs_better": ["suggestion 1", "suggestion 2"],
        "reco": "Main recommendation paragraph",
        "questions": ["Interview question 1", "Interview question 2"],
        "reco_close": "Closing recommendation sentence",
        "matrix": [
          ["Skill Name", "Coverage description", "excellent|strong|good|moderate|weak|gap"]
        ]
      }
    ]

Requirements:
    No external dependencies — uses only Python stdlib.
"""

import argparse
import json
import pathlib
import sys


# ─── CSS (shared across all reports) ─────────────────────────────────────────

CSS = """
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Merriweather:ital,wght@0,400;0,700;1,400&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root { --black:#000; --dark:#1a1a1a; --mid:#444; --soft:#666; --rule:#bbb; --rule-lt:#ddd; --bg:#fff; --radius:8px; }
    body { font-family:'Inter',sans-serif; font-size:14.5px; line-height:1.7; color:var(--mid); background:#ebebeb; padding:40px 20px 60px; }
    .page { max-width:860px; margin:0 auto; background:var(--bg); border:1.5px solid var(--rule); border-radius:12px; overflow:hidden; }
    .header { background:#fff; padding:36px 48px 28px; border-bottom:3px solid var(--black); }
    .header-label { font-size:10.5px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--soft); margin-bottom:6px; }
    .header h1 { font-family:'Merriweather',serif; font-size:26px; font-weight:700; color:var(--black); margin-bottom:14px; }
    .header-meta { display:flex; flex-wrap:wrap; gap:18px; font-size:12.5px; color:var(--soft); }
    .header-meta span { display:flex; align-items:center; gap:5px; }
    .fit-banner { display:flex; align-items:center; gap:20px; padding:20px 48px; border-bottom:1px solid var(--rule); }
    .fit-score { flex-shrink:0; width:70px; height:70px; border-radius:50%; border:2.5px solid var(--black); background:#fff; color:var(--black); display:flex; flex-direction:column; align-items:center; justify-content:center; font-weight:700; font-size:19px; line-height:1; }
    .fit-score span { font-size:10px; font-weight:600; color:var(--soft); margin-top:2px; letter-spacing:.05em; text-transform:uppercase; }
    .fit-text h2 { font-size:16px; font-weight:700; color:var(--dark); margin-bottom:4px; }
    .fit-text p { font-size:13px; color:var(--soft); }
    .body { padding:36px 48px 48px; }
    section { margin-bottom:34px; }
    .section-title { display:flex; align-items:center; gap:8px; font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--soft); margin-bottom:16px; padding-bottom:8px; border-bottom:2px solid var(--dark); }
    .cards { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
    .card { border-radius:var(--radius); padding:16px 18px; background:#fff; border:1px solid var(--rule); }
    .card-title { font-weight:700; font-size:13px; color:var(--dark); margin-bottom:7px; }
    .card ul { padding-left:15px; } .card ul li { font-size:12.5px; color:var(--mid); margin-bottom:4px; } .card p { font-size:12.5px; color:var(--mid); }
    .strength-block { border:1px solid var(--rule); border-left:4px solid var(--dark); border-radius:var(--radius); padding:18px 22px; margin-bottom:10px; background:#fff; }
    .strength-block .card-title { color:var(--dark); }
    .strength-block ul { padding-left:16px; } .strength-block ul li { font-size:13px; color:var(--mid); margin-bottom:5px; }
    .gap-block { border-radius:var(--radius); padding:16px 20px; margin-bottom:10px; background:#fff; }
    .gap-block.major { border:1px solid var(--rule); border-left:5px solid var(--dark); }
    .gap-block.minor { border:1px dashed var(--rule); border-left:3px dashed var(--mid); }
    .gap-block .card-title { font-size:13px; margin-bottom:6px; color:var(--dark); }
    .gap-block.major .card-title { font-weight:700; } .gap-block.minor .card-title { font-weight:600; }
    .gap-block p { font-size:12.5px; color:var(--mid); }
    .reco-box { border:2px solid var(--dark); border-radius:var(--radius); padding:20px 24px; background:#fff; }
    .reco-box p { font-size:13.5px; color:var(--mid); margin-bottom:12px; }
    .reco-box ol { padding-left:18px; } .reco-box ol li { font-size:13px; color:var(--mid); margin-bottom:6px; font-style:italic; }
    .schedule-box { border:1px solid var(--rule); border-left:4px solid var(--dark); border-radius:var(--radius); padding:14px 20px; background:#fff; font-size:13px; color:var(--mid); }
    .schedule-box strong { color:var(--dark); }
    table { width:100%; border-collapse:collapse; font-size:13px; border:1.5px solid var(--dark); }
    thead tr { background:#fff; border-bottom:2px solid var(--dark); }
    thead th { padding:10px 14px; text-align:left; font-weight:700; font-size:11px; letter-spacing:.08em; text-transform:uppercase; color:var(--dark); }
    tbody tr { border-bottom:1px solid var(--rule-lt); } tbody tr:nth-child(even) { background:#f8f8f8; }
    tbody td { padding:9px 14px; vertical-align:middle; color:var(--mid); } tbody td:first-child { font-weight:600; color:var(--dark); }
    .badge { display:inline-block; padding:2px 9px; border-radius:999px; font-size:11px; font-weight:700; background:#fff; color:var(--dark); letter-spacing:.02em; }
    .badge.excellent { border:2px solid var(--dark); }
    .badge.strong { border:1.5px solid var(--dark); }
    .badge.good { border:1.5px solid var(--mid); color:var(--mid); }
    .badge.moderate { border:1.5px dashed var(--mid); color:var(--mid); }
    .badge.weak { border:1.5px dashed var(--soft); color:var(--soft); }
    .badge.gap { border:2px dashed var(--dark); font-style:italic; }
    .obs-good, .obs-better { border-radius:var(--radius); padding:14px 18px; margin-bottom:10px; background:#fff; }
    .obs-good { border:1px solid var(--rule); border-left:4px solid var(--dark); }
    .obs-better { border:1px dashed var(--rule); border-left:3px dashed var(--mid); }
    .obs-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; margin-bottom:7px; color:var(--dark); }
    .obs-good ul, .obs-better ul { padding-left:15px; } .obs-good ul li, .obs-better ul li { font-size:12.5px; color:var(--mid); margin-bottom:4px; }
    .footer { text-align:center; font-size:11px; color:var(--soft); padding:16px 48px; border-top:1px solid var(--rule); letter-spacing:.04em; }
    @media print { body { background:#fff; padding:0; } .page { box-shadow:none; border-radius:0; border:none; } section { page-break-inside:avoid; } }
  </style>
"""


# ─── Individual report builder ────────────────────────────────────────────────

def build_candidate_html(c: dict) -> str:
    score    = c["score"]
    schedule = c["schedule"]

    rows = "\n".join(
        f'<tr><td>{r[0]}</td><td>{r[1]}</td>'
        f'<td><span class="badge {r[2]}">{r[2].title()}</span></td></tr>'
        for r in c["matrix"]
    )
    strengths_html = "\n".join(
        f'<div class="strength-block"><div class="card-title">{s["title"]}</div><ul>'
        + "".join(f"<li>{pt}</li>" for pt in s["points"])
        + "</ul></div>"
        for s in c["strengths"]
    )
    gaps_html = "\n".join(
        f'<div class="gap-block {g["severity"]}">'
        f'<div class="card-title">{g["title"]}</div><p>{g["body"]}</p></div>'
        for g in c["gaps"]
    )
    qs_html        = "\n".join(f"<li>{q}</li>" for q in c["questions"])
    obs_good_html  = "".join(f"<li>{o}</li>" for o in c["obs_good"])
    obs_better_html = "".join(f"<li>{o}</li>" for o in c["obs_better"])
    remarks_html = (
        f' &nbsp;|&nbsp; <strong>Remarks:</strong> {schedule["remarks"]}'
        if schedule.get("remarks") else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Resume Analysis – {c['name']}</title>
  {CSS}
</head>
<body>
<div class="page">
  <div class="header">
    <div class="header-label">Resume Analysis Report</div>
    <h1>{c['name']}</h1>
    <div class="header-meta">
      <span>🎯 {c['current_title']}</span>
      <span>📅 {c['date']}</span>
      <span>💼 {c['experience']}</span>
      <span>📍 {c['location']}</span>
    </div>
  </div>
  <div class="fit-banner">
    <div class="fit-score">{score}%<span>Fit</span></div>
    <div class="fit-text">
      <h2>{c['verdict']}</h2>
      <p>{c['summary']}</p>
    </div>
  </div>
  <div class="body">
    <section>
      <div class="section-title"><span>📅</span> Interview Schedule</div>
      <div class="schedule-box">
        <strong>Slot:</strong> {schedule['date']} at {schedule['time']}
        &nbsp;|&nbsp; <strong>Status:</strong> {schedule['status']}{remarks_html}
      </div>
    </section>
    <section>
      <div class="section-title"><span>✅</span> Key Strengths</div>
      {strengths_html}
    </section>
    <section>
      <div class="section-title"><span>⚠️</span> Gaps &amp; Weaknesses</div>
      {gaps_html}
    </section>
    <section>
      <div class="section-title"><span>📋</span> Resume Quality Observations</div>
      <div class="obs-good"><div class="obs-label">The Good</div><ul>{obs_good_html}</ul></div>
      <div class="obs-better"><div class="obs-label">Could Be Better</div><ul>{obs_better_html}</ul></div>
    </section>
    <section>
      <div class="section-title"><span>🏁</span> Recommendation</div>
      <div class="reco-box">
        <p>{c['reco']}</p>
        <ol>{qs_html}</ol>
        <p style="margin-top:14px;margin-bottom:0;font-style:normal;">{c['reco_close']}</p>
      </div>
    </section>
    <section>
      <div class="section-title"><span>📊</span> Skills Coverage Matrix</div>
      <table>
        <thead><tr><th>JD Requirement</th><th>Resume Coverage</th><th>Strength</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
  </div>
  <div class="footer">
    Confidential &middot; Resume Analysis &middot; {c['name']} &middot; {c['date']}
  </div>
</div>
</body>
</html>"""


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate B&W print-ready HTML resume analysis reports."
    )
    parser.add_argument(
        "--data", required=True,
        help="Path to JSON file containing list of candidate analysis objects"
    )
    parser.add_argument(
        "--output", default="./reports/candidates",
        help="Output folder for individual HTML reports (default: ./reports/candidates)"
    )
    args = parser.parse_args()

    data_path = pathlib.Path(args.data)
    if not data_path.exists():
        sys.exit(f"Data file not found: {data_path}")

    candidates = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(candidates, list):
        sys.exit("JSON file must contain a list of candidate objects.")

    out_dir = pathlib.Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating {len(candidates)} individual report(s) → {out_dir}")
    print("─" * 60)

    for c in candidates:
        html = build_candidate_html(c)
        fname = f"{c['filename']}_Analysis.html"
        (out_dir / fname).write_text(html, encoding="utf-8")
        print(f"  ✓ {fname}  (fit={c['score']}%)")

    print("─" * 60)
    print(f"\nDone. Open any file in a browser and Cmd+P / Ctrl+P to print.")
    print("Tip: Run Shortlist_Report.html for the ranked comparison view.")


if __name__ == "__main__":
    main()
