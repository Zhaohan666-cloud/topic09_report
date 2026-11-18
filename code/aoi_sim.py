"""
EEEN3008J Group Project - Topic 09
Freshness-aware wireless sensor scheduling (Age of Information)

Time-slotted simulator and experiment runner.

Model
-----
- N sensors generate one timestamped update every T_s slots (per-sensor
  period, random phase drawn once per seed and shared across all policies,
  so runs are paired).  Several sensors may generate in the same slot.
- A gateway keeps a queue and transmits ONE packet per slot over a shared
  wireless link; a transmission succeeds with probability (1-p).  Failed
  transmissions are lost (no retransmission in this model).
- The loss process is a per-slot uniform draw u[t], shared across policies:
  any policy transmitting in slot t succeeds iff u[t] >= p (common random
  numbers -> paired comparison, validation-guide step 7).
- AoI of sensor i at end of slot t:  Delta_i(t) = t - tau_i, where tau_i is
  the generation time of the newest update of sensor i received so far.

Policies
--------
- fifo : finite FIFO queue (capacity K, tail drop on overflow), transmits
         the oldest queued packet.
- lrp  : latest-sample replacement (LCFS with in-queue preemption): keeps at
         most one sample per sensor (a new sample replaces the queued one);
         transmits the most recently generated sample.
- aog  : AoI-gain rule (max-weight style): same queue discipline as lrp,
         transmits the sample with the largest freshness gain
             G_i(t) = g_i(t) - tau_i(t)
         (generation time of the queued sample minus newest received
         generation time); ties broken by the older sample.

Experiments
-----------
E1 symmetric load  : all sensors share period T in {2,3,4,8,16,32}
                     (offered load rho = N/T from 2.0 down to 0.125),
                     p in {0, 0.1, 0.3}.
E2 priority imbalance: fast group (sensors 0,1) and slow group (2,3) with
                     periods (T_fast, T_slow) in {(2,8),(2,16),(4,16)},
                     p = 0.1.  Reported per group to expose starvation.

Usage
-----
  python aoi_sim.py            # full experiment + verification (~6 min)

Outputs into ../results/:  main_results.json, summary_e1.csv,
                           summary_e2.csv, verification.json
"""

import json
import math
import os
from collections import deque

import numpy as np

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
N_SENSORS = 4
QUEUE_CAP = 20                 # FIFO queue capacity (packets)
N_SLOTS = 100_000              # simulated slots per run
WARMUP = 10_000                # first 10% slots excluded from statistics
SEEDS = list(range(10))
T_VALUES = [2, 3, 4, 8, 16, 32]        # E1: generation interval sweep
P_VALUES = [0.0, 0.1, 0.3]             # E1: loss probability
IMBALANCE = [(2, 8), (2, 16), (4, 16)]  # E2: (T_fast, T_slow)
P_IMBALANCE = 0.1
POLICIES = ["fifo", "lrp", "aog"]

NEG = -(10 ** 9)               # 'never delivered' sentinel for tau

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "results")


# ----------------------------------------------------------------------
# Paired randomness shared by all policies for a given seed
# ----------------------------------------------------------------------
def shared_randomness(seed, n_slots, n_sensors):
    """Per-sensor arrival phases, per-slot loss uniforms and per-slot
    tie-break uniforms.

    The same master seed is used for every policy, so all policies face an
    identical arrival process and identical per-slot loss outcomes
    (common random numbers).
    """
    rng = np.random.default_rng(seed)
    phases = rng.integers(0, 1 << 30, size=n_sensors)
    loss_u = rng.random(n_slots)
    tb_u = rng.random(n_slots)
    return phases, loss_u, tb_u


def arrival_schedule(phases, periods, n_slots, n_sensors):
    """arrv[s][t] = True iff sensor s generates an update at slot t.

    Multiple sensors may generate in the same slot (random phases can
    collide), so a per-sensor schedule is used; no arrival is ever merged
    or dropped by the schedule itself.
    """
    if np.isscalar(periods):
        periods = [periods] * n_sensors
    t = np.arange(n_slots)
    return [(((t - int(phases[s] % periods[s])) % periods[s]) == 0).tolist()
            for s in range(n_sensors)]


