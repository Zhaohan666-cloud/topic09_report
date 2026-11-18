# EEEN3008J Group Project — Topic 09

**Freshness-aware wireless sensor scheduling (Age of Information)**

Group project, Autumn 2026/27. Deadline: **20 Nov 2026, 23:59 Dublin time**.
Submission: one report per group, max 15 pages single column (8 double),
appendices excluded. AI-use disclosure statement mandatory.

## Contents

| Path | What it is |
|---|---|
| `Topic09_Group_Report.docx` | The report (regenerate with `code/make_report.py`) |
| `code/aoi_sim.py` | Time-slotted simulator + experiments E1/E2 + verification |
| `code/make_figures.py` | All figures and equation images |
| `code/make_report.py` | Builds the .docx; injects numbers from `results/` |
| `results/` | Raw per-run data (`main_results.json`, `runs.jsonl`), summaries (`summary_e1.csv`, `summary_e2.csv`), `verification.json`, `run_log.txt` |
| `figures/` | All PNGs used by the report |

## Reproduce everything

```bash
python code/aoi_sim.py        # ~6-8 min: verification + E1 + E2
python code/make_figures.py   # figures + equation images
python code/make_report.py    # rebuilds the .docx
```

Requirements: Python 3.10+, numpy, matplotlib, python-docx.

## Model in one paragraph

Four periodic sensors feed a gateway queue; the shared link serves one
packet per slot with success probability 1−p (no retransmission). Three
policies: **FIFO** (queue 20, tail drop), **LRP** (keep newest sample per
sensor, transmit most recent), **AoG** (same queue, transmit the sample
with the largest freshness gain g_i − τ_i). All policies share the same
arrival phases and per-slot loss draws (common random numbers, paired
seeds, run-level 95% t-CIs, 10 seeds per configuration).

## Headline findings

- PDR is **identical** across policies at every load — same channel, same
  airtime.
- Under overload (ρ = N/T > 1) FIFO's mean AoI explodes (it tail-drops
  newest arrivals and structurally starves co-phased sensors); LRP/AoG
  stay within a few slots.
- Under priority imbalance LRP starves the slow group; AoG balances.
- Below ~half capacity all policies coincide (honest negative case).
- Verified against analytic sawtooth means (error 0.00%) and exact packet
  conservation on all 630 runs.
