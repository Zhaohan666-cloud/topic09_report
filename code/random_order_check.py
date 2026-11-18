"""Sensitivity check for Section 6.2 of the report.

aoi_sim.simulate() queues several sensors that generate in the *same* slot in
ascending sensor-index order. Under overload the queue is full, so that order
decides which sensor is dropped - i.e. it silently acts as a permanent
priority. This script re-runs the overload configurations twice:

    order="index"   exactly the production code path (sanity check: the
                    numbers must equal results/summary_e1.csv)
    order="random"  the co-arriving sensors are permuted per slot

Everything else (phases, per-slot loss draws, policy logic, seed stream) is
identical, so any difference is attributable to the ordering alone.

The simulate() loop is duplicated here on purpose: code/aoi_sim.py stays
untouched so results/main_results.json keeps reproducing bit-for-bit.

Run:  python code/random_order_check.py
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aoi_sim as S

NEG = S.NEG
SEEDS = range(10)


def simulate(policy, periods, p, seed, order="index",
             n_slots=S.N_SLOTS, n_sensors=S.N_SENSORS, k=S.QUEUE_CAP,
             warmup=S.WARMUP):
    if np.isscalar(periods):
        periods = [periods] * n_sensors

    phases, loss_u, tb_u = S.shared_randomness(seed, n_slots, n_sensors)
    arrv = S.arrival_schedule(phases, periods, n_slots, n_sensors)
    loss_u = loss_u.tolist()
    tb_u = tb_u.tolist()
    # independent stream, only used to permute co-arrivals
    order_u = np.random.default_rng(seed + 999_983).random(n_slots).tolist()

    tau = [NEG] * n_sensors
    delivered = [0] * n_sensors
    generated = [0] * n_sensors
    age_sum = 0.0
    age_sens = [0.0] * n_sensors
    slots = 0
    dropped = 0

    q = []
    qs = [None] * n_sensors

    for t in range(n_slots):
        arr = [s for s in range(n_sensors) if arrv[s][t]]
        if order == "random" and len(arr) > 1:
            for i in range(len(arr) - 1, 0, -1):
                j = int(order_u[t] * (i + 1)) % (i + 1)
                arr[i], arr[j] = arr[j], arr[i]

        for s in arr:
            generated[s] += 1
            if policy == "fifo":
                if len(q) >= k:
                    dropped += 1
                else:
                    q.append((t, s))
            else:
                qs[s] = t

        tx = None
        if policy == "fifo":
            if q:
                tx = q.pop(0)
        else:
            cand = [j for j in range(n_sensors) if qs[j] is not None]
            if cand:
                if policy == "lrp":
                    newest = max(qs[j] for j in cand)
                    tied = [j for j in cand if qs[j] == newest]
                    i = tied[0] if len(tied) == 1 else \
                        tied[int(tb_u[t] * len(tied)) % len(tied)]
                else:
                    i = cand[0]
                    best = (qs[i] - tau[i], qs[i])
                    for j in cand[1:]:
                        key = (qs[j] - tau[j], qs[j])
                        if key > best:
                            best, i = key, j
                tx = (qs[i], i)
                qs[i] = None

        if tx is not None:
            g, i = tx
            if loss_u[t] >= p:
                delivered[i] += 1
                tau[i] = max(tau[i], g)

        if t >= warmup:
            slot_total = 0
            for i in range(n_sensors):
                a = t - tau[i]
                age_sens[i] += a
                slot_total += a
            age_sum += slot_total / n_sensors
            slots += 1

    return dict(mean=age_sum / slots,
                sens=[a / slots for a in age_sens],
                delivered=delivered)


def summarise(policy, periods, p, order):
    means, sens = [], []
    for sd in SEEDS:
        r = simulate(policy, periods, p, sd, order)
        means.append(r["mean"])
        sens.append(r["sens"])
    m = float(np.mean(means))
    hw = 2.262 * float(np.std(means, ddof=1)) / math.sqrt(len(means))
    per = [float(np.mean([s[i] for s in sens])) for i in range(len(sens[0]))]
    return m, hw, per


CASES = [
    ("E1 T=2, p=0.1 (rho=2.00)", 2, 0.1, None),
    ("E1 T=3, p=0.1 (rho=1.33)", 3, 0.1, None),
    ("E2 (Tf,Ts)=(2,8), p=0.1 (rho=1.25)", [2, 2, 8, 8], 0.1, (2, 2)),
]

if __name__ == "__main__":
    print("intra-slot order sensitivity (10 paired seeds, 100k slots)\n")
    for title, periods, p, groups in CASES:
        print("-" * 74)
        print(title)
        for pol in ("fifo", "lrp", "aog"):
            line = f"  {pol.upper():4s}"
            for order in ("index", "random"):
                m, hw, per = summarise(pol, periods, p, order)
                line += f" | {order}: {m:10.2f} +/- {hw:6.2f}"
                if groups:
                    nf = groups[0]
                    fast = float(np.mean(per[:nf]))
                    slow = float(np.mean(per[nf:]))
                    line += f" (fast {fast:7.2f}, slow {slow:9.2f})"
            print(line)
        print()
