"""
Generate all figures (and equation images) for the Topic 09 report.

Reads ../results/summary_e1.csv, summary_e2.csv, verification.json;
writes PNGs into ../figures/.  Re-run after aoi_sim.py.

Style: validated categorical palette, fixed slot order
  FIFO = blue  #2a78d6   LRP = orange #eb6834   AOG = aqua #1baf7a
Marker shape + linestyle carry identity redundantly (print / CVD safety).
One y-axis per panel (no dual axes); hairline grid; muted axis ink.
"""

import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)

# palette (dataviz reference instance, light mode)
C_FIFO, C_LRP, C_AOG = "#2a78d6", "#eb6834", "#1baf7a"
POL = {"fifo": "FIFO", "lrp": "LRP", "aog": "AoG"}
COL = {"fifo": C_FIFO, "lrp": C_LRP, "aog": C_AOG}
MARK = {"fifo": "o", "lrp": "s", "aog": "^"}
LS = {"fifo": "-", "lrp": "--", "aog": "-."}
INK, SEC, MUT, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": BASE, "axes.labelcolor": SEC, "axes.titlesize": 10,
    "axes.titleweight": "bold", "axes.titlecolor": INK,
    "xtick.color": SEC, "ytick.color": SEC, "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5, "legend.frameon": False, "legend.fontsize": 8.5,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "savefig.dpi": 300, "savefig.bbox": "tight",
})


def style_ax(ax, ylog=False):
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if ylog:
        ax.set_yscale("log")


def load_e1():
    rows = list(csv.DictReader(open(os.path.join(RES, "summary_e1.csv"),
                                    encoding="utf-8")))
    for r in rows:
        for k in r:
            r[k] = float(r[k])
    return rows


def load_e2():
    rows = list(csv.DictReader(open(os.path.join(RES, "summary_e2.csv"),
                                    encoding="utf-8")))
    for r in rows:
        for k in r:
            r[k] = float(r[k])
    return rows


# ----------------------------------------------------------------------
# Fig 1: system model diagram
# ----------------------------------------------------------------------
def fig1_system():
    fig, ax = plt.subplots(figsize=(7.0, 2.5))
    ax.set_xlim(0, 100); ax.set_ylim(0, 34); ax.axis("off")

    def box(x, y, w, h, text, fc, ec, fs=8.5, tc=INK):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6",
                                    fc=fc, ec=ec, lw=1.0))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=tc, linespacing=1.35)

    def arrow(x1, y1, x2, y2, style="-|>", col=SEC, lw=1.2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                     arrowstyle=style, mutation_scale=11,
                                     color=col, lw=lw, shrinkA=2, shrinkB=2))

    ys = [25.5, 19.5, 13.5, 7.5]
    targets = [22.0, 18.3, 14.6, 10.9]      # spread along gateway edge
    for i, (y, ty) in enumerate(zip(ys, targets)):
        box(1, y, 14.5, 4.4, f"Sensor {i}\nperiod $T_i$ slots",
            "#ffffff", BASE)
        arrow(16.1, y + 2.2, 21.6, ty)
    ax.text(8.2, 31.5, "update generation", ha="center", fontsize=8,
            color=MUT)

    box(22, 8, 20, 17,
        "Gateway\n\nqueue +\nscheduling policy\n(FIFO / LRP / AoG)",
        "#eef4fc", C_FIFO)
    arrow(43, 16.5, 51.6, 16.5)
    ax.text(47.3, 19.6, "1 packet\nper slot", ha="center", fontsize=7.5,
            color=MUT)

    box(52, 8, 20, 17,
        "Shared wireless\nlink\n\nsuccess w.p. $1-p$\n(no retransmission)",
        "#fdf0ea", C_LRP)
    arrow(73, 16.5, 81.6, 16.5)

    box(82, 8, 17, 17,
        "Monitor\n\nstores $\\tau_i$:\nnewest received\ngeneration time",
        "#eafaf3", C_AOG)
    ax.plot([90.5, 90.5], [8.0, 6.6], color=BASE, lw=0.9)
    ax.text(90.5, 4.2,
            "$\\Delta_i(t) = t - \\tau_i(t)$  (age of information)",
            ha="center", fontsize=9, color=INK)

    fig.savefig(os.path.join(FIG, "fig1_system.png"))
    plt.close(fig)


