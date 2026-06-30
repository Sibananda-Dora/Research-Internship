import os, sys, numpy as np, joblib
import torch, torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
import xgboost as xgb
from sklearn.linear_model import RidgeCV, Ridge

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'prepared_data')
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.manual_seed(42)

# ─── Load Data (random splits: train 80%, val 10%, test 10%) ───
X_seq_tr = np.load(f'{DATA_DIR}/X_seq_daily_train.npy')
X_seq_va = np.load(f'{DATA_DIR}/X_seq_daily_val.npy')
X_seq_te = np.load(f'{DATA_DIR}/X_seq_daily_test.npy')
X_static_tr = np.load(f'{DATA_DIR}/X_static_train.npy')
X_static_va = np.load(f'{DATA_DIR}/X_static_val.npy')
X_static_te = np.load(f'{DATA_DIR}/X_static_test.npy')
X_xgb_tr = np.load(f'{DATA_DIR}/X_xgb_train.npy')
X_xgb_va = np.load(f'{DATA_DIR}/X_xgb_val.npy')
X_xgb_te = np.load(f'{DATA_DIR}/X_xgb_test.npy')
y_y_tr = np.load(f'{DATA_DIR}/y_yield_train.npy')
y_y_va = np.load(f'{DATA_DIR}/y_yield_val.npy')
y_y_te = np.load(f'{DATA_DIR}/y_yield_test.npy')
y_f_tr = np.load(f'{DATA_DIR}/y_fail_train.npy')
y_f_va = np.load(f'{DATA_DIR}/y_fail_val.npy')
y_f_te = np.load(f'{DATA_DIR}/y_fail_test.npy')

# Drop unused year arrays (kept only for backward compat with old temporal split stacking)
# y_tr_yr = np.load(f'{DATA_DIR}/year_train.npy')

print(f'Daily seq: train {X_seq_tr.shape}, val {X_seq_va.shape}, test {X_seq_te.shape}')
print(f'Static: train {X_static_tr.shape}')
print(f'XGB: train {X_xgb_tr.shape}')
print(f'Failure rate: train {y_f_tr.mean():.2%}, val {y_f_va.mean():.2%}, test {y_f_te.mean():.2%}')

# ─── Model Architecture ───
N_FEATURES = 4
SEQ_LEN = 84
HIDDEN_DIM = 64
N_LAYERS = 2
RAW_STATIC_DIM = X_static_tr.shape[1]       # 4: [district_idx, season_0, season_1, year]
EMBEDDING_DIM = 8                            # learned dense district embedding
N_DISTRICTS = 30
EFFECTIVE_STATIC_DIM = EMBEDDING_DIM + RAW_STATIC_DIM - 1  # 8 + 3 = 11
BATCH_SIZE = 16
EPOCHS = 150
LR = 5e-4
FAILURE_LOSS_WEIGHT = 3.0   # Scale up BCE to balance with MSE (Fix #2, recalibrated for temporal split)
FREEZE_EPOCHS = 10          # Freeze pretrained encoder for N epochs before unfreezing (Fix #4)

class LSTMAttention(nn.Module):
    def __init__(self, input_dim=N_FEATURES, hidden_dim=HIDDEN_DIM, n_layers=N_LAYERS,
                 static_dim=EFFECTIVE_STATIC_DIM, embedding_dim=EMBEDDING_DIM, n_districts=N_DISTRICTS):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.seq_len = SEQ_LEN
        self.district_embedding = nn.Embedding(n_districts, embedding_dim)
        self.encoder = nn.LSTM(input_dim, hidden_dim, n_layers, batch_first=True, dropout=0.2)
        self.pos_bias = nn.Parameter(torch.zeros(self.seq_len))
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim, 32), nn.Tanh(), nn.Linear(32, 1)
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim + static_dim, 32), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(32, 16), nn.ReLU(), nn.Dropout(0.2),
        )
        self.yield_head = nn.Linear(16, 1)
        self.failure_head = nn.Linear(16, 1)

    def forward(self, x_seq, x_static):
        B = x_seq.shape[0]
        enc_out, _ = self.encoder(x_seq)
        enc_out_norm = F.layer_norm(enc_out, enc_out.shape[-1:])
        raw_scores = self.attention(enc_out_norm).squeeze(-1)
        scores = raw_scores + self.pos_bias[:self.seq_len].unsqueeze(0)
        attn_weights = F.softmax(scores, dim=1)
        context = torch.sum(enc_out * attn_weights.unsqueeze(-1), dim=1)
        d_idx = x_static[:, 0].long()
        d_emb = self.district_embedding(d_idx)
        rest = x_static[:, 1:]
        combined = torch.cat([context, d_emb, rest], dim=1)
        features = self.fc(combined)
        y_pred = self.yield_head(features).squeeze(-1)
        f_logit = self.failure_head(features).squeeze(-1)
        return y_pred, f_logit, attn_weights

