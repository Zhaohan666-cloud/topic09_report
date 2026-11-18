# Update notes — repo sync with the final report

The report was revised after the initial commit (measurement definitions,
section 6.2 rewording, corrected references). Three things in the repo no
longer match, and two new ones are missing.

## 1. `code/make_figures.py` — bug fix (must)

`fig2_sawtooth()` called `simulate(..., warmup=0)`. In `aoi_sim.simulate()`
the check `if t == warmup:` tests the age sentinel before any delivery has
happened, so `stats_valid` stays `False` and the returned `trace` is empty:
the committed `figures/fig2_sawtooth.png` therefore showed nothing but the
dotted 3.5 line. Fixed by using `warmup=T` (and a longer window, explicit
limits), so the sawtooth actually appears.

`fig6_imbalance()` printed `rho` with `:.2f` (1.125 -> 1.13) and put the
off-scale bar label above the axes, where it was clipped. Fixed with `:g`
and a label anchored inside the bar.

## 2. `figures/fig2_sawtooth.png`, `figures/fig6_imbalance.png` — regenerated (must)

These are the two images embedded in the revised report. Regenerate with
`python code/make_figures.py`.

## 3. `code/random_order_check.py`, `results/random_order_check.txt` — new (should)

Section 6.2 now quotes the intra-slot ordering sensitivity (27,501 -> 23.0
at T = 2, 13,752 -> 21.5 at T = 3, slow sensors 32,967/38,458 -> 29.6/32.4).
Those numbers had no script in the repo. The new script reproduces them and
also shows that LRP and AoG are unchanged, which is the point of the check.

`aoi_sim.simulate()` is deliberately left untouched: the script duplicates
its loop so that `results/main_results.json` keeps reproducing exactly.

## 4. `README.md` — wording (should)

"structurally starves co-phased sensors" and "error 0.00%" no longer match
the report (starvation is tail drop + fixed service order; the N = 4 cases
are 0.7% and 6.6% off). Also lists the new script.

## 5. `Topic09_Group_Report.docx` — replace (should)

The committed .docx is the pre-revision report. Upload
`Topic09_Group_Report_final.docx` as `Topic09_Group_Report.docx` (and the
matching PDF if you keep one in the repo).

## Not changed, on purpose

- `code/aoi_sim.py`: `summarise_e2()` reports sensor 0 as the "fast" value
  and sensor 2 as the "slow" value, not the two-sensor group mean
  (19.86 / 35,713). The report now says so in the Table 6 caption instead
  of changing the numbers, which would also require regenerating
  `summary_e2.csv`, Fig. 6 and Table 6. Flag it if you would rather do that.
- `code/make_report.py` still builds the pre-revision text. Re-running it
  overwrites the submitted .docx; the README now says so.

## Committing

```bash
# from a clone of the repo
copy <this folder>\code\make_figures.py        code\
copy <this folder>\code\random_order_check.py  code\
copy <this folder>\figures\*.png               figures\
copy <this folder>\results\random_order_check.txt results\
copy <this folder>\README.md                   .
copy Topic09_Group_Report_final.docx           Topic09_Group_Report.docx

git add -A
git commit -m "Sync report revision: fix fig2 trace bug, add intra-slot order check, correct README claims"
git push
```

On the GitHub web UI each file can be replaced with *Add file > Upload files*
(drag the whole folder structure onto the repo page).
