"""Masked autoencoder pre-training on unlabeled 84-step daily weather sequences."""

import os, sys, numpy as np
import torch, torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader

DATA_DIR = os.path.join(os.path.dirname(__file__), "pretrain_data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

N_FEATURES = 4
HIDDEN_DIM = 64
N_LAYERS = 2
MASK_RATIO = 0.4
EPOCHS = 300
BATCH_SIZE = 64
LR = 1e-3

class MaskedLSTMAutoencoder(nn.Module):
    def __init__(self, n_features=N_FEATURES, hidden_dim=HIDDEN_DIM, n_layers=N_LAYERS):
        super().__init__()
        self.encoder = nn.LSTM(n_features, hidden_dim, n_layers, batch_first=True, dropout=0.2, bidirectional=False)
        self.decoder = nn.LSTM(hidden_dim, hidden_dim, n_layers, batch_first=True, dropout=0.2)
        self.proj = nn.Linear(hidden_dim, n_features)
        self.mask_token = nn.Parameter(torch.zeros(1, 1, n_features))
        nn.init.normal_(self.mask_token, std=0.02)

    def forward(self, x, mask_ratio=MASK_RATIO):
        B, T, D = x.shape
        mask = torch.rand(B, T, 1, device=x.device) < mask_ratio
        x_masked = x.clone()
        x_masked = x_masked * (~mask).float() + self.mask_token * mask.float()

        enc_out, (h, c) = self.encoder(x_masked)
        dec_out, _ = self.decoder(enc_out)
        x_recon = self.proj(dec_out)

        loss = F.mse_loss(x_recon[mask.expand(-1, -1, D)], x[mask.expand(-1, -1, D)])
        return x_recon, loss, mask

    def encode(self, x):
        enc_out, _ = self.encoder(x)
        return enc_out

def train():
    print("Loading pretrain data...")
    X = np.load(os.path.join(DATA_DIR, "weather_sequences.npy"))
    print(f"  Shape: {X.shape}")

    # Z-score normalize per feature across all samples
    mean = X.mean(axis=(0, 1), keepdims=True)
    std = X.std(axis=(0, 1), keepdims=True) + 1e-8
    X_norm = (X - mean) / std

    np.save(os.path.join(DATA_DIR, "pretrain_mean.npy"), mean.squeeze(axis=(0, 1)))
    np.save(os.path.join(DATA_DIR, "pretrain_std.npy"), std.squeeze(axis=(0, 1)))

    n_total = len(X_norm)
    n_train = int(n_total * 0.9)
    n_val = n_total - n_train

    X_tr = torch.tensor(X_norm[:n_train], dtype=torch.float32)
    X_va = torch.tensor(X_norm[n_train:], dtype=torch.float32)

    tr_loader = DataLoader(TensorDataset(X_tr), batch_size=BATCH_SIZE, shuffle=True)
    va_loader = DataLoader(TensorDataset(X_va), batch_size=BATCH_SIZE)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MaskedLSTMAutoencoder().to(device)
    print(f"  Model: {sum(p.numel() for p in model.parameters()):,} params")
    print(f"  Device: {device}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=15, factor=0.5)

    best_val = float('inf')
    patience = 0

    for epoch in range(1, EPOCHS + 1):
        model.train()
        tr_loss = 0
        for (xb,) in tr_loader:
            xb = xb.to(device)
            optimizer.zero_grad()
            _, loss, _ = model(xb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            tr_loss += loss.item()

        model.eval()
        va_loss = 0
        with torch.no_grad():
            for (xb,) in va_loader:
                xb = xb.to(device)
                _, loss, _ = model(xb)
                va_loss += loss.item()

        tr_loss /= len(tr_loader)
        va_loss /= len(va_loader)
        scheduler.step(va_loss)

        if va_loss < best_val:
            best_val = va_loss
            torch.save(model.state_dict(), os.path.join(MODEL_DIR, "autoencoder_best.pt"))
            patience = 0
        else:
            patience += 1

        if epoch % 20 == 0 or epoch == 1:
            print(f"  Epoch {epoch:3d} | Train: {tr_loss:.6f} | Val: {va_loss:.6f} | Best: {best_val:.6f} | LR: {optimizer.param_groups[0]['lr']:.2e}")

        if patience >= 50:
            print(f"  Early stopping at epoch {epoch}")
            break

    model.load_state_dict(torch.load(os.path.join(MODEL_DIR, "autoencoder_best.pt")))
    model.eval()

    # Save full model for fine-tuning
    torch.save({
        'model_state_dict': model.state_dict(),
        'hidden_dim': HIDDEN_DIM,
        'n_features': N_FEATURES,
        'n_layers': N_LAYERS,
    }, os.path.join(MODEL_DIR, "autoencoder_complete.pt"))

    print(f"\nPre-training done. Best val loss: {best_val:.6f}")
    print(f"Model saved to {MODEL_DIR}/autoencoder_complete.pt")

    # Quick reconstruction test
    X_va_t = X_va.to(device)
    with torch.no_grad():
        recon, _, mask = model(X_va_t[:4])
        D = X_va_t.shape[2]
        masked_mse = F.mse_loss(recon[mask.expand(-1, -1, D)], X_va_t[:4][mask.expand(-1, -1, D)])
        full_mse = F.mse_loss(recon, X_va_t[:4])
    print(f"  Test: masked MSE = {masked_mse:.6f}, full MSE = {full_mse:.6f}")

if __name__ == "__main__":
    train()