# ----------------------------------------------------------------------
# Simulator
# ----------------------------------------------------------------------
def simulate(policy, periods, p, seed, n_slots=N_SLOTS, n_sensors=N_SENSORS,
             k=QUEUE_CAP, warmup=WARMUP, collect_trace=False, trace_sensor=0):
    """Run one simulation; return a dict of run-level metrics.

    `periods` may be a scalar (shared by all sensors) or a per-sensor list.
    `collect_trace` records the end-of-slot age of `trace_sensor` only.
    """
    if np.isscalar(periods):
        periods = [periods] * n_sensors
    phases, loss_u, tb_u = shared_randomness(seed, n_slots, n_sensors)
    arrv = arrival_schedule(phases, periods, n_slots, n_sensors)
    # plain Python lists in the hot loop: no per-slot numpy scalar
    # extraction (faster, and avoids an interpreter crash observed with
    # sustained numpy scalar indexing on this CPython build)
    loss_u = loss_u.tolist()
    tb_u = tb_u.tolist()

    tau = [NEG] * n_sensors            # newest received generation time
    generated = [0] * n_sensors
    delivered = [0] * n_sensors
    failed_tx = 0
    dropped_overflow = 0               # FIFO tail drop
    replaced = 0                       # lrp/aog old-sample replacement

    age_sum = 0.0                       # window sum of system mean age
    age_sum_sens = [0.0] * n_sensors    # window sum of per-sensor age
    window_slots = 0
    peaks = []                          # peak age just before each improving delivery
    stale_del = 0                       # delivered sample older than receiver state
    improving_del = 0
    lag_sum = 0                         # delivery lag sum: t - g at delivery
    lag_n = 0
    trace = [] if collect_trace else None

    q = deque() if policy == "fifo" else None
    qs = [None] * n_sensors if policy in ("lrp", "aog") else None
    stats_valid = True

    for t in range(n_slots):
        # ---- arrivals (slot start; several sensors may arrive) --------
        for s in range(n_sensors):
            if arrv[s][t]:
                generated[s] += 1
                if policy == "fifo":
                    if len(q) >= k:
                        dropped_overflow += 1
                    else:
                        q.append((t, s))
                else:  # lrp / aog: keep only the latest sample per sensor
                    if qs[s] is not None:
                        replaced += 1
                    qs[s] = t

        # ---- transmission (during slot) ------------------------------
        # NOTE: no generator expressions / comprehensions inside the slot
        # loop - this CPython build raises SystemError on some of them in
        # long-running loops.
        tx = None
        if policy == "fifo":
            if q:
                tx = q.popleft()
        else:
            cand = []
            for j in range(n_sensors):
                if qs[j] is not None:
                    cand.append(j)
            if cand:
                if policy == "lrp":     # newest generated sample first;
                    # ties (same-slot generation) broken uniformly at random
                    # so the baseline is not weakened by a deterministic
                    # first-index rule that would starve co-phased sensors
                    newest = -1
                    for j in cand:
                        if qs[j] > newest:
                            newest = qs[j]
                    tied = []
                    for j in cand:
                        if qs[j] == newest:
                            tied.append(j)
                    if len(tied) == 1:
                        i = tied[0]
                    else:
                        i = tied[int(tb_u[t] * len(tied)) % len(tied)]
                else:                   # aog: max freshness gain g_i - tau_i,
                    i = cand[0]         # ties -> older sample first
                    best = (qs[i] - tau[i], qs[i])
                    for j in cand[1:]:
                        key = (qs[j] - tau[j], qs[j])
                        if key > best:
                            best = key
                            i = j
                tx = (qs[i], i)
                qs[i] = None

        if tx is not None:
            g, i = tx
            if loss_u[t] >= p:          # delivered at end of slot
                delivered[i] += 1
                if t >= warmup and stats_valid:
                    lag_sum += t - g
                    lag_n += 1
                    if g > tau[i]:
                        if tau[i] > NEG // 2:
                            peaks.append(t - tau[i])   # peak before reset
                        improving_del += 1
                    else:
                        stale_del += 1                 # useless delivery
                tau[i] = max(tau[i], g)
            else:
                failed_tx += 1          # packet lost; no retransmission

        # ---- age bookkeeping (end of slot, after delivery) -----------
        if t == warmup:
            # a sensor never delivered during warm-up would poison window
            # statistics with the sentinel value: flag the run instead
            for x in tau:
                if x <= NEG // 2:
                    stats_valid = False
                    break
        if t >= warmup and stats_valid:
            slot_total = 0
            for i in range(n_sensors):
                a = t - tau[i]
                age_sum_sens[i] += a
                slot_total += a
            age_sum += slot_total / n_sensors
            window_slots += 1
            if collect_trace:
                trace.append(t - tau[trace_sensor])  # Delta(t), end-of-slot

    # ---- conservation check (whole run) ------------------------------
    if policy == "fifo":
        in_queue_end = len(q)
    else:
        in_queue_end = 0
        for x in qs:
            if x is not None:
                in_queue_end += 1
    lhs = sum(generated)
    rhs = sum(delivered) + failed_tx + dropped_overflow + replaced + in_queue_end
    conservation_ok = (lhs == rhs)

    # any sensor never delivered, or poisoned window -> failed run
    # (counted and reported as a failure, never silently discarded)
    all_delivered = True
    for d in delivered:
        if d <= 0:
            all_delivered = False
    run_ok = all_delivered and stats_valid and window_slots > 0
    mean_aoi_sens = []
    for a in age_sum_sens:
        mean_aoi_sens.append(a / window_slots if window_slots
                             else float("nan"))

    return {
        "policy": policy, "periods": list(periods), "p": p, "seed": seed,
        "mean_aoi": age_sum / window_slots if window_slots else float("nan"),
        "mean_aoi_sens": mean_aoi_sens,
        "peak_aoi": float(np.mean(peaks)) if peaks else float("nan"),
        "n_peaks": len(peaks),
        "pdr": sum(delivered) / max(1, sum(generated)),
        "stale_frac": stale_del / max(1, stale_del + improving_del),
        "mean_lag": lag_sum / lag_n if lag_n else float("nan"),
        "failed_tx": failed_tx,
        "generated": sum(generated), "delivered": sum(delivered),
        "delivered_sens": list(delivered), "generated_sens": list(generated),
        "dropped": dropped_overflow, "replaced": replaced,
        "conservation_ok": conservation_ok, "run_ok": run_ok,
        "trace": trace,
    }