def roc_auc_score_metric(y_true, y_score):
    from sklearn.metrics import roc_auc_score
    try:
        return roc_auc_score(y_true, y_score)
    except:
        return 0.0

def load_pretrained_weights(model, pretrain_path):
    """Load encoder weights from pretrained autoencoder if available."""
    if not os.path.exists(pretrain_path):
        print("  No pretrained weights found. Training from scratch.")
        return False
    try:
        ckpt = torch.load(pretrain_path, map_location=device, weights_only=True)
        # The encoder state dict keys match: encoder.weight_ih_l0 etc.
        enc_state = {k: v for k, v in ckpt.items() if k.startswith('encoder.')}
        if not enc_state:
            if 'model_state_dict' in ckpt:
                enc_state = {k: v for k, v in ckpt['model_state_dict'].items() if k.startswith('encoder.')}
        if not enc_state:
            print("  No encoder keys found in pretrained checkpoint.")
            return False
        # Strip "encoder." prefix since model's LSTM is already named "encoder"
        enc_state_stripped = {k.replace('encoder.', ''): v for k, v in enc_state.items()}
        model.encoder.load_state_dict(enc_state_stripped, strict=False)
        # Freeze encoder
        for p in model.encoder.parameters():
            p.requires_grad = False
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())
        print(f"  Loaded pretrained encoder. Trainable: {trainable:,}/{total:,} params ({trainable/total*100:.1f}%)")
        return True
    except Exception as e:
        print(f"  Failed to load pretrained weights: {e}")
        return False

# ─── Build Model ───
model = LSTMAttention().to(device)
total_params = sum(p.numel() for p in model.parameters())
loaded = load_pretrained_weights(model, os.path.join(MODEL_DIR, 'autoencoder_complete.pt'))

# Graduated unfreezing: keep encoder frozen initially (Fix #4)
# Session notes showed frozen-only gave R2=0.215 and full-unfreeze gave 0.469.
# Graduated approach: freeze for FREEZE_EPOCHS, then unfreeze with lower LR.
# This lets attention+FC heads converge first, then fine-tunes encoder gently.
if not loaded:
    FREEZE_EPOCHS = 0  # Nothing to freeze if no pretrained weights

trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f'Total params: {total_params:,} | Trainable (phase 1): {trainable_params:,} ({trainable_params/total_params*100:.1f}%)')
if loaded:
    print(f'  Encoder frozen for first {FREEZE_EPOCHS} epochs, then unfreezing with LR/{10}')

pos_weight = torch.tensor([(y_f_tr == 0).sum() / (y_f_tr == 1).sum()]).to(device)

X_tr_t = torch.tensor(X_seq_tr, dtype=torch.float32)
Xs_tr_t = torch.tensor(X_static_tr, dtype=torch.float32)
y_y_tr_t = torch.tensor(y_y_tr, dtype=torch.float32)
y_f_tr_t = torch.tensor(y_f_tr, dtype=torch.float32)

X_va_t = torch.tensor(X_seq_va, dtype=torch.float32)
Xs_va_t = torch.tensor(X_static_va, dtype=torch.float32)
y_y_va_t = torch.tensor(y_y_va, dtype=torch.float32)
y_f_va_t = torch.tensor(y_f_va, dtype=torch.float32)