# ----------------------------------------------------------------------
# Fig 2: baseline verification - ideal sawtooth
# ----------------------------------------------------------------------
def fig2_sawtooth():
    from aoi_sim import simulate
    T = 8
    r = simulate("fifo", T, 0.0, seed=0, n_slots=4 * T, n_sensors=1,
                 warmup=0, collect_trace=True, trace_sensor=0)
    t = list(range(len(r["trace"])))
    fig, ax = plt.subplots(figsize=(4.6, 2.3))
    ax.step(t, r["trace"], where="post", color=C_FIFO, lw=1.8)
    ax.axhline((T - 1) / 2, color=MUT, lw=1.0, ls=":")
    ax.text(0.4, (T - 1) / 2 + 0.25,
            f"analytic mean $(T-1)/2 = {(T - 1) / 2:.1f}$",
            fontsize=8, color=SEC)
    ax.set_xlabel("slot $t$")
    ax.set_ylabel("age $\\Delta(t)$  [slots]")
    ax.set_title(f"Single sensor, no loss, no queueing (T = {T}): "
                 "verification case")
    ax.set_xticks(range(0, 4 * T + 1, T))
    style_ax(ax)
    fig.savefig(os.path.join(FIG, "fig2_sawtooth.png"))
    plt.close(fig)


# ----------------------------------------------------------------------
# Fig 3: E1 main result - mean AoI vs generation interval, 3 loss panels
# ----------------------------------------------------------------------
def fig3_main(rows):
    Ts = [2, 3, 4, 8, 16, 32]
    ps = [0.0, 0.1, 0.3]
    xs = range(len(Ts))
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9), sharey=True)
    sel = {(r["T"], r["p"]): r for r in rows}
    for ax, p in zip(axes, ps):
        for pol in ("fifo", "lrp", "aog"):
            ys = [sel[(T, p)][f"{pol}_aoi"] for T in Ts]
            es = [sel[(T, p)][f"{pol}_aoi_ci"] for T in Ts]
            ax.errorbar(xs, ys, yerr=es, color=COL[pol], marker=MARK[pol],
                        ls=LS[pol], lw=1.7, ms=5, elinewidth=1.0,
                        capsize=2.5, label=POL[pol],
                        markerfacecolor=("white" if pol != "fifo"
                                         else COL[pol]),
                        markeredgewidth=1.4)
        ax.set_title(f"$p$ = {p:g}")
        ax.set_xticks(list(xs))
        ax.set_xticklabels([f"{T}\n{4 / T:.2f}" for T in Ts])
        style_ax(ax, ylog=True)
    axes[0].set_ylabel("mean AoI  [slots]")
    axes[1].set_xlabel("generation interval $T$  [slots]   "
                       "(lower number = offered load $\\rho = N/T$)")
    axes[0].legend(loc="lower right")
    fig.savefig(os.path.join(FIG, "fig3_main.png"))
    plt.close(fig)