# ----------------------------------------------------------------------
# Statistics: mean +/- 95% CI over independent seeds (run-level)
# ----------------------------------------------------------------------
T_CRIT_9DF = 2.262  # two-sided 97.5% quantile, t distribution, df = 9


def agg(runs, key):
    """mean, half-width of 95% CI, n (run-level samples)."""
    vals = [r[key] for r in runs if r["run_ok"]]
    n = len(vals)
    m = float(np.mean(vals))
    hw = T_CRIT_9DF * float(np.std(vals, ddof=1)) / math.sqrt(n) if n > 1 else 0.0
    return m, hw, n


def paired_diff(runs_a, runs_b, key):
    """CI of mean(a - b), pairing runs by seed."""
    da = {r["seed"]: r for r in runs_a}
    db = {r["seed"]: r for r in runs_b}
    diffs = [da[s][key] - db[s][key] for s in sorted(da)
             if s in db and da[s]["run_ok"] and db[s]["run_ok"]]
    n = len(diffs)
    m = float(np.mean(diffs))
    hw = T_CRIT_9DF * float(np.std(diffs, ddof=1)) / math.sqrt(n) if n > 1 else 0.0
    return m, hw, n


# ----------------------------------------------------------------------
# Baseline verification (validation-guide step 4)
# ----------------------------------------------------------------------
def verify_baseline():
    out = []
    for T in (8, 16):
        theory = (T - 1) / 2.0        # single sensor, no loss, no queueing:
        runs = []                     # ideal sawtooth ages 0,1,...,T-1
        for seed in range(5):
            runs.append(simulate("fifo", T, 0.0, seed, n_sensors=1))
        sim_mean = float(np.mean([r["mean_aoi"] for r in runs]))
        err = abs(sim_mean - theory) / theory * 100.0
        out.append({
            "case": f"N=1, p=0, T={T}, FIFO",
            "theory": theory, "sim": sim_mean, "err_pct": err,
            "conservation_all_ok": all(r["conservation_ok"] for r in runs),
        })
    return out


# ----------------------------------------------------------------------
# Experiments
# ----------------------------------------------------------------------
def run_grid(grid, tag):
    """grid: list of (periods, p). Returns list of run dicts.

    Each run is checkpointed to results/runs.jsonl so that a crash loses at
    most one run and the experiment can be resumed.
    """
    runs = []
    total = len(grid) * len(POLICIES) * len(SEEDS)
    done = 0
    ckpt = os.path.join(RESULTS_DIR, "runs.jsonl")
    with open(ckpt, "a", encoding="utf-8") as ck:
        for periods, p in grid:
            for pol in POLICIES:
                for seed in SEEDS:
                    r = simulate(pol, periods, p, seed, n_slots=N_SLOTS,
                                 warmup=WARMUP)
                    runs.append(r)
                    ck.write(json.dumps(
                        {k: v for k, v in r.items() if k != "trace"}) + "\n")
                    ck.flush()
                done += len(SEEDS)
                print(f"  [{tag}] {done}/{total}  periods={periods} "
                      f"p={p} {pol}", flush=True)
    return runs


