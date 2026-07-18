"""Standalone evaluation of the existing trained models on the held-out test set.

This script does NOT modify any existing code or retrain models. It loads the
saved prepared test arrays (deterministic random_state=42 split) and the saved
model weights, then computes a full set of measured metrics for the three model
families (LSTM, XGBoost, Stacked). Results are printed and dumped to
metrics_eval.json (separate from version.json, which remains the pipeline's
single source of truth).
"""
import json
import os
import warnings

import numpy as np
import joblib
import torch

warnings.filterwarnings("ignore")

from sklearn.metrics import (
    roc_auc_score,
    f1_score,
    precision_score,
    recall_score,
    accuracy_score,
)

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "prepared_data")
MODEL_DIR = os.path.join(BASE, "models")

device = torch.device("cpu")


def load_test_arrays():
    d = DATA_DIR
    return {
        "seq": np.load(f"{d}/X_seq_daily_test.npy").astype(np.float32),
        "static": np.load(f"{d}/X_static_test.npy").astype(np.float32),
        "xgb": np.load(f"{d}/X_xgb_test.npy").astype(np.float32),
        "y_yield": np.load(f"{d}/y_yield_test.npy").astype(np.float32),
        "y_fail": np.load(f"{d}/y_fail_test.npy").astype(np.float32),
    }


def r2(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return 1 - ss_res / ss_tot


def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true, y_pred):
    return float(np.mean(np.abs(y_true - y_pred)))


def classification_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    return {
        "auc": float(roc_auc_score(y_true, y_prob)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "threshold": threshold,
        "pos_rate": float(y_true.mean()),
    }


def optimal_threshold_f1(y_true, y_prob):
    """Best F1 over a sweep of thresholds (handles class imbalance honestly)."""
    best_f1, best_t = -1.0, 0.5
    for t in np.linspace(0.05, 0.95, 91):
        y_pred = (y_prob >= t).astype(int)
        f = f1_score(y_true, y_pred, zero_division=0)
        if f > best_f1:
            best_f1, best_t = f, float(t)
    return {"f1_opt": float(best_f1), "threshold_opt": float(round(best_t, 2))}


def main():
    from predict import CDTPredictor  # safe: no training at import

    arr = load_test_arrays()
    X_seq = torch.tensor(arr["seq"], dtype=torch.float32)
    X_static = torch.tensor(arr["static"], dtype=torch.float32)
    X_xgb = arr["xgb"]
    y_y = arr["y_yield"]
    y_f = arr["y_fail"]

    print(f"Test partition: {len(y_y)} samples | failure pos-rate: {y_f.mean():.2%}")

    p = CDTPredictor()

    # ---- LSTM forward on the prepared (already scaled) test tensors ----
    p.dnn.eval()
    with torch.no_grad():
        y_lstm_t, f_lstm_logit, _ = p.dnn(X_seq, X_static)
    y_lstm = y_lstm_t.cpu().numpy().flatten()
    f_lstm = torch.sigmoid(f_lstm_logit).cpu().numpy().flatten()

    # ---- XGBoost ----
    y_xgb = p.xgb_reg.predict(X_xgb)
    f_xgb = p.xgb_clf.predict_proba(X_xgb)[:, 1]

    # ---- Stacked (convex blend via saved meta-learners) ----
    y_ens = p.meta_yield.predict(np.column_stack([y_lstm, y_xgb]))
    f_ens = np.clip(p.meta_fail.predict(np.column_stack([f_lstm, f_xgb])), 0, 1)

    # ---- Naive average (baseline reported in train.py) ----
    y_naive = (y_lstm + y_xgb) / 2
    f_naive = (f_lstm + f_xgb) / 2

    families = {
        "LSTM": (y_lstm, f_lstm),
        "XGBoost": (y_xgb, f_xgb),
        "Stacked": (y_ens, f_ens),
        "NaiveAvg": (y_naive, f_naive),
    }

    results = {}
    print("\n" + "=" * 78)
    print(f"{'Family':<10}{'Yield R2':>10}{'RMSE':>10}{'MAE':>10}"
          f"{'AUC':>10}{'F1@.5':>9}{'Prec':>8}{'Rec':>8}{'Acc':>8}")
    print("-" * 78)
    for name, (y_pred, f_prob) in families.items():
        reg = {"r2": float(r2(y_y, y_pred)), "rmse": rmse(y_y, y_pred),
               "mae": mae(y_y, y_pred)}
        clf = classification_metrics(y_f, f_prob, threshold=0.5)
        opt = optimal_threshold_f1(y_f, f_prob)
        results[name] = {"yield": reg, "failure": {**clf, **opt}}
        print(f"{name:<10}{reg['r2']:>10.3f}{reg['rmse']:>10.3f}{reg['mae']:>10.3f}"
              f"{clf['auc']:>10.3f}{clf['f1']:>9.3f}{clf['precision']:>8.3f}"
              f"{clf['recall']:>8.3f}{clf['accuracy']:>8.3f}")
    print("=" * 78)
    print("Note: F1/Precision/Recall/Accuracy @ threshold 0.5; "
          "f1_opt = best-F1 over threshold sweep (imbalanced set).")

    out = os.path.join(BASE, "metrics_eval.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nMetrics written to {out}")


if __name__ == "__main__":
    main()