# ----------------------------------------------------------------------
# Fig 4: same delivery rate, different freshness (p = 0.1)
# ----------------------------------------------------------------------
def fig4_pdr_aoi(rows):
    Ts = [2, 3, 4, 8, 16, 32]
    xs = range(len(Ts))
    sel = {(r["T"], r["p"]): r for r in rows}
    fig, axes = plt.subplots(3, 1, figsize=(5.6, 5.3), sharex=True,
                             gridspec_kw={"hspace": 0.32})
    panels = [
        ("pdr", "packet delivery ratio", False),
        ("lag", "delivery lag  [slots]", False),
        ("aoi", "mean AoI  [slots]", True),
    ]
    for ax, (key, ylab, ylog) in zip(axes, panels):
        for pol in ("fifo", "lrp", "aog"):
            ys = [sel[(T, 0.1)][f"{pol}_{key}"] for T in Ts]
            es = ([sel[(T, 0.1)][f"{pol}_aoi_ci"] for T in Ts]
                  if key == "aoi" else None)
            if es is not None:
                ax.errorbar(xs, ys, yerr=es, color=COL[pol],
                            marker=MARK[pol], ls=LS[pol], lw=1.7, ms=5,
                            elinewidth=1.0, capsize=2.5, label=POL[pol],
                            markerfacecolor=("white" if pol != "fifo"
                                             else COL[pol]),
                            markeredgewidth=1.4)
            else:
                ax.plot(xs, ys, color=COL[pol], marker=MARK[pol],
                        ls=LS[pol], lw=1.7, ms=5, label=POL[pol],
                        markerfacecolor=("white" if pol != "fifo"
                                         else COL[pol]),
                        markeredgewidth=1.4)
        ax.set_ylabel(ylab, fontsize=8.5, labelpad=3)
        style_ax(ax, ylog=ylog)
    axes[0].set_ylim(0, 1.02)
    axes[1].set_ylim(-0.5, 20.5)
    axes[0].legend(loc="lower right", ncol=3, columnspacing=1.0)
    axes[2].set_xticks(list(xs))
    axes[2].set_xticklabels([str(T) for T in Ts])
    axes[2].set_xlabel("generation interval $T$  [slots]   ($p$ = 0.1)")
    fig.savefig(os.path.join(FIG, "fig4_pdr_aoi.png"))
    plt.close(fig)


# ----------------------------------------------------------------------
# Fig 5: single-run trajectory of the starved sensor (T = 3, p = 0.1)
# ----------------------------------------------------------------------
def fig5_trajectory():
    from aoi_sim import simulate
    W = 600  # plotted window length (slots), from warm-up end
    fig, axes = plt.subplots(3, 1, figsize=(5.6, 5.6), sharex=True,
                             gridspec_kw={"hspace": 0.30})
    for ax, pol in zip(axes, ("fifo", "lrp", "aog")):
        r = simulate(pol, 3, 0.1, seed=0, collect_trace=True,
                     trace_sensor=3)
        seg = r["trace"][:W]
        ax.plot(range(len(seg)), seg, color=COL[pol], lw=1.5)
        ax.set_title(f"{POL[pol]}  (sensor 3, mean over run: "
                     f"{r['mean_aoi_sens'][3]:.1f})", fontsize=9, loc="left")
        ax.set_ylabel("$\\Delta_3(t)$", fontsize=8.5)
        style_ax(ax)
    axes[2].set_xlabel("slot $t$  (window starts after warm-up; "
                       "$T=3$, $p=0.1$, seed 0)")
    fig.savefig(os.path.join(FIG, "fig5_trajectory.png"))
    plt.close(fig)


