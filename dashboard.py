import streamlit as st
import pandas as pd
import torch
import numpy as np
from model import BottleneckPredictorLSTM
from dataset import PlantWideDataset

# --- Page Setup ---
st.set_page_config(page_title="AIC Digital Twin", layout="wide")
st.title("🏭 Plant Floor Digital Twin: Predictive Prediction Engine")

# --- Load Data & Model (Cached for speed) ---
@st.cache_resource
def load_system():
    # Load dataset
    dataset = PlantWideDataset("plant_twin_data.csv", window_size=10)
    
    # Recreate model and load weights
    sample_x, _ = dataset[0]
    input_dim = sample_x.shape[1]
    
    model = BottleneckPredictorLSTM(input_dim=input_dim, hidden_dim=64, num_layers=2, num_classes=41)
    # Use weights_only=True to safely load the model
    model.load_state_dict(torch.load("bottleneck_lstm_model.pth", weights_only=True))
    model.eval()
    
    # Load raw dataframe for visualization
    df = pd.read_csv("plant_twin_data.csv")
    return dataset, model, df

dataset, model, raw_df = load_system()

# --- Interactive Time Slider ---
st.sidebar.header("Time Control")
# Slider from step 10 (minimum window) to 499
current_step = st.sidebar.slider("Current Time Step", min_value=10, max_value=len(dataset)+9, value=295)

# --- Run Live Inference ---
# Dataset index is offset by window_size (10)
dataset_idx = current_step - 10
sample_x, true_target = dataset[dataset_idx]
sample_x_batch = sample_x.unsqueeze(0) # Add batch dimension

with torch.no_grad():
    logits = model(sample_x_batch)
    probabilities = torch.softmax(logits, dim=1)
    confidence, pred_station = torch.max(probabilities, dim=1)
    
pred_station = pred_station.item()
confidence_pct = confidence.item() * 100.0

# --- Dashboard Layout ---
col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("🔮 Predictive Engine")
    if confidence_pct > 80.0 and pred_station != 0:
        st.error(f"⚠️ HIGH BOTTLENECK RISK\n\n**Station {pred_station}**\n\nConfidence: {confidence_pct:.1f}%")
        st.write("**Recommended Action:** Inspect station, reduce incoming load.")
    else:
        st.success("✅ Line Flow: Normal. No bottlenecks detected.")

with col1:
    st.subheader("📊 Live Station Telemetry")
    # Show data for the current time step
    current_data = raw_df[raw_df['time_step'] == current_step]
    
    # Focus on the most critical stations (e.g., Station 19, 20, 21)
    # Show all 40 stations
    focus_stations = current_data
    
    # Format the table for display
    display_df = focus_stations[['station_id', 'cycle_time', 'queue_length', 'throughput']].copy()
    display_df.set_index('station_id', inplace=True)
    st.dataframe(display_df.style.highlight_max(axis=0, subset=['queue_length']))
    
st.markdown("---")
st.write("*(Prototype developed for Accenture Innovation Challenge)*")