X_te_t = torch.tensor(X_seq_te, dtype=torch.float32)
Xs_te_t = torch.tensor(X_static_te, dtype=torch.float32)
y_y_te_t = torch.tensor(y_y_te, dtype=torch.float32)
y_f_te_t = torch.tensor(y_f_te, dtype=torch.float32)

tr_ds = TensorDataset(X_tr_t, Xs_tr_t, y_y_tr_t, y_f_tr_t)
tr_loader = DataLoader(tr_ds, batch_size=BATCH_SIZE, shuffle=True)

# ─── Training Loop ───
# Start with only trainable params (encoder frozen if pretrained)
optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=LR, weight_decay=1e-4)
best_val = float('inf')
patience = 0
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
encoder_unfrozen = not loaded  # Already unfrozen if no pretrained weights

for epoch in range(1, EPOCHS + 1):
    # Graduated unfreezing: unfreeze encoder after FREEZE_EPOCHS (Fix #4)
    if not encoder_unfrozen and epoch > FREEZE_EPOCHS:
        print(f"\n  >>> Unfreezing encoder at epoch {epoch} (graduated unfreezing)")
        for p in model.encoder.parameters():
            p.requires_grad = True
        encoder_unfrozen = True
        # Rebuild optimizer with differential LR: encoder at LR/10, heads at current LR
        head_params = [p for n, p in model.named_parameters() if not n.startswith('encoder.')]
        enc_params = list(model.encoder.parameters())
        current_lr = optimizer.param_groups[0]['lr']
        optimizer = torch.optim.AdamW([
            {'params': enc_params, 'lr': current_lr / 5},
            {'params': head_params, 'lr': current_lr}
        ], weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
        trainable_now = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"  Trainable now: {trainable_now:,}/{total_params:,} ({trainable_now/total_params*100:.1f}%)")
        print(f"  Encoder LR: {current_lr/5:.2e}, Heads LR: {current_lr:.2e}")
        patience = 0  # Reset patience after unfreezing

    model.train()
    tr_loss = 0.0
    for xb, xsb, yb, fb in tr_loader:
        xb, xsb, yb, fb = xb.to(device), xsb.to(device), yb.to(device), fb.to(device)
        optimizer.zero_grad()
        y_pred, f_logit, _ = model(xb, xsb)
        loss_y = F.mse_loss(y_pred, yb)
        loss_f = F.binary_cross_entropy_with_logits(f_logit, fb, pos_weight=pos_weight)
        # Weighted multi-task loss: scale up failure BCE to match MSE magnitude (Fix #2)
        loss = loss_y + FAILURE_LOSS_WEIGHT * loss_f
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        tr_loss += loss.item()

    model.eval()
    with torch.no_grad():
        y_pred, f_logit, attn_w = model(X_va_t.to(device), Xs_va_t.to(device))
        v_loss_y = F.mse_loss(y_pred, y_y_va_t.to(device))
        v_loss_f = F.binary_cross_entropy_with_logits(f_logit, y_f_va_t.to(device), pos_weight=pos_weight.to(device))
        v_loss = v_loss_y + FAILURE_LOSS_WEIGHT * v_loss_f

    tr_loss /= len(tr_loader)
    scheduler.step(v_loss)

    if v_loss < best_val:
        best_val = v_loss
        torch.save(model.state_dict(), os.path.join(MODEL_DIR, 'lstm_best.pt'))
        patience = 0
    else:
        patience += 1

    if epoch % 20 == 0 or epoch == 1:
        y_hat = y_pred.cpu().numpy()
        r2 = 1 - ((y_y_va - y_hat) ** 2).sum() / ((y_y_va - y_y_va.mean()) ** 2).sum()
        f_prob = torch.sigmoid(f_logit).cpu().numpy()
        auc = roc_auc_score_metric(y_f_va, f_prob)
        phase = 'frozen' if (loaded and not encoder_unfrozen) else 'full'
        print(f"  Epoch {epoch:3d} [{phase}] | Tr: {tr_loss:.4f} | V: {v_loss:.4f} "
              f"| R2: {r2:.3f} | AUC: {auc:.3f} | LR: {optimizer.param_groups[0]['lr']:.2e}")

    if patience >= 30:
        print(f"  Early stopping at epoch {epoch}")
        break

