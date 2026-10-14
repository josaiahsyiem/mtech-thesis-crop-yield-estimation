"""One way to test every model (Phase 5). Used by all later phases.

evaluate(make_model, X, y, folds, schemes) fits the model in every fold of every scheme,
collects the test predictions and returns the metrics:
  - per fold, then averaged over the folds (as Cao et al. 2026 report r), and
  - pooled over all test predictions of a scheme (one r over everything).
Yield is in q/acre, so RMSE, MAE and bias are in q/acre.
"""
import numpy as np
import pandas as pd
from scipy import stats

SCHEMES = ["random", "group", "block", "loyo", "loto"]          # columns in folds_v2.csv
MAIN = "group"                                                   # main score: spatial group 5-fold


def metrics(y, p):
    """All metrics for one set of true (y) and predicted (p) yields."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    e = p - y
    lo, hi = y <= np.quantile(y, 0.10), y >= np.quantile(y, 0.90)
    out = {"n": len(y),
           "r": stats.pearsonr(y, p)[0] if len(y) > 2 and np.std(p) > 0 else np.nan,
           "rho": stats.spearmanr(y, p)[0] if len(y) > 2 and np.std(p) > 0 else np.nan,
           "R2": 1 - np.sum(e ** 2) / np.sum((y - y.mean()) ** 2),
           "RMSE_q_acre": np.sqrt(np.mean(e ** 2)),
           "MAE_q_acre": np.mean(np.abs(e)),
           "bias_q_acre": np.mean(e),
           "MAE_low10_q_acre": np.mean(np.abs(e[lo])),
           "MAE_high10_q_acre": np.mean(np.abs(e[hi]))}
    out["NRMSE_pct"] = 100 * out["RMSE_q_acre"] / y.mean()
    return out


def fold_columns(folds, scheme):
    """Fold-id columns of one scheme (several seeds for random, group and block)."""
    return [c for c in folds.columns if c == scheme or c.startswith(scheme + "_s")]


def evaluate(make_model, X, y, folds, schemes=SCHEMES, min_test=10, fit_kwargs=None):
    """make_model(): returns a new unfitted model with fit/predict.
    X: DataFrame of features (index = uid), y: Series (index = uid), folds: DataFrame (index = uid).
    Returns (per_fold table, summary table, out-of-fold predictions)."""
    fit_kwargs = fit_kwargs or {}
    rows, preds = [], []
    for scheme in schemes:
        for col in fold_columns(folds, scheme):
            f = folds.loc[X.index, col]
            for k in sorted(f.dropna().unique()):
                test = (f == k).values
                if test.sum() < min_test:            # too few test fields (e.g. Deoni, 2 fields): train only
                    continue
                m = make_model()
                m.fit(X[~test], y[~test], **fit_kwargs)
                p = np.asarray(m.predict(X[test]), float).ravel()
                rows.append({"scheme": scheme, "repeat": col, "fold": k, **metrics(y[test], p)})
                preds.append(pd.DataFrame({"uid": X.index[test], "scheme": scheme, "repeat": col, "fold": k,
                                           "y": y[test].values, "pred": p}))
    per_fold = pd.DataFrame(rows); oof = pd.concat(preds, ignore_index=True)
    summ = []
    for scheme, g in per_fold.groupby("scheme", sort=False):
        mean, sd = g.drop(columns=["scheme", "repeat", "fold", "n"]).mean(), g.drop(columns=["scheme", "repeat", "fold", "n"]).std()
        pooled = pd.DataFrame([metrics(o["y"], o["pred"]) for _, o in oof[oof["scheme"] == scheme].groupby("repeat")]).mean()
        row = {"scheme": scheme, "folds": len(g)}
        for k in ["r", "R2", "RMSE_q_acre", "MAE_q_acre", "NRMSE_pct", "bias_q_acre", "rho", "MAE_low10_q_acre", "MAE_high10_q_acre"]:
            row[f"{k}_mean"], row[f"{k}_sd"] = mean[k], sd[k]
        row["r_pooled"], row["R2_pooled"] = pooled["r"], pooled["R2"]
        summ.append(row)
    return per_fold, pd.DataFrame(summ), oof


def compare(per_fold_a, per_fold_b, metric="RMSE_q_acre", scheme=MAIN, n_train_test_ratio=0.25):
    """Is model A different from model B on the same folds?
    Wilcoxon signed-rank test and the corrected resampled t-test (Nadeau and Bengio 2003)."""
    key = ["scheme", "repeat", "fold"]
    a = per_fold_a[per_fold_a["scheme"] == scheme].set_index(key)[metric]
    b = per_fold_b[per_fold_b["scheme"] == scheme].set_index(key)[metric]
    d = (a - b).dropna(); k = len(d)
    w = stats.wilcoxon(d) if k > 5 and d.abs().sum() > 0 else None
    var = d.var(ddof=1) * (1 / k + n_train_test_ratio)                 # test/train size ratio, about 1/4 for 5-fold
    t = d.mean() / np.sqrt(var) if var > 0 else np.nan
    p_t = 2 * stats.t.sf(abs(t), k - 1) if np.isfinite(t) else np.nan
    return {"metric": metric, "scheme": scheme, "folds": k, "mean_diff_A_minus_B": d.mean(),
            "wilcoxon_p": w.pvalue if w else np.nan, "corrected_t": t, "corrected_t_p": p_t}


class MeanBaseline:
    """Predicts the training mean."""
    def fit(self, X, y): self.m = float(np.mean(y)); return self
    def predict(self, X): return np.full(len(X), self.m)


class GroupMeanBaseline:
    """Predicts the training mean of the same year x variety; falls back to the year mean, then the overall mean."""
    def fit(self, X, y):
        d = X[["year", "variety"]].assign(y=np.asarray(y))
        self.yv = d.groupby(["year", "variety"])["y"].mean(); self.yr = d.groupby("year")["y"].mean(); self.all = d["y"].mean()
        return self
    def predict(self, X):
        out = []
        for yr, v in zip(X["year"], X["variety"]):
            out.append(self.yv.get((yr, v), self.yr.get(yr, self.all)))
        return np.array(out, float)
