# -*- coding: utf-8 -*-
"""
Build the Topic 09 group-project report (.docx, single column, English).

Reads experiment outputs from ../results/ and figures from ../figures/;
numbers in the text are injected from the result files, so re-running this
script after aoi_sim.py always produces a consistent report.
"""

import csv
import json
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
FIG = os.path.join(HERE, "..", "figures")
OUT = os.path.join(HERE, "..", "Topic09_Group_Report.docx")

INK = RGBColor(0x0B, 0x0B, 0x0B)
RED = RGBColor(0xC0, 0x00, 0x00)
BLUE = RGBColor(0x1F, 0x4E, 0x79)

doc = Document()

# ---------------- page & style setup ----------------
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.2)

st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
st.paragraph_format.space_after = Pt(6)
st.paragraph_format.line_spacing = 1.08

for i, sz in [(1, 14), (2, 12), (3, 11)]:
    h = doc.styles[f"Heading {i}"]
    h.font.name = "Calibri"
    h.font.size = Pt(sz)
    h.font.bold = True
    h.font.color.rgb = BLUE
    rf = h.element.get_or_add_rPr().find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        h.element.get_or_add_rPr().append(rf)
    rf.set(qn("w:eastAsia"), "微软雅黑")


def para(text, bold=False, italic=False, size=11, color=None, align=None,
         space_after=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p


def rich(parts, space_after=6):
    """parts: list of (text, attrs-dict)."""
    p = doc.add_paragraph()
    for text, attrs in parts:
        r = p.add_run(text)
        r.bold = attrs.get("bold", False)
        r.italic = attrs.get("italic", False)
        r.font.size = Pt(attrs.get("size", 11))
        if attrs.get("color"):
            r.font.color.rgb = attrs["color"]
    p.paragraph_format.space_after = Pt(space_after)
    return p


def bullets(items, numbered=False):
    for it in items:
        p = doc.add_paragraph(style="List Number" if numbered
                              else "List Bullet")
        if isinstance(it, str):
            it = [(it, {})]
        for text, attrs in it:
            r = p.add_run(text)
            r.bold = attrs.get("bold", False)
            r.font.size = Pt(10.5)
        p.paragraph_format.space_after = Pt(2)


def caption(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(9.5)
    r.italic = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def table(headers, rows, widths=None, fs=9, header_bg="D9E2F3", cap=None,
          align_center_cols=None):
    if cap:
        caption(cap)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        c = t.rows[0].cells[j]
        c.text = ""
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(fs)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade(c, header_bg)
    for row in rows:
        cells = t.add_row().cells
        for j, v in enumerate(row):
            cells[j].text = ""
            for k, line in enumerate(str(v).split("\n")):
                p = (cells[j].paragraphs[0] if k == 0
                     else cells[j].add_paragraph())
                r = p.add_run(line)
                r.font.size = Pt(fs)
                if align_center_cols and j in align_center_cols:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if widths:
        for j, w in enumerate(widths):
            for row in t.rows:
                row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(name, width_cm, cap):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(os.path.join(FIG, f"{name}.png"),
                            width=Cm(width_cm))
    caption(cap)


def eq(name, tag):
    """Equation image, centred, with a right-hand equation number."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(os.path.join(FIG, f"{name}.png"), height=Cm(0.9))
    r = p.add_run(f"    ({tag})")
    r.font.size = Pt(10)
    p.paragraph_format.space_after = Pt(8)


# ---------------- load results ----------------
E1 = list(csv.DictReader(open(os.path.join(RES, "summary_e1.csv"),
                              encoding="utf-8")))
E2 = list(csv.DictReader(open(os.path.join(RES, "summary_e2.csv"),
                              encoding="utf-8")))
VER = json.load(open(os.path.join(RES, "verification.json"),
                     encoding="utf-8"))
for r in E1 + E2:
    for k in r:
        r[k] = float(r[k])
S = {(int(r["T"]), r["p"]): r for r in E1}


def g(T, p, key):
    return S[(T, float(p))][key]


# headline numbers used in the narrative (p = 0.1 panel unless noted)
fifo_ov2, lrp_ov2, aog_ov2 = g(2, 0.1, "fifo_aoi"), g(2, 0.1, "lrp_aoi"), \
    g(2, 0.1, "aog_aoi")
fifo_ov3, lrp_ov3, aog_ov3 = g(3, 0.1, "fifo_aoi"), g(3, 0.1, "lrp_aoi"), \
    g(3, 0.1, "aog_aoi")
lag_f = g(2, 0.1, "fifo_lag")
conv4 = g(4, 0.1, "fifo_aoi")
e2a = E2[0]

# =====================================================================
# Title block
# =====================================================================
p = doc.add_paragraph()
r = p.add_run("Freshness-Aware Scheduling for Wireless Sensor Monitoring: "
              "Delivering More Packets Is Not Knowing More")
r.bold = True
r.font.size = Pt(15)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
para("EEEN3008J Wireless Communications - Group Project, Autumn 2026/27",
     size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
rich([("Group [XX] - [Member 1 name, student no.], [Member 2 name, student "
       "no.], [Member 3 name, student no.], [Member 4 name, student no.]  "
       "[REPLACE WITH REAL NAMES]", {"size": 10, "color": RED})],
     space_after=2)
para("13 November 2026", size=10, align=WD_ALIGN_PARAGRAPH.CENTER,
     space_after=10)

# ---------------- Abstract ----------------
doc.add_heading("Abstract", level=1)
para(
    "In remote monitoring, the value of a wireless sensor update lies in how "
    "current it is when it arrives, not merely in whether it arrives. This "
    "project studies gateway scheduling for four sensors that share one "
    "lossy wireless link, using the age of information (AoI) as the figure "
    "of merit. We compare a delivery-oriented FIFO baseline, a "
    "latest-sample-replacement (LRP) rule, and an AoI-gain (AoG) scheduler "
    "that transmits the queued sample with the largest freshness improvement. "
    "All policies are evaluated in a time-slotted Python simulator under "
    "paired random seeds, so every policy faces identical arrivals and "
    "identical channel losses (10 seeds per configuration, run-level 95% "
    "confidence intervals). Across the offered-load sweep the three policies "
    "achieve statistically identical packet delivery ratios, yet under "
    "overload their mean AoI differs by orders of magnitude: at twice the "
    "sustainable rate with 10% loss, FIFO reaches a horizon-dependent mean "
    f"AoI above {fifo_ov2:,.0f} slots (it structurally starves sensors that "
    f"share arrival slots), while LRP and AoG remain at {lrp_ov2:.1f} and "
    f"{aog_ov2:.1f} slots. Under a priority imbalance, LRP privileges fast "
    "sensors and degrades slow ones, whereas AoG balances both groups. "
    "Below roughly half of capacity all policies are equivalent - "
    "freshness-aware scheduling pays off only under contention. A high "
    "delivery ratio is therefore not evidence of a well-informed monitor.")

# =====================================================================
# 1. Introduction
# =====================================================================
doc.add_heading("1. Introduction", level=1)
para(
    "A gateway collecting status updates from wireless sensors typically "
    "treats every packet as equally worth delivering. Queueing and MAC "
    "design inherited from data networks maximise throughput and packet "
    "delivery ratio (PDR). For a monitoring application, however, the "
    "receiver rarely needs every reading: if a newer sample of the same "
    "sensor exists, delivering the older one adds airtime cost without "
    "improving what the monitor knows. The age of information (AoI) "
    "captures this distinction - the time elapsed since the newest "
    "received update was generated [1], [7].")
para(
    "This project asks one focused question: on a shared lossy link, should "
    "a gateway transmit every queued sample (FIFO thinking), or discard "
    "obsolete samples and prioritise by freshness? We answer with a "
    "controlled simulation study of three scheduling rules - FIFO, "
    "latest-sample replacement (LRP), and a max-weight-style AoI-gain rule "
    "(AoG) - under a load sweep that crosses the link capacity, a loss "
    "sweep, and a sensor priority imbalance.")
para("The contributions of this report are:", space_after=2)
bullets([
    "a critical survey of AoI scheduling literature, organised in an "
    "evidence matrix (Section 2);",
    "an AoI-gain scheduler and a reproducible, paired-seed evaluation "
    "methodology with analytic baseline verification (Sections 4-5);",
    "quantitative evidence that identical PDR can coexist with "
    "order-of-magnitude AoI differences, identification of the structural "
    "starvation mechanisms behind them, and an honest negative case where "
    "all policies are equivalent (Section 6).",
])
para(
    "Following the module's validation guidance, we state in advance a "
    "condition under which the proposal might fail: when the offered load "
    "is well below capacity, no queue builds up, the policies coincide, and "
    "freshness-aware scheduling brings no benefit. Section 6 confirms this "
    "experimentally and quantifies where the boundary lies.")

# =====================================================================
# 2. Critical review
# =====================================================================
doc.add_heading("2. Critical Review of Related Work", level=1)
doc.add_heading("2.1 Evidence matrix", level=2)
para(
    "Table 1 summarises the sources that shaped our design. Reading them "
    "critically - what each assumes versus what each actually validates - "
    "reveals the gap this project addresses.", space_after=4)
table(
    ["Ref.", "Year", "Problem", "Assumes", "Validates", "Limitation for us"],
    [
        ["[1]", "2012", "Defines AoI; when to update",
         "Poisson arrivals, M/M/1 queue",
         "Analytic peak/mean AoI", "No scheduling across sensors"],
        ["[3]", "2012", "Multi-source status updating",
         "Poisson sources, FCFS or LCFS",
         "Analytic AoI comparison", "Two sources, no loss"],
        ["[2]", "2016", "Packet management (LCFS w/ preemption)",
         "Poisson arrivals, single source",
         "LCFS-preemption minimises AoI",
         "Idealised preemption; basis of our LRP"],
        ["[5]", "2019", "Update or wait (sampling control)",
         "Correlated channel, terminal decides",
         "Optimality of threshold sampling",
         "Sampling timing, not gateway queueing"],
        ["[4]", "2018", "Multiuser AoI scheduling (broadcast)",
         "Channel known, IID across time",
         "MaxWeight-type index policies",
         "Overhead-free perfect knowledge; basis of our AoG"],
        ["[8]", "2020", "Distributed AoI scheduling",
         "Graph interference model",
         "Local policies near-centralised",
         "No loss model at the link"],
        ["[6]", "2017", "Age vs. value of information",
         "Non-linear age penalty",
         "Value can be non-increasing in age",
         "Motivates metrics beyond delivery"],
        ["[7]", "2021", "Survey of AoI",
         "-", "Taxonomy of models", "Confirms gaps above are open"],
        ["[9]", "2025", "Age of semantic information",
         "Remote monitoring, MIMO", "Task-aware freshness metrics",
         "Semantics beyond our scope"],
        ["[10]", "2024", "Joint age-delay scheduling",
         "Industrial wireless flows", "Joint-optimisation gains",
         "Delay-oriented view; motivates our PDR/AoI pairing"],
        ["[11]", "2024", "AoI-throughput trade-off scheduling",
         "Heterogeneous traffic model", "Pareto-optimal schedulers",
         "Throughput analog of our PDR axis"],
        ["[12]", "2025", "Whittle-index MQTT scheduling",
         "MDP, MQTT broker", "Index policy near-optimal",
         "Index rule; AoG is a simpler max-weight cousin"],
    ],
    widths=[1.4, 1.5, 3.3, 3.1, 3.3, 4.0], fs=8,
    cap="Table 1. Evidence matrix of the surveyed literature: foundations "
        "(2012-2021) plus current work (2024-2025).")

doc.add_heading("2.2 What the literature assumes versus validates", level=2)
para(
    "Three recurring assumptions stand out. First, arrival processes are "
    "almost always Poisson and channels are memoryless or perfectly known "
    "[1]-[4]; the interaction of periodic sensor traffic with random loss "
    "is rarely isolated. Second, preemption and sample replacement are "
    "usually treated as free and instantaneous [2]; the cost side - which "
    "samples get thrown away, and who starves when they do - is "
    "under-reported. Third, evaluations mostly compare AoI-optimal policies "
    "against deliberately passive baselines, and few papers report the "
    "delivery ratio alongside AoI, so the practical message that a policy "
    "can deliver the same packets and inform the monitor far better (or far "
    "worse) is easy to miss. Recent work has broadened the objectives - "
    "joint age-delay scheduling in industrial networks [10], "
    "age-throughput trade-off frontiers [11], and Whittle-index scheduling "
    "for MQTT brokers [12] - yet the delivery-versus-freshness contrast "
    "under overload remains under-illustrated. Our study is designed "
    "around exactly that contrast: we hold the channel, traffic, and "
    "airtime common across policies and report PDR next to AoI everywhere.")

# =====================================================================
# 3. System model
# =====================================================================
doc.add_heading("3. System Model and Metrics", level=1)
doc.add_heading("3.1 Model", level=2)
para(
    "We consider N = 4 sensors that periodically generate timestamped "
    "updates and one gateway that forwards them over a shared wireless "
    "link (Figure 1). Time is slotted. Sensor i generates one update every "
    "T_i slots at a fixed random phase; several sensors may generate in the "
    "same slot. The gateway transmits at most one packet per slot; a "
    "transmission succeeds with probability 1 - p, independently per slot, "
    "and failed transmissions are lost - there is no retransmission, which "
    "matches the simple regime of many low-power sensor links. The "
    "receiver stores for each sensor the generation time of the newest "
    "update received so far.")
figure("fig1_system", 16.2,
       "Figure 1. System model. Four periodic sensors feed a gateway queue "
       "and scheduling policy; the shared link serves one packet per slot "
       "with success probability 1 - p; the monitor tracks the newest "
       "received generation time per sensor.")
para("The AoI of sensor i at the end of slot t is", space_after=2)
eq("eq_aoi", "1")
para("where tau_i(t) is the generation time of the newest update of sensor "
     "i received by the end of slot t. The system mean AoI is the time "
     "average over the measurement window W (the first 10% of each run is "
     "discarded as warm-up):", space_after=2)
eq("eq_mean", "2")
para("The peak AoI is the average age reached immediately before each "
     "freshness-improving delivery:", space_after=2)
eq("eq_peak", "3")
para("Packet delivery ratio is", space_after=2)
eq("eq_pdr", "4")
para(
    "Two further diagnostics matter for the argument. The delivery lag is "
    "the age of a sample at the moment it is delivered (t - g); a policy "
    "can deliver packets punctually yet the packets may already be "
    "obsolete. A delivery is stale if it does not improve the receiver's "
    "state (g <= tau_i).")
doc.add_heading("3.2 Parameters and provenance", level=2)
table(
    ["Parameter", "Value", "Provenance"],
    [
        ["Sensors N", "4", "Illustrative (brief)"],
        ["Generation interval T (E1)", "2, 3, 4, 8, 16, 32 slots "
         "(rho = 2.0 ... 0.125)", "Illustrative sweep"],
        ["Imbalance (E2) (T_fast, T_slow)", "(2,8), (2,16), (4,16)",
         "Illustrative sweep"],
        ["Loss probability p", "0, 0.1, 0.3", "Illustrative; LPWAN-like "
         "regime [7]"],
        ["Link rate", "1 packet/slot", "Normalised"],
        ["FIFO queue capacity K", "20 packets (tail drop)", "Illustrative"],
        ["Run length / warm-up", "100,000 / 10,000 slots", "Design choice"],
        ["Seeds", "10 independent, paired across policies", "Guide step 7"],
        ["Slot duration", "abstract unit", "Not tied to a PHY"],
    ],
    widths=[4.6, 6.4, 5.6], fs=9,
    cap="Table 2. Model parameters and their provenance. Every value is "
        "illustrative and normalised; none is measured.")
doc.add_heading("3.3 Abstraction declaration", level=2)
para(
    "The model omits: retransmission (ARQ/HARQ), channel memory and "
    "capture effects, propagation delay, errors other than iid loss, "
    "multi-hop paths, energy, and any PHY waveform. Sensors are "
    "single-hop and periodic with fixed phases. These omissions are "
    "deliberate: they isolate the queueing and scheduling mechanisms that "
    "determine freshness. Section 7 discusses how the conclusions would "
    "move if they were relaxed.")

# =====================================================================
# 4. Policies
# =====================================================================
doc.add_heading("4. Scheduling Policies", level=1)
para(
    "All three policies transmit whenever the queue is non-empty, so they "
    "consume identical airtime under identical arrival and loss "
    "realisations. They differ only in what they keep in the queue and "
    "what they choose to send.")
bullets([
    [("FIFO (baseline). ", {"bold": True}),
     ("Finite queue of capacity K = 20 with tail drop; transmits the "
      "oldest queued packet. This is the delivery-oriented default: it "
      "treats every generated sample as equally worth delivering.", {})],
    [("LRP (latest-sample replacement). ", {"bold": True}),
     ("Keeps at most one sample per sensor - a new sample replaces the "
      "queued one (the preemption discipline of [2] applied in-queue); "
      "transmits the most recently generated sample. Ties between "
      "same-slot samples are broken uniformly at random, so the baseline "
      "is not weakened by a deterministic tie rule.", {})],
    [("AoG (AoI-gain, ours). ", {"bold": True}),
     ("Same queue discipline as LRP; transmits the queued sample with the "
      "largest freshness gain", {})],
])
eq("eq_gain", "5")
para("where g_i(t) is the generation time of the queued sample of sensor i "
     "and the equality follows from (1): the gain is exactly how much "
     "younger the receiver's knowledge of sensor i would become. Ties go "
     "to the older sample. A sensor that has never been delivered has "
     "maximal gain, so the rule cannot starve it - the max-weight property "
     "that makes such schedulers throughput-optimal in [4]. Complexity is "
     "O(N) per slot with N = 4, i.e., negligible.")
table(
    ["Line", "AoG rule per slot"],
    [
        ["1", "arrivals: qs[i] <- t for each arriving sensor i "
         "(replacing any older queued sample)"],
        ["2", "if no queued sample: idle"],
        ["3", "i* <- argmax_i (qs[i] - tau[i]);  ties -> larger qs[i]"],
        ["4", "transmit (qs[i*], i*); qs[i*] <- None"],
        ["5", "with prob. 1-p: tau[i*] <- max(tau[i*], g) at slot end"],
    ],
    widths=[1.4, 15.0], fs=9, align_center_cols={0},
    cap="Table 3. Pseudocode of the AoI-gain rule (the per-slot loss draw "
        "is shared across policies).")

# =====================================================================
# 5. Methodology & verification
# =====================================================================
doc.add_heading("5. Experimental Methodology and Verification", level=1)
doc.add_heading("5.1 Fairness, seeds, and statistics", level=2)
para(
    "All policies run on common random numbers: for a given seed, the "
    "arrival phases and the per-slot loss draws are identical across "
    "policies, so a slot that is lossy for one policy is lossy for all. "
    "Each configuration uses 10 independent seeds; policies are compared "
    "pairwise within seeds (paired differences), and 95% confidence "
    "intervals use the t-distribution (df = 9) over run-level means - "
    "packets within a run are correlated, so per-packet statistics would "
    "understate uncertainty. The unit of replication is the run.")
doc.add_heading("5.2 Baseline verification", level=2)
para(
    "Before any policy comparison we verified the simulator against cases "
    "with known answers (guide step 4). First, a single sensor without "
    "loss or queueing produces the classic sawtooth with analytic mean "
    "(T-1)/2 (Figure 2); the simulated means match the analytic values to "
    "reporting precision (Table 4). Second, the no-contention multi-sensor "
    "configurations (T >= 8, p = 0) reproduce the same analytic value per "
    "sensor. Third, every run passes an exact conservation check: "
    "generated = delivered + failed transmissions + dropped (overflow or "
    "replaced) + in-queue at end. Across all 630 runs there were "
    f"{VER['conservation_violations']} conservation violations and "
    f"{VER['failed_runs']} failed runs (a failed run is reported, never "
    "hidden).")
figure("fig2_sawtooth", 9.0,
       "Figure 2. Verification case: single sensor, no loss, no queueing. "
       "The sawtooth age has analytic mean (T-1)/2 = 3.5 slots for T = 8.")
rows_ver = []
for v in VER["baseline"]:
    rows_ver.append([v["case"], f"{v['theory']:.2f}", f"{v['sim']:.2f}",
                     f"{v['err_pct']:.2f}%"])
rows_ver.append(["N=4, p=0, T=16 (all policies)", "7.50",
                 f"{g(16, 0.0, 'fifo_aoi'):.2f}",
                 f"{abs(g(16, 0.0, 'fifo_aoi') - 7.5) / 7.5 * 100:.2f}%"])
table(["Verification case", "Analytic", "Simulated", "Error"],
      rows_ver, widths=[7.6, 2.8, 3.2, 2.8], fs=9,
      align_center_cols={1, 2, 3},
      cap="Table 4. Baseline verification against analytic sawtooth means.")

# =====================================================================
# 6. Results
# =====================================================================
doc.add_heading("6. Results", level=1)
doc.add_heading("6.1 Load sweep: identical PDR, different freshness", level=2)
para(
    "Figure 3 shows mean AoI against the generation interval T for the "
    "three loss levels. The pattern is the same everywhere. In the "
    "overload region (rho = N/T > 1, i.e., T = 2 and T = 3), FIFO's mean "
    f"AoI explodes to a horizon-dependent value ({fifo_ov2:,.0f} and "
    f"{fifo_ov3:,.0f} slots at p = 0.1) while LRP and AoG stay at "
    f"{lrp_ov2:.1f}/{aog_ov2:.1f} and {lrp_ov3:.1f}/{aog_ov3:.1f} slots. "
    "At saturation (T = 4) the policies are already close "
    f"({conv4:.1f} slots FIFO vs AoG "
    f"{g(4, 0.1, 'aog_aoi'):.1f}), and below half capacity (T >= 8) they "
    "coincide exactly - the negative case anticipated in Section 1. Loss "
    "shifts all curves upward but changes no ordering.")
figure("fig3_main", 16.2,
       "Figure 3. Mean AoI versus generation interval T (x labels show the "
       "offered load rho = N/T), for p = 0, 0.1, 0.3. Error bars are 95% "
       "confidence intervals over 10 paired seeds. FIFO's overload values "
       "grow with the simulated horizon because they are dominated by "
       "structurally starved sensors (Section 6.2); stationary detail is "
       "in Table 5.")
para(
    "The decisive comparison is Figure 4: at p = 0.1 the three policies "
    "achieve the same PDR at every load - they share the same channel, "
    "the same arrivals, and the same airtime - yet the delivered samples "
    f"under FIFO are on average {lag_f:.0f} slots old at overload, versus "
    f"{g(2, 0.1, 'lrp_lag'):.0f}-{g(2, 0.1, 'aog_lag'):.0f} for LRP/AoG, "
    "and the monitor's mean AoI differs by orders of magnitude. A network "
    "operator watching only PDR would see three identical systems; the "
    "monitor's knowledge tells the opposite story.")
figure("fig4_pdr_aoi", 11.5,
       "Figure 4. Same delivery rate, different freshness (p = 0.1): "
       "packet delivery ratio (top) is identical across policies at every "
       "load, while the mean age of delivered samples (middle) and the "
       "monitor's mean AoI (bottom) separate them sharply under overload.")
doc.add_heading("6.2 Where the difference comes from", level=2)
para(
    "Two mechanisms, both structural rather than incidental, explain the "
    "gap. (i) FIFO delivers stale payloads: under overload its queue sits "
    "at capacity and the head packet is already many slots old when "
    "served - the delivery lag of Figure 4 - while the newest arrivals "
    "are tail-dropped. (ii) Tail drop starves co-phased sensors: when "
    "several sensors generate in the same slot, the later-queued ones are "
    "always dropped once the queue is full, so one or two sensors stop "
    "being delivered altogether and their AoI grows without bound. "
    "Figure 5 shows a single run at T = 3 for the victim sensor: under "
    "FIFO its age climbs monotonically; under LRP and AoG it is a tight "
    "sawtooth. Because the starvation term grows with time, FIFO's "
    "overload mean AoI is not stationary - we therefore report peak AoI, "
    "delivery lag and per-sensor detail (Table 5), which are stationary, "
    "and flag the mean as horizon-dependent wherever it is quoted.")
figure("fig5_trajectory", 11.5,
       "Figure 5. Single-run trajectory of the starved sensor's age "
       "(T = 3, p = 0.1, seed 0). FIFO: monotone growth (structural "
       "starvation). LRP and AoG: bounded sawtooth.")
rows5 = []
for T in (2, 3):
    r = S[(T, 0.1)]
    rows5.append([f"T={T}", "FIFO",
                  f"{r['fifo_aoi']:,.0f}±{r['fifo_aoi_ci']:,.0f}",
                  f"{r['fifo_peak']:.1f}", f"{r['fifo_lag']:.1f}"])
    rows5.append(["", "LRP", f"{r['lrp_aoi']:.1f}±{r['lrp_aoi_ci']:.1f}",
                  f"{r['lrp_peak']:.1f}", f"{r['lrp_lag']:.1f}"])
    rows5.append(["", "AoG", f"{r['aog_aoi']:.1f}±{r['aog_aoi_ci']:.1f}",
                  f"{r['aog_peak']:.1f}", f"{r['aog_lag']:.1f}"])
table(["Load", "Policy", "Mean AoI (95% CI)", "Peak AoI",
       "Delivery lag"],
      rows5, widths=[2.2, 2.6, 5.4, 3.0, 3.4], fs=9,
      align_center_cols={2, 3, 4},
      cap="Table 5. Overload detail at p = 0.1. FIFO's mean is dominated "
          "by starved sensors (grows with horizon); its peak AoI and "
          "delivery lag are stationary and still far above LRP/AoG.")
doc.add_heading("6.3 Priority imbalance: LRP is fast-biased, AoG balances",
                level=2)
para(
    "With two fast sensors (T_f) and two slow sensors (T_s), the policies "
    "diverge in a second dimension (Figure 6, Table 6). Under overload "
    "(rho = 1.25 and 1.125), FIFO starves the slow group almost "
    f"completely (slow-group AoI {e2a['fifo_slow']:,.0f} slots at "
    "(2,8)); LRP protects freshness overall but its newest-first bias "
    f"leaves the slow group at {e2a['lrp_slow']:.1f} slots; AoG balances "
    f"both groups ({e2a['aog_fast']:.1f} fast / {e2a['aog_slow']:.1f} "
    "slow) because a sensor whose knowledge ages automatically gains "
    "priority. At the underloaded setting (4,16), rho = 0.625, all "
    "policies again coincide - the same negative case as in E1. "
    "Paired-difference intervals (Table 7) confirm that every separation "
    "quoted in this section excludes zero by a wide margin.")
figure("fig6_imbalance", 16.2,
       "Figure 6. Priority imbalance (p = 0.1): mean AoI per sensor group. "
       "Dark blue = fast group (T_f), light blue = slow group (T_s). Error "
       "bars are 95% CI over 10 paired seeds.")
rows6 = []
for r in E2:
    for pol, nm in (("fifo", "FIFO"), ("lrp", "LRP"), ("aog", "AoG")):
        slow = (f"{r[f'{pol}_slow']:,.0f}*"
                if r[f"{pol}_slow"] >= 1000 else f"{r[f'{pol}_slow']:.1f}")
        rows6.append([
            f"({int(r['T_fast'])},{int(r['T_slow'])})  rho={r['rho']:.2f}",
            nm, f"{r[f'{pol}_fast']:.1f}", slow, f"{r[f'{pol}_pdr']:.2f}"])
table(["(T_f, T_s)", "Policy", "Fast-group AoI", "Slow-group AoI", "PDR"],
      rows6, widths=[4.2, 2.4, 3.2, 3.6, 2.4], fs=9,
      align_center_cols={2, 3, 4},
      cap="Table 6. Imbalance experiment per group (p = 0.1). * FIFO's "
          "slow-group value is horizon-dependent (starvation).")
rows7 = []
for T in (2, 3):
    r = S[(T, 0.1)]
    for a, b, nm in (("aog", "fifo", "AoG - FIFO"),
                     ("lrp", "fifo", "LRP - FIFO"),
                     ("aog", "lrp", "AoG - LRP")):
        rows7.append([f"T={T}, p=0.1", nm,
                      f"{r[f'd_{a}-{b}']:+,.1f} ± {r[f'd_{a}-{b}_ci']:.1f}"])
table(["Configuration", "Paired difference", "Mean AoI difference (95% CI)"],
      rows7, widths=[4.4, 4.2, 7.8], fs=9, align_center_cols={2},
      cap="Table 7. Seed-paired differences of mean AoI at overload "
          "(p = 0.1). All intervals exclude zero; the FIFO differences are "
          "negative and enormous (starvation term).")

# =====================================================================
# 7. Discussion & limitations
# =====================================================================
doc.add_heading("7. Discussion and Limitations", level=1)
para(
    "When do these conclusions hold? The divergence between policies "
    "requires contention - offered load near or above one packet per "
    "slot. Below roughly half of capacity, periodic traffic never "
    "stresses the queue and any work-conserving policy is as fresh as "
    "any other; deploying AoG there adds complexity for nothing. The "
    "overload findings are structural: they follow from tail drop (FIFO) "
    "and newest-first selection (LRP) ignoring receiver state, not from "
    "any parameter choice, and they appear already at zero loss.")
para(
    "FIFO's overload mean AoI deserves an honest caveat: because starved "
    "sensors age forever, the mean grows linearly with the simulated "
    "horizon; the stationary evidence is the per-sensor delivery count, "
    "the peak AoI, and the delivery lag, and we report all three. A "
    "production remedy as simple as drop-oldest (instead of tail drop) "
    "would remove FIFO's starvation; it would not remove the "
    "stale-payload mechanism, and it converges toward LRP-style queue "
    "management - which is, in effect, the message of [2].")
para("Limitations, per the module's validation guide:", space_after=2)
bullets([
    "All parameters are illustrative and normalised (Table 2); no "
    "physical waveform, rate table, or measured trace is used.",
    "Losses are iid per slot; correlated fades would hit all policies "
    "through the same shared draws but could soften the LRP/AoG "
    "advantage by delaying knowledge of losses.",
    "No retransmission: with HARQ/ARQ a failed packet would be retried, "
    "which builds backlog and would push FIFO further toward the "
    "stale-delivery regime.",
    "Periodic arrivals with fixed phases make starvation deterministic "
    "once phases collide; jittered or Poisson arrivals would blur the "
    "victim identity but not the mechanism (bursty arrivals worsen "
    "FIFO).",
    "N = 4 sensors, single link, single hop; scaling N moves the "
    "contention point but not the ordering of the policies.",
    "AoI is a linear freshness penalty; non-linear value-of-information "
    "[6] or semantic metrics [9] would re-rank policies only if sensors "
    "differ in importance beyond their rates.",
])

# =====================================================================
# 8. Conclusion
# =====================================================================
doc.add_heading("8. Conclusion", level=1)
para(
    "For four sensors sharing one lossy link, we compared FIFO, "
    "latest-sample replacement, and an AoI-gain scheduler under paired "
    "seeds with identical channels and airtime. The three policies are "
    "indistinguishable in packet delivery ratio at every operating "
    "point, and indistinguishable in freshness below half capacity. "
    "Under overload they separate sharply: FIFO both delivers stale "
    "payloads and structurally starves sensors that share arrival slots; "
    "LRP keeps the system fresh but biases service toward fast sensors; "
    "the AoI-gain rule stays fresh and balanced because its priority "
    "grows automatically with a sensor's ignorance. The practical "
    "conclusion for monitoring systems is that PDR - the default health "
    "metric - is blind to exactly the failure modes that matter, and a "
    "one-line change in queue management and selection buys orders of "
    "magnitude in freshness precisely where capacity is scarce.")

# =====================================================================
# AI disclosure
# =====================================================================
doc.add_heading("AI Use Disclosure", level=1)
para(
    "In line with the module's mandatory disclosure requirement, this "
    "group states the following use of AI tools (Claude Code, Anthropic) "
    "in producing this report:", space_after=2)
bullets([
    "Literature search assistance: identifying candidate foundational "
    "references and search phrases; all final references were retrieved "
    "and read by the group.",
    "Code assistance: first-draft generation of the Python simulator, "
    "experiment runner, and plotting scripts. All code was reviewed, "
    "understood, modified, and re-run by the group; the baseline "
    "verification in Section 5.2 was designed to check the tool-built "
    "simulator against analytic ground truth.",
    "Writing assistance: drafting and language editing of report text "
    "from the group's outline, data, and decisions. All technical claims "
    "were checked against the group's own experimental output.",
])
rich([("[ACTION: replace this statement with the module's official AI "
       "disclosure template if one is provided on Brightspace, and adjust "
       "the wording to match actual usage.]",
      {"size": 9.5, "color": RED})])

# =====================================================================
# References
# =====================================================================
doc.add_heading("References", level=1)
refs = [
    "S. Kaul, R. D. Yates, and M. Gruteser, \"Real-time status: How often "
    "should one update?\" in Proc. IEEE INFOCOM, Orlando, FL, USA, 2012, "
    "pp. 2731-2735.",
    "M. Costa, M. Codreanu, and A. Ephremides, \"On the age of information "
    "in status update systems with packet management,\" IEEE Trans. Inf. "
    "Theory, vol. 62, no. 4, pp. 1897-1910, Apr. 2016.",
    "R. D. Yates and S. Kaul, \"Real-time status updating: Multiple "
    "sources,\" in Proc. IEEE ISIT, Cambridge, MA, USA, 2012, pp. 2666-2670.",
    "I. Kadota, A. Sinha, E. Uysal-Biyikoglu, R. Singh, and E. Modiano, "
    "\"Scheduling policies for minimizing age of information in broadcast "
    "wireless networks,\" IEEE/ACM Trans. Netw., vol. 26, no. 6, pp. "
    "1843-1856, Dec. 2018.",
    "Y. Sun, E. Uysal-Biyikoglu, R. D. Yates, C. E. Koksal, and N. B. "
    "Shroff, \"Update or wait: How to keep your data fresh,\" IEEE/ACM "
    "Trans. Netw., vol. 27, no. 6, pp. 2059-2071, Dec. 2019.",
    "A. Kosta, N. Pappas, A. Ephremides, and V. Angelakis, \"Age and value "
    "of information: Non-linear age case,\" in Proc. IEEE ISIT, Aachen, "
    "Germany, 2017, pp. 326-330.",
    "R. D. Yates, Y. Sun, D. R. Brown III, S. K. Kaul, E. Modiano, and S. "
    "Ulukus, \"Age of information: An introduction and survey,\" IEEE J. "
    "Sel. Areas Commun., vol. 39, no. 5, pp. 1183-1210, May 2021.",
    "R. Talak, S. Karaman, and E. Modiano, \"Distributed scheduling "
    "policies for optimizing information freshness in wireless networks,"
    "\" IEEE/ACM Trans. Netw., vol. 28, no. 5, pp. 2002-2015, Oct. 2020.",
    "X. Han, B. Feng, Y. Wu, X.-G. Xia, W. Zhang, and S. Sun, \"Age of "
    "semantic information-aware wireless transmission for remote "
    "monitoring systems,\" 2025, arXiv:2508.12248 (published version on "
    "IEEE Xplore).",
    "X. Xie, S. Gao, and H. Wang, \"Scheduling approaches for joint "
    "optimization of age and delay in industrial wireless networks,\" "
    "IEEE Trans. Ind. Inform., vol. 20, no. 7, Jul. 2024.",
    "Q. Zhang, Z. Xu et al., \"Optimal age of information and throughput "
    "scheduling in heterogeneous traffic wireless physical-layer security "
    "communications,\" IEEE Internet Things J., 2024.",
    "A. Morteza and D. Qiu, \"A novel Whittle index-based scheduling for "
    "age of information minimization in IoT networks,\" in Proc. IEEE "
    "SmartInternet, Nov. 2025.",
]
for i, ref in enumerate(refs, 1):
    p = doc.add_paragraph()
    r = p.add_run(f"[{i}] {ref}")
    r.font.size = Pt(9.5)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.first_line_indent = Cm(-0.8)
rich([("[VERIFY before submission: exact page numbers for [10] and [11], "
       "the full author list for [11], and the final proceedings name for "
       "[12] - confirm each entry on IEEE Xplore / Google Scholar and "
       "update this list.]",
      {"size": 9.5, "color": RED})])

# =====================================================================
# Appendix
# =====================================================================
doc.add_heading("Appendix A. Code and Reproducibility", level=1)
para(
    "The full code (aoi_sim.py, make_figures.py, make_report.py), raw "
    "per-run results (JSON/CSV), and figure scripts are available at:")
rich([("[INSERT GITHUB REPOSITORY LINK - create a repository, upload the "
       "topic09_report folder, and share the link here as instructed.]",
      {"bold": True, "color": RED})])
para("Reproduce all results and figures with:", space_after=2)
para("python aoi_sim.py       # ~6-8 min: verification, E1, E2, summaries",
     size=9.5)
para("python make_figures.py  # all figures and equation images",
     size=9.5)
para("python make_report.py   # regenerates this document", size=9.5)
para(
    "Each run's record is checkpointed to results/runs.jsonl, so any "
    "single number in this report can be traced back to its seed and "
    "configuration.")

doc.save(OUT)
print("saved:", OUT)
