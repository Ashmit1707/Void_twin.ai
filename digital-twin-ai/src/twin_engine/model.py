from pathlib import Path
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split

# Ensure project root is in sys.path when running directly
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from src.twin_engine.dataset import PlantWideDataset
except ImportError:
    from dataset import PlantWideDataset

# ==========================================
# 1. Dual-Head MTL Architecture
# ==========================================
class DigitalTwinMTL(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2, num_classes: int = 41):
        super(DigitalTwinMTL, self).__init__()
        
        # Shared Temporal Physics Backbone
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0
        )
        
        # Output Head 1: Bottleneck Station Prediction (0 to 40)
        self.bottleneck_head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, num_classes)
        )
        
        # Output Head 2: Defect Station Prediction (0 to 40)
        self.defect_head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, num_classes)
        )

    def forward(self, x: torch.Tensor):
        lstm_out, _ = self.lstm(x)
        last_step = lstm_out[:, -1, :]  # Hidden state of the most recent time step
        
        bn_logits = self.bottleneck_head(last_step)
        def_logits = self.defect_head(last_step)
        return bn_logits, def_logits


# ==========================================
# 2. Training and Evaluation Pipeline
# ==========================================
def train_model():
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    csv_path = PROJECT_ROOT / "data" / "raw" / "plant_twin_data.csv"
    
    if not csv_path.exists():
        csv_path = Path(__file__).parent / "synthetic_factory_data.csv"
        
    dataset = PlantWideDataset(str(csv_path), window_size=10, is_training=True)
    
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    sample_x, _, _ = dataset[0]
    input_dim = sample_x.shape[1]
    
    model = DigitalTwinMTL(input_dim=input_dim, hidden_dim=64, num_layers=2, num_classes=41)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.003)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    epochs = 35
    print(f"--- Training Dual-Head MTL Model on {len(train_dataset)} Samples ({epochs} Epochs) ---")
    
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        
        for batch_x, batch_y_bn, batch_y_def in train_loader:
            optimizer.zero_grad()
            
            bn_logits, def_logits = model(batch_x)
            
            loss_bn = criterion(bn_logits, batch_y_bn)
            loss_def = criterion(def_logits, batch_y_def)
            loss = loss_bn + loss_def
            
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        avg_train_loss = total_loss / len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for vx, vy_bn, vy_def in val_loader:
                vbn, vdef = model(vx)
                vloss = criterion(vbn, vy_bn) + criterion(vdef, vy_def)
                val_loss += vloss.item()
        avg_val_loss = val_loss / len(val_loader)
        scheduler.step(avg_val_loss)
        
        if epoch % 5 == 0 or epoch == 1:
            print(f"Epoch [{epoch:02d}/{epochs:02d}] | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
            
    # Save the trained model weights
    model_path = Path(__file__).parent / "twin_mtl_model.pth"
    root_model_path = PROJECT_ROOT / "twin_mtl_model.pth"
    
    torch.save(model.state_dict(), model_path)
    torch.save(model.state_dict(), root_model_path)
    print(f"\nModel saved successfully to '{model_path}' and '{root_model_path}'")
    
    simulate_live_inference(model, dataset)


# ==========================================
# 3. Live Floor Inference Test
# ==========================================
def simulate_live_inference(model: nn.Module, dataset: PlantWideDataset):
    model.eval()
    print("\n--- Live Floor Prediction & False Alarm Suppression Test ---")
    
    test_indices = [
        ("Normal Flow Window (Step 50)", 40),
        ("Defect Window (Step 155, Station 12)", 145),
        ("Bottleneck Window (Step 450, Station 20)", len(dataset) - 10)
    ]
    
    with torch.no_grad():
        for name, idx in test_indices:
            idx = min(idx, len(dataset) - 1)
            sample_x, true_bn, true_def = dataset[idx]
            sample_x_batch = sample_x.unsqueeze(0)
            
            bn_logits, def_logits = model(sample_x_batch)
            
            bn_conf, pred_bn = torch.max(torch.softmax(bn_logits, dim=1), dim=1)
            def_conf, pred_def = torch.max(torch.softmax(def_logits, dim=1), dim=1)
            
            print(f"\n[{name}]")
            print(f"  Bottleneck -> Target: Station {true_bn.item():02d} | Pred: Station {pred_bn.item():02d} ({bn_conf.item()*100:.1f}% Conf)")
            print(f"  Defect     -> Target: Station {true_def.item():02d} | Pred: Station {pred_def.item():02d} ({def_conf.item()*100:.1f}% Conf)")


if __name__ == "__main__":
    train_model()