def summarise_e1(runs):
    rows = []
    for T in T_VALUES:
        for p in P_VALUES:
            sel = lambda pol: [r for r in runs if r["policy"] == pol
                               and r["periods"] == [T] * N_SENSORS
                               and r["p"] == p]
            row = {"T": T, "rho": N_SENSORS / T, "p": p}
            for pol in POLICIES:
                m, hw, _ = agg(sel(pol), "mean_aoi")
                pk, _, _ = agg(sel(pol), "peak_aoi")
                pdr, _, _ = agg(sel(pol), "pdr")
                st, _, _ = agg(sel(pol), "stale_frac")
                lg, _, _ = agg(sel(pol), "mean_lag")
                row.update({
                    f"{pol}_aoi": round(m, 2), f"{pol}_aoi_ci": round(hw, 2),
                    f"{pol}_peak": round(pk, 2), f"{pol}_pdr": round(pdr, 4),
                    f"{pol}_stale": round(st, 4), f"{pol}_lag": round(lg, 2)})
            for a, b in (("aog", "fifo"), ("lrp", "fifo"), ("aog", "lrp")):
                d, dhw, _ = paired_diff(sel(a), sel(b), "mean_aoi")
                row[f"d_{a}-{b}"] = round(d, 2)
                row[f"d_{a}-{b}_ci"] = round(dhw, 2)
            rows.append(row)
    return rows


def summarise_e2(runs, p):
    """Per-group (fast/slow) mean AoI for the imbalance experiment."""
    rows = []
    for tf, ts in IMBALANCE:
        periods = [tf, tf, ts, ts]
        sel = lambda pol: [r for r in runs if r["policy"] == pol
                           and r["periods"] == periods and r["p"] == p]
        row = {"T_fast": tf, "T_slow": ts,
               "rho": 2 / tf + 2 / ts, "p": p}
        for pol in POLICIES:
            rs = sel(pol)
            m, hw, _ = agg(rs, "mean_aoi")
            row[f"{pol}_aoi"] = round(m, 2)
            row[f"{pol}_aoi_ci"] = round(hw, 2)
            for idx, name in ((0, "fast"), (2, "slow")):
                vals = [r["mean_aoi_sens"][idx] for r in rs if r["run_ok"]]
                n = len(vals)
                mg = float(np.mean(vals))
                hwg = (T_CRIT_9DF * float(np.std(vals, ddof=1))
                       / math.sqrt(n)) if n > 1 else 0.0
                row[f"{pol}_{name}"] = round(mg, 2)
                row[f"{pol}_{name}_ci"] = round(hwg, 2)
            pdr, _, _ = agg(rs, "pdr")
            row[f"{pol}_pdr"] = round(pdr, 4)
        rows.append(row)
    return rows


def write_csv(path, rows):
    keys = list(rows[0].keys())
    with open(path, "w") as f:
        f.write(",".join(keys) + "\n")
        for r in rows:
            f.write(",".join(str(r[k]) for k in keys) + "\n")


def main(argv):
    import aoi_sim as _self  # allow overriding globals for quick mode
    if "quick" in argv:
        _self.N_SLOTS = 20000
        _self.WARMUP = 2000
        _self.SEEDS = [0, 1]

    os.makedirs(RESULTS_DIR, exist_ok=True)
    # fresh checkpoint each full/quick invocation
    ckpt = os.path.join(RESULTS_DIR, "runs.jsonl")
    if os.path.exists(ckpt):
        os.remove(ckpt)

    print("baseline verification ...", flush=True)
    ver = verify_baseline()
    for v in ver:
        print(f"  {v['case']}: theory={v['theory']:.3f} sim={v['sim']:.3f} "
              f"err={v['err_pct']:.3f}%  cons_ok={v['conservation_all_ok']}",
              flush=True)

    grid1 = [(T, p) for T in T_VALUES for p in P_VALUES]
    print(f"E1 symmetric load: {len(grid1)} configs ...", flush=True)
    runs1 = run_grid(grid1, "E1")

    grid2 = [([tf, tf, ts, ts], P_IMBALANCE) for tf, ts in IMBALANCE]
    print(f"E2 priority imbalance: {len(grid2)} configs ...", flush=True)
    runs2 = run_grid(grid2, "E2")

    all_runs = runs1 + runs2
    n_bad = sum(1 for r in all_runs if not r["conservation_ok"])
    n_fail = sum(1 for r in all_runs if not r["run_ok"])
    print(f"conservation violations: {n_bad}; failed runs: {n_fail}")

    with open(os.path.join(RESULTS_DIR, "main_results.json"), "w") as f:
        json.dump([{k: v for k, v in r.items() if k != "trace"}
                   for r in all_runs], f, indent=1)

    write_csv(os.path.join(RESULTS_DIR, "summary_e1.csv"), summarise_e1(runs1))
    write_csv(os.path.join(RESULTS_DIR, "summary_e2.csv"),
              summarise_e2(runs2, P_IMBALANCE))
    with open(os.path.join(RESULTS_DIR, "verification.json"), "w") as f:
        json.dump({"baseline": ver,
                   "conservation_violations": n_bad,
                   "failed_runs": n_fail}, f, indent=1)

    print("saved: main_results.json, summary_e1.csv, summary_e2.csv, "
          "verification.json")


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
