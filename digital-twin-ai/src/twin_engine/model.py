from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from src.twin_engine.dataset import PlantWideDataset

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
    dataset = PlantWideDataset("data/raw/plant_twin_data.csv", window_size=10)
    
    # 80% Train, 20% Validation split
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    
    # Unpack the 3 items dataset[0] now returns to find the feature dimension
    sample_x, _, _ = dataset[0]
    input_dim = sample_x.shape[1]
    
    model = DigitalTwinMTL(input_dim=input_dim, hidden_dim=64, num_layers=2, num_classes=41)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    epochs = 25
    print(f"--- Training Dual-Head Model on {len(train_dataset)} Samples ---")
    
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        
        # The dataloader now yields batch_x, and TWO targets (Bottleneck and Defect)
        for batch_x, batch_y_bn, batch_y_def in train_loader:
            optimizer.zero_grad()
            
            # Forward pass through both heads
            bn_logits, def_logits = model(batch_x)
            
            # Dual Loss computation
            loss_bn = criterion(bn_logits, batch_y_bn)
            loss_def = criterion(def_logits, batch_y_def)
            loss = loss_bn + loss_def
            
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        avg_loss = total_loss / len(train_loader)
        
        if epoch % 5 == 0 or epoch == 1:
            print(f"Epoch [{epoch:02d}/{epochs:02d}] | Combined Loss: {avg_loss:.4f}")
            
    # Save the trained model weights
    # Save the trained model weights securely to the project root
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    model_path = PROJECT_ROOT / "src/twin_engine/twin_mtl_model.pth"
    
    torch.save(model.state_dict(), model_path)
    print(f"\nModel saved successfully as '{model_path}'")
    
    simulate_live_inference(model, dataset)


# ==========================================
# 3. Live Floor Inference Test
# ==========================================
def simulate_live_inference(model: nn.Module, dataset: PlantWideDataset):
    model.eval()
    print("\n--- Live Floor Prediction & False Alarm Suppression Test ---")
    
    # Take the very last observation window from the dataset
    sample_x, true_bn, true_def = dataset[len(dataset) - 1]
    sample_x_batch = sample_x.unsqueeze(0) # Add batch dimension for PyTorch
    
    with torch.no_grad():
        bn_logits, def_logits = model(sample_x_batch)
        
        bn_conf, pred_bn = torch.max(torch.softmax(bn_logits, dim=1), dim=1)
        def_conf, pred_def = torch.max(torch.softmax(def_logits, dim=1), dim=1)
        
    print(f"Bottleneck -> Target: Station {true_bn.item()} | Pred: Station {pred_bn.item()} ({bn_conf.item()*100:.1f}% Conf)")
    print(f"Defect     -> Target: Station {true_def.item()} | Pred: Station {pred_def.item()} ({def_conf.item()*100:.1f}% Conf)")


if __name__ == "__main__":
    train_model()