# ─── Final Evaluation (on held-out test set, years >= 2020) ───
model.load_state_dict(torch.load(os.path.join(MODEL_DIR, 'lstm_best.pt')))
model.eval()
with torch.no_grad():
    y_pred, f_logit, attn_w = model(X_te_t.to(device), Xs_te_t.to(device))
    y_hat = y_pred.cpu().numpy().flatten()
    f_prob = torch.sigmoid(f_logit).cpu().numpy().flatten()
    attn_w = attn_w.cpu().numpy()

r2 = 1 - ((y_y_te - y_hat) ** 2).sum() / ((y_y_te - y_y_te.mean()) ** 2).sum()
rmse = np.sqrt(((y_y_te - y_hat) ** 2).mean())
auc = roc_auc_score_metric(y_f_te, f_prob)

print(f"\n{'='*50}")
print("  LSTM FINAL PERFORMANCE (84-step daily)")
print(f"  Yield R2:  {r2:.3f}")
print(f"  Yield RMSE: {rmse:.3f} Q/Acre")
print(f"  Failure AUC: {auc:.3f}")
print(f"{'='*50}")

# Attention pattern
avg_attn = attn_w.mean(axis=0)
print(f"\n  Mean attention across test samples (84 days):")
print(f"  Peak week: {avg_attn.reshape(12, 7).sum(axis=1).argmax() + 1}")
print(f"  Weeks 4-6 attention: {avg_attn.reshape(12, 7)[3:6].sum():.2%}")

torch.save(model.state_dict(), os.path.join(MODEL_DIR, 'lstm_final.pth'))
torch.save({'input_dim': N_FEATURES, 'hidden_dim': HIDDEN_DIM, 'n_layers': N_LAYERS,
            'static_dim': EFFECTIVE_STATIC_DIM, 'embedding_dim': EMBEDDING_DIM,
            'n_districts': N_DISTRICTS, 'pretrained_encoder': loaded, 'seq_len': SEQ_LEN},
           os.path.join(MODEL_DIR, 'lstm_config.pth'))

# ─── Train XGBoost Models ───
print(f"\n{'='*50}")
print("  XGBoost Training")
xgb_reg = xgb.XGBRegressor(n_estimators=500, max_depth=4, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.8,
                            reg_alpha=1.0, reg_lambda=2.0, random_state=42,
                            monotone_constraints=(1, 0, 1, 1, -1, 0, -1, -1, 0, 0, 0, 0, 1, 0, 1, 1, 1, -1, 1, 0, 0, 0, 1))
xgb_reg.fit(X_xgb_tr, y_y_tr)
y_xgb = xgb_reg.predict(X_xgb_te)
r2_xgb = 1 - ((y_y_te - y_xgb) ** 2).sum() / ((y_y_te - y_y_te.mean()) ** 2).sum()
print(f"  XGB Regressor: R2 = {r2_xgb:.3f}")

neg_pos = (y_f_tr == 0).sum() / (y_f_tr == 1).sum()
xgb_clf = xgb.XGBClassifier(n_estimators=500, max_depth=4, learning_rate=0.05,
                             subsample=0.8, colsample_bytree=0.8,
                             reg_alpha=1.0, reg_lambda=2.0,
                             scale_pos_weight=neg_pos, random_state=42)
xgb_clf.fit(X_xgb_tr, y_f_tr)
f_xgb = xgb_clf.predict_proba(X_xgb_te)[:, 1]
auc_xgb = roc_auc_score_metric(y_f_te, f_xgb)
print(f"  XGB Classifier: AUC = {auc_xgb:.3f}")

