# EEEN3008J Group Project — Topic 09

**Freshness-aware wireless sensor scheduling (Age of Information)**

Group project, Autumn 2026/27.
Submission: one report per group, max 15 pages single column (8 double),
appendices excluded. AI-use disclosure statement mandatory.

## Contents

| Path | What it is |
|---|---|
| `code/aoi_sim.py` | Time-slotted simulator + experiments E1/E2 + verification |
| `code/make_figures.py` | All figures and equation images |
| `code/make_report.py` | Builds the .docx; injects numbers from `results/` |
| `code/random_order_check.py` | Sensitivity check behind Section 6.2 (intra-slot ordering) |
| `results/` | Raw per-run data (`main_results.json`, `runs.jsonl`), summaries (`summary_e1.csv`, `summary_e2.csv`), `verification.json`, `run_log.txt`, `run_log.txt` |
| `figures/` | All PNGs used by the report |

## Reproduce everything

```bash
python code/aoi_sim.py            # ~6-8 min: verification + E1 + E2
python code/make_figures.py       # figures + equation images
python code/random_order_check.py # ~4 min: intra-slot order sensitivity (Sec. 6.2)
python code/make_report.py        # rebuilds the .docx
```

Requirements: Python 3.10+, numpy, matplotlib, python-docx.

Note: `Topic09_Group_Report.docx` is the authoritative version. `make_report.py`
still rebuilds the *original* generated text, so re-running it will overwrite the
hand edits made after generation. It is kept for the build pipeline, not as a
byte-exact regenerator.

## Model in one paragraph

Four periodic sensors feed a gateway queue; the shared link serves one
packet per slot with success probability 1−p (no retransmission). Three
policies: **FIFO** (queue 20, tail drop, co-arriving sensors queued in
ascending sensor-index order), **LRP** (keep newest sample per sensor,
transmit most recent), **AoG** (same queue, transmit the sample with the
largest freshness gain g_i − τ_i). All policies share the same arrival
phases and per-slot loss draws (common random numbers, paired seeds,
run-level 95% t-CIs, 10 seeds per configuration).

## Headline findings

- PDR is **identical** across policies at every load — same channel, same
  airtime.
- Under overload (ρ = N/T > 1) FIFO's mean AoI departs from LRP/AoG by
  more than an order of magnitude: tail drop combined with the fixed
  service order starves the sensors served last. At T = 2 the mean AoI is
  27,501 slots, almost all of it contributed by sensors that never get
  through.
- That starvation term is **order-dependent, not intrinsic to FIFO**: with
  the intra-slot order randomised (Section 6.2, `random_order_check.py`)
  FIFO drops to 23.0 slots at T = 2 and 21.5 at T = 3, while LRP and AoG
  are unchanged to the last digit. FIFO is still an order of magnitude
  behind AoG, but the ranking is unchanged.
- Under priority imbalance LRP starves the slow group; AoG balances
  (FIFO's slow-sensor AoI is order-dependent too: 32,967 → 29.6 slots).
- Below ~half capacity all policies coincide (honest negative case).
- Verified against analytic sawtooth means (0.00% for N = 1; 0.7% at
  T = 16 and 6.6% at T = 8 for N = 4, where sensors collide in a slot) and
  exact packet conservation on all 630 runs.