# ----------------------------------------------------------------------
# Fig 6: E2 priority imbalance - per-group mean AoI
# ----------------------------------------------------------------------
def fig6_imbalance(rows2):
    YMAX = 30.0   # axis truncated; starvation bars annotated off-scale
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.1), sharey=True)
    fig.subplots_adjust(bottom=0.20, top=0.84, wspace=0.08)
    for ax, r in zip(axes, rows2):
        pols = ["fifo", "lrp", "aog"]
        xs = range(len(pols))
        w = 0.34
        overload = r["rho"] > 1.0
        for off, (grp, lab, col) in enumerate(
                [("fast", "fast group", "#2a78d6"),
                 ("slow", "slow group", "#9ec5f4")]):
            ys = [min(r[f"{pol}_{grp}"], YMAX) for pol in pols]
            es = [r[f"{pol}_{grp}_ci"] if r[f"{pol}_{grp}"] <= YMAX
                  else 0.0 for pol in pols]
            xs_off = [x + (off - 0.5) * w for x in xs]
            ax.bar(xs_off, ys, w * 0.92, yerr=es,
                   color=col, edgecolor="white", linewidth=0.8,
                   error_kw=dict(elinewidth=1.0, capsize=2.5),
                   label=lab)
            for xo, pol in zip(xs_off, pols):
                v = r[f"{pol}_{grp}"]
                if v > YMAX:  # clipped starvation bar: break mark + value
                    ax.text(xo, YMAX - 1.0, f"{v:,.0f}*", ha="center",
                            va="top", fontsize=7, color=SEC, rotation=90)
                    ax.fill_between([xo - w * 0.5, xo + w * 0.5],
                                    [27.6, 28.4], [28.0, 28.8],
                                    color="white", lw=0, zorder=3)
                    ax.plot([xo - w * 0.5, xo + w * 0.5], [27.6, 28.4],
                            color=BASE, lw=0.8, zorder=4)
                    ax.plot([xo - w * 0.5, xo + w * 0.5], [28.0, 28.8],
                            color=BASE, lw=0.8, zorder=4)
        ax.set_title(f"($T_f$, $T_s$) = ({int(r['T_fast'])}, "
                     f"{int(r['T_slow'])})\n$\\rho$ = {r['rho']:.2f}, "
                     f"{'overload' if overload else 'underload'}",
                     fontsize=8.5, pad=4)
        ax.set_xticks(list(xs))
        ax.set_xticklabels([POL[p] for p in pols])
        ax.set_ylim(0, YMAX)
        style_ax(ax)
    axes[0].set_ylabel("mean AoI  [slots]")
    axes[0].legend(loc="upper right")
    fig.supxlabel("scheduling policy   (dark = fast group, light = slow "
                   "group;  $p$ = 0.1;  * off-scale, horizon-dependent)",
                  fontsize=8.5, color=SEC, y=0.02)
    fig.savefig(os.path.join(FIG, "fig6_imbalance.png"))
    plt.close(fig)


# ----------------------------------------------------------------------
# Equation images (mathtext) for the Word report
# ----------------------------------------------------------------------
def equations():
    eqs = {
        "eq_aoi": r"$\Delta_i(t) \;=\; t \,-\, \tau_i(t)$",
        "eq_mean": (r"$\bar{\Delta} \;=\; \frac{1}{|\mathcal{W}|}"
                    r"\sum_{t \in \mathcal{W}} \frac{1}{N}"
                    r"\sum_{i=1}^{N} \left( t - \tau_i(t) \right)$"),
        "eq_peak": (r"$\Delta^{\mathrm{peak}} \;=\; \mathbb{E}\left["
                    r"\Delta_i(t^{-})\right]$"),
        "eq_gain": (r"$G_i(t) \;=\; \Delta_i(t) - \left(t - g_i(t)\right)"
                    r" \;=\; g_i(t) \,-\, \tau_i(t)$"),
        "eq_pdr": (r"$\mathrm{PDR} \;=\; \frac{\mathrm{delivered}}"
                   r"{\mathrm{generated}}$"),
    }
    for name, tex in eqs.items():
        fig = plt.figure(figsize=(0.5, 0.5))
        fig.text(0.5, 0.5, tex, ha="center", va="center", fontsize=12)
        fig.savefig(os.path.join(FIG, f"{name}.png"), dpi=300,
                    bbox_inches="tight", pad_inches=0.06)
        plt.close(fig)


if __name__ == "__main__":
    fig1_system()
    fig2_sawtooth()
    rows = load_e1()
    fig3_main(rows)
    fig4_pdr_aoi(rows)
    fig5_trajectory()
    fig6_imbalance(load_e2())
    equations()
    print("figures written to", os.path.abspath(FIG))
