"""Is the proxy generator biased on the 5-day share checks that are xfail in tests/test_proxy.py?

    .venv/bin/python experiments/proxy_bias/bias_check.py 200      # 200 independent 5-day campaigns (fresh seeds)

Each campaign draws D1-D5 with seeds 10000 + 10 c + k and normalised day factors (as `thesis_sumo.proxy.generate`
does for the committed days), scores them with the test's own `_rates` / `_signalled`, and prints the mean and SD
of the relative error against the target: motorcycle red running per approach, car red running and car early start
pooled. A mean near 0 with an SD that covers the committed days' error means the xfail is sampling noise.
"""

import sys
import tempfile
from pathlib import Path

import numpy as np

from thesis_sumo.config import REPO_ROOT, load_site
from thesis_sumo.proxy import generate

sys.path.insert(0, str(REPO_ROOT / "tests"))
import test_proxy as T  # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
site, tg = load_site(T.PROXY_SITE), T._targets()
res = {"red_moto": {a: [] for a in T.APPROACHES}, "early_car": [], "red_car": []}
with tempfile.TemporaryDirectory() as tmp:
    for c in range(n):
        seeds = {f"PROXY_D{k}": 10000 + 10 * c + k for k in range(1, 6)}
        fac = generate.campaign_day_factors(tg, seeds)
        days = []
        for d, s in seeds.items():
            out = Path(tmp) / f"c{c}" / d
            generate.generate_day(tg, site, d, s, out, day_factors=fac[d])
            days.append(T._read(out))
        for kind in ("red", "early"):
            got = [T._rates(T._signalled(t), kind) for t in days]
            if kind == "red":
                for a in T.APPROACHES:
                    res["red_moto"][a].append(np.mean([g[(a, "moto")] for g in got]))
            res[f"{kind}_car"].append(np.mean([g[(a, "car")] for g in got for a in T.APPROACHES]))
red, early = T._t("M3_red_running.red_run_share"), T._t("M2_early_start.early_start_share")
print(f"{n} campaigns, relative error vs target: mean, sd, min, max")
for a in T.APPROACHES:
    x = np.array(res["red_moto"][a]) / red[a]["moto"] - 1
    print(f"red moto {a}: {x.mean():+.3f} {x.std(ddof=1):.3f} {x.min():+.3f} {x.max():+.3f}")
for k, w in (("red_car", np.mean([red[a]["car"] for a in T.APPROACHES])),
             ("early_car", np.mean([early[a]["car"] for a in T.APPROACHES]))):
    x = np.array(res[k]) / w - 1
    print(f"{k}: {x.mean():+.3f} {x.std(ddof=1):.3f} {x.min():+.3f} {x.max():+.3f}")
