"""
TPP capsule line — very first-order digital-twin core
Author: Casey Frantz, Jun-2025
-----------------------------------------------------
1 printer  →  1 dryer  →  1 CT scanner
• Cycle-time distributions are triangular(min, mode, max) in minutes
• 5 % chance any printed capsule is scrap and is discarded early
• All times converted to hours for the SimPy clock
-----------------------------------------------------
"""

import simpy, random, statistics
from itertools import count

# ---------- CONFIGURABLE INPUTS ----------
SIM_HOURS       = 24                # how long to run the model
PRINTER_COUNT   = 1
DRYER_COUNT     = 1
CT_COUNT        = 1

PRINT_T         = (45, 55, 70)      # min, mode, max  (minutes)
DRY_T           = (40, 50, 80)
CT_T            = (10, 12, 15)

SCRAP_PROB      = 0.05              # 5 % scrap at printer
SEED            = 42                # reproducibility
# -----------------------------------------

random.seed(SEED)


def t(min_, mode, max_):
    """Draw a triangular RV and convert minutes → hours for SimPy."""
    return random.triangular(min_, max_, mode) / 60.0


class Capsule:
    _ids = count(0)

    def __init__(self):
        self.id = next(self._ids)


def printer_proc(env, dryer_res):
    """Continuously print capsules and pass good ones to the dryer."""
    while True:
        cap = Capsule()
        yield env.timeout(t(*PRINT_T))

        # decide scrap
        if random.random() < SCRAP_PROB:
            continue  # discard & print next capsule

        # good part → dryer
        env.process(dryer_proc(env, dryer_res, cap))


def dryer_proc(env, dryer_res, cap):
    with dryer_res.request() as req:
        yield req
        yield env.timeout(t(*DRY_T))
        env.process(ct_proc(env, ct_res, cap))


def ct_proc(env, ct_res, cap):
    with ct_res.request() as req:
        yield req
        yield env.timeout(t(*CT_T))
        completed_caps.append(cap.id)


def run_once():
    """Run one simulation and return KPI dictionary."""
    env = simpy.Environment()
    dryer_res = simpy.Resource(env, DRYER_COUNT)
    global ct_res
    ct_res = simpy.Resource(env, CT_COUNT)

    for _ in range(PRINTER_COUNT):
        env.process(printer_proc(env, dryer_res))

    env.run(until=SIM_HOURS)

    good = len(completed_caps)
    return {
        "capsules_good": good,
        "caps_per_day": good / (SIM_HOURS / 24),
    }


# --------- CLI entry point ---------
if __name__ == "__main__":
    completed_caps = []          # reset between runs
    kpi = run_once()
    print(f"Good capsules: {kpi['capsules_good']}")
    print(f"Throughput  : {kpi['caps_per_day']:.1f} caps / day")