xgb_reg.save_model(os.path.join(MODEL_DIR, 'xgb_regressor.json'))
xgb_clf.save_model(os.path.join(MODEL_DIR, 'xgb_classifier.json'))
print("  XGBoost models saved.")

# ─── Stacking Meta-Learner ───
# Calibrate convex blend weights on a chronological validation set (2018-2019).
# This avoids leaking test data into model calibration.
print(f"\n{'='*50}")
print("  Stacking Meta-Learner Calibration (Validation Set 2018-2019)")

# Get val predictions from both models
model.eval()
with torch.no_grad():
    y_pred_va, f_logit_va, _ = model(X_va_t.to(device), Xs_va_t.to(device))
    y_hat_va = y_pred_va.cpu().numpy().flatten()
    f_prob_va = torch.sigmoid(f_logit_va).cpu().numpy().flatten()
y_xgb_va = xgb_reg.predict(X_xgb_va)
f_xgb_va = xgb_clf.predict_proba(X_xgb_va)[:, 1]

best_w_y = 0.5
best_r2_y = -float('inf')
for w in np.linspace(0.2, 0.8, 61):
    y_blend = w * y_hat_va + (1 - w) * y_xgb_va
    ss_res = np.sum((y_y_va - y_blend) ** 2)
    ss_tot = np.sum((y_y_va - y_y_va.mean()) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    if r2 > best_r2_y:
        best_r2_y = r2
        best_w_y = w

best_w_f = 0.5
best_auc_f = -float('inf')
for w in np.linspace(0.2, 0.8, 61):
    f_blend = w * f_prob_va + (1 - w) * f_xgb_va
    auc = roc_auc_score_metric(y_f_va, f_blend)
    if auc > best_auc_f:
        best_auc_f = auc
        best_w_f = w

print(f"  Calibrated Stacking Weights (Validation Set {len(y_y_va)} samples):")
print(f"    Yield:   LSTM={best_w_y:.3f}, XGB={1-best_w_y:.3f} (R2: {best_r2_y:.3f})")
print(f"    Failure: LSTM={best_w_f:.3f}, XGB={1-best_w_f:.3f} (AUC: {best_auc_f:.3f})")

# Construct dummy Ridge objects for compatibility with predict.py
meta_yield = Ridge()
meta_yield.coef_ = np.array([best_w_y, 1 - best_w_y])
meta_yield.intercept_ = 0.0

meta_fail = Ridge()
meta_fail.coef_ = np.array([best_w_f, 1 - best_w_f])
meta_fail.intercept_ = 0.0

# Final evaluation on held-out test set using calibrated stacking
y_ens = meta_yield.predict(np.column_stack([y_hat, y_xgb]))
r2_ens = 1 - ((y_y_te - y_ens) ** 2).sum() / ((y_y_te - y_y_te.mean()) ** 2).sum()
print(f"  Stacked Yield R2 (Test 2020-2024): {r2_ens:.3f}")

f_ens = np.clip(meta_fail.predict(np.column_stack([f_prob, f_xgb])), 0, 1)
auc_ens = roc_auc_score_metric(y_f_te, f_ens)
print(f"  Stacked Failure AUC (Test 2020-2024): {auc_ens:.3f}")

# Save stacking weights
joblib.dump(meta_yield, os.path.join(MODEL_DIR, 'meta_yield.pkl'))
joblib.dump(meta_fail, os.path.join(MODEL_DIR, 'meta_fail.pkl'))
print("  Stacking meta-learners saved.")

# Also report naive average for comparison
y_naive = (y_hat + y_xgb) / 2
r2_naive = 1 - ((y_y_te - y_naive) ** 2).sum() / ((y_y_te - y_y_te.mean()) ** 2).sum()
print(f"\n  (Comparison) Naive Average R2: {r2_naive:.3f}")
print(f"\n  Random split summary:")
print(f"    Train:      80% ({len(y_y_tr)} samples)")
print(f"    Validation: 10% ({len(y_y_va)} samples)")
print(f"    Test:       10% ({len(y_y_te)} samples)")
print("  Done.")
