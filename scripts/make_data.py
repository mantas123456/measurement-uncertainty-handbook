"""Generate the synthetic datasets used by the handbook notebooks.

Every number here is invented. No real laboratory, client or employer data is
used, copied or "anonymised". The datasets imitate one plausible method,
copper (Cu) in water by ICP-OES, so that the chapters can follow a single
measurand from validation to the reported result.

Datasets written to data/synthetic/:

- blanks.csv       blank replicates over 3 days (for LOD/LOQ)
- calibration.csv  6-level calibration with 3 replicates (for linearity)
- qc.csv           60 runs of a control sample (for Nordtest u(Rw), control charts)
- pt.csv           12 proficiency-testing rounds (for bias, z-scores, En numbers)

The script is seeded, so the same version always writes byte-identical files.
Run it with ``--check`` to confirm that the committed CSVs match the script
(CI does this on every push).

Usage::

    python scripts/make_data.py            # write the CSVs
    python scripts/make_data.py --check    # exit 1 if a CSV differs
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

# One fixed seed for the whole handbook. Each dataset draws from its own child
# stream (SeedSequence.spawn), so changing one generator never changes the
# numbers in another dataset.
SEED: int = 20261122

OUT_DIR: Path = Path(__file__).resolve().parents[1] / "data" / "synthetic"

# Shared "truth" about the fictional laboratory. The QC and PT generators use
# the same bias and precision, so the Nordtest chapter gets a consistent story:
# what the QC chart shows about precision matches what PT shows about bias.
LAB_RELATIVE_BIAS: float = 0.012
"""+1.2 % bias: small, typical of a calibration-standard or matrix effect that
a lab would not correct but must include in its uncertainty."""

LAB_RSD_RW: float = 0.03
"""3 % relative within-lab reproducibility s(Rw) for Cu at tens of ug/L by
ICP-OES: inside the 2-5 % range usually seen for this technique and level."""


def make_blanks(rng: np.random.Generator) -> pd.DataFrame:
    """Blank replicates: 3 days x 10 replicates, in ug/L Cu.

    Assumptions:
    - Results are reported blank-signal-corrected against the calibration
      zero, so the expected value is a small residual contamination, not zero:
      0.40 ug/L from reagents and labware.
    - Within-day (repeatability) SD 0.25 ug/L: noise near the detection limit
      of a radial/axial ICP-OES at 324.754 nm.
    - A between-day SD of 0.10 ug/L, so the data show why LOD should be
      estimated over several days (Eurachem) rather than in one sequence.
    - Negative values are kept. Instruments report them, and replacing them
      with zero or "<LOD" would bias the SD downwards.
    """
    n_days, n_reps = 3, 10
    true_blank, sd_within, sd_between = 0.40, 0.25, 0.10

    day_offsets = rng.normal(0.0, sd_between, size=n_days)
    rows = []
    for day in range(n_days):
        values = true_blank + day_offsets[day] + rng.normal(0.0, sd_within, size=n_reps)
        for rep, value in enumerate(values, start=1):
            rows.append({"day": day + 1, "replicate": rep, "cu_ug_L": round(float(value), 3)})
    return pd.DataFrame(rows)


def make_calibration(rng: np.random.Generator) -> pd.DataFrame:
    """Calibration standards: 6 levels x 3 replicates, intensity in counts/s.

    Assumptions:
    - Levels 0, 10, 25, 50, 100 and 200 ug/L: a working range typical for Cu
      in waters, with the control sample (50 ug/L) in the middle.
    - The true response is linear: 150 cps intercept (plasma background) and
      a slope of 1200 cps per ug/L. Linearity tests should therefore pass;
      curvature examples will get their own dataset later.
    - Noise SD = sqrt(40^2 + (0.01 * signal)^2) cps: a constant floor near
      zero plus 1 % RSD at higher signal. This heteroscedasticity is what makes
      weighted regression worth discussing in chapter 2.
    - Replicates are independent preparations of the same level.
    """
    levels = np.array([0.0, 10.0, 25.0, 50.0, 100.0, 200.0])
    n_reps = 3
    intercept, slope = 150.0, 1200.0
    sd_floor, rsd = 40.0, 0.01

    rows = []
    for level_idx, conc in enumerate(levels, start=1):
        true_signal = intercept + slope * conc
        sd = np.sqrt(sd_floor**2 + (rsd * true_signal) ** 2)
        for rep in range(1, n_reps + 1):
            signal = true_signal + rng.normal(0.0, sd)
            rows.append(
                {
                    "level": level_idx,
                    "replicate": rep,
                    "cu_ug_L": conc,
                    "intensity_cps": round(float(signal), 1),
                }
            )
    return pd.DataFrame(rows)


def make_qc(rng: np.random.Generator) -> pd.DataFrame:
    """Control sample: 60 runs, Mon/Wed/Fri from 5 January 2026, in ug/L Cu.

    Assumptions:
    - The control is an in-house material with an assigned (target) value of
      50.0 ug/L, run once per analytical run.
    - The lab's results scatter with the shared s(Rw) (3 % RSD, 1.5 ug/L)
      around the target plus the shared +1.2 % bias.
    - The process is in statistical control: no shifts or trends are planted.
      Control-chart rule examples (chapter 4) will use separate scenario files,
      so that u(Rw) for the Nordtest example is not inflated by a fault.
    - 60 runs give a stable s(Rw) estimate (Nordtest TR 537 recommends at
      least a year of data or enough runs to cover normal variation).
    """
    n_runs = 60
    target = 50.0
    dates = pd.bdate_range("2026-01-05", periods=n_runs, freq="C", weekmask="Mon Wed Fri")
    mean = target * (1.0 + LAB_RELATIVE_BIAS)
    values = rng.normal(mean, LAB_RSD_RW * target, size=n_runs)
    return pd.DataFrame(
        {
            "run": np.arange(1, n_runs + 1),
            "date": dates.strftime("%Y-%m-%d"),
            "target_ug_L": target,
            "cu_ug_L": np.round(values, 2),
        }
    )


def make_pt(rng: np.random.Generator) -> pd.DataFrame:
    """Proficiency testing: 12 quarterly rounds, 2024-2026, in ug/L Cu.

    Assumptions:
    - Assigned values x_pt are spread over the working range, 20-150 ug/L, as
      real PT schemes vary the level between rounds.
    - u(x_pt) is 1.5 % of x_pt: a consensus value from many participants
      (ISO 13528, u = 1.25 s*/sqrt(p)) is usually known to 1-2 %.
    - sigma_pt is 10 % of x_pt: a common fitness-for-purpose standard
      deviation for trace metals in water.
    - The lab's result = x_pt * (1 + 1.2 % bias) + noise with 3 % RSD, the
      same bias and precision as the QC data.
    - The lab reports U with k = 2 and a relative expanded uncertainty of
      7 %, as if taken from its own uncertainty budget. En numbers use it.
    """
    n_rounds = 12
    dates = pd.date_range("2024-02-15", periods=n_rounds, freq="3MS") + pd.Timedelta(days=14)
    x_pt = np.round(rng.uniform(20.0, 150.0, size=n_rounds), 1)
    u_x_pt = np.round(0.015 * x_pt, 2)
    sigma_pt = np.round(0.10 * x_pt, 2)
    lab = x_pt * (1.0 + LAB_RELATIVE_BIAS) + rng.normal(0.0, LAB_RSD_RW * x_pt)
    lab = np.round(lab, 1)
    k = 2.0
    lab_U = np.round(0.07 * lab, 1)
    return pd.DataFrame(
        {
            "round": np.arange(1, n_rounds + 1),
            "date": dates.strftime("%Y-%m-%d"),
            "x_pt_ug_L": x_pt,
            "u_x_pt_ug_L": u_x_pt,
            "sigma_pt_ug_L": sigma_pt,
            "lab_result_ug_L": lab,
            "lab_U_ug_L": lab_U,
            "k": k,
        }
    )


# File name -> generator. The order fixes which child seed each dataset gets;
# append new datasets at the end so existing files keep their numbers.
GENERATORS: dict[str, Callable[[np.random.Generator], pd.DataFrame]] = {
    "blanks.csv": make_blanks,
    "calibration.csv": make_calibration,
    "qc.csv": make_qc,
    "pt.csv": make_pt,
}


def build_all() -> dict[str, str]:
    """Return each dataset as CSV text, keyed by file name."""
    children = np.random.SeedSequence(SEED).spawn(len(GENERATORS))
    out: dict[str, str] = {}
    for (name, generator), child in zip(GENERATORS.items(), children, strict=True):
        frame = generator(np.random.default_rng(child))
        out[name] = frame.to_csv(index=False, lineterminator="\n")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="output folder")
    parser.add_argument(
        "--check", action="store_true", help="compare with the files on disk; write nothing"
    )
    args = parser.parse_args(argv)

    datasets = build_all()
    if args.check:
        stale = [
            name
            for name, text in datasets.items()
            if not (args.out / name).exists()
            or (args.out / name).read_text(encoding="utf-8") != text
        ]
        if stale:
            print(f"Out of date: {', '.join(stale)}. Run: python scripts/make_data.py")
            return 1
        print(f"All {len(datasets)} datasets match scripts/make_data.py.")
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    for name, text in datasets.items():
        (args.out / name).write_text(text, encoding="utf-8", newline="")
        print(f"wrote {args.out / name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
