from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import pandas as pd

# Import your modules
from src.data import loader
from src.data import topology_loader
from src.models.defect_tracker import LatentDefectTracker
from src.twin_engine.inference import TwinPredictor  # <-- Teammate's ML Inference Engine

# --- Global State (In-Memory Data & Models) ---
app_state = {
    "tracker": None,
    "predictor": None, # <-- Holds the PyTorch MTL model runner
    "raw_data": None,
    "factory_dag": None,
    "station_configs": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Initializing Digital Twin Backend ---")
    
    try:
        # 1. Load Data & Configs dynamically
        print("Loading factory telemetry and metadata...")
        app_state["raw_data"] = loader.load_plant_data()
        app_state["station_configs"] = loader.load_station_configs()
        
        # 2. Load the Factory Graph
        print("Building factory topology DAG...")
        app_state["factory_dag"] = topology_loader.build_topology_graph()
        
        # 3. Initialize Teammate's PyTorch MTL Predictor
        print("Loading PyTorch Multi-Task Learning model...")
        try:
            from pathlib import Path
            # UPDATE THIS LINE to point to the exact folder:
            weights_path = Path(__file__).parent / "src" / "twin_engine" / "twin_mtl_model.pth"
            
            app_state["predictor"] = TwinPredictor(model_weights_path=str(weights_path), num_stations=40)
            print("Deep learning predictor loaded successfully.")
        except Exception as weights_err:
            print(f"WARNING: Could not load model weights yet. Error: {weights_err}")
        
        # 4. Initialize and Train the Defect Tracker (Isolation Forest for Problem 3)
        exclude_cols = [
            'time_step', 'station_id', 'is_parallel', 
            'part_defect_risk', 'bottleneck_risk', 'defect_risk'
        ]
        feature_columns = [col for col in app_state["raw_data"].columns if col not in exclude_cols]
        
        app_state["tracker"] = LatentDefectTracker(feature_columns=feature_columns)
        app_state["tracker"].train_healthy_baseline(app_state["raw_data"])
        
        print("--- Backend AI Engines Fully Loaded and Ready! ---")
        
    except Exception as e:
        print(f"CRITICAL STARTUP ERROR: {e}")
        
    yield 
    
    print("Shutting down Digital Twin engines...")


app = FastAPI(title="Digital Twin AI API", version="2.5", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Contracts ---
class DefectTraceRequest(BaseModel):
    final_station_id: str
    defect_time_step: int 


# --- API Endpoints ---

@app.get("/api/v1/topology")
def get_factory_topology():
    dag = app_state["factory_dag"]
    configs = app_state["station_configs"]
    
    if not dag or not configs:
        raise HTTPException(status_code=500, detail="Topology or configs not loaded")
    
    enriched_nodes = []
    for node_id in dag.nodes():
        node_info = {"id": node_id}
        if node_id in configs:
            config = configs[node_id]
            node_info.update({
                "type": config.station_type.value,
                "status": config.sensor_maturity.value
            })
        enriched_nodes.append(node_info)
    
    return {
        "nodes": enriched_nodes,
        "edges": list(dag.edges())
    }


@app.get("/api/v1/predict/status")
def get_live_predictions():
    """
    Feeds the most recent telemetry window (last 10 time steps) 
    into your teammate's PyTorch Dual-Head MTL model.
    Returns bottleneck and defect alerts with confidence scores.
    """
    predictor = app_state["predictor"]
    raw_data = app_state["raw_data"]
    
    if not predictor:
        raise HTTPException(status_code=500, detail="PyTorch model weights not found. Run model.py to train and save weights first.")
        
    if raw_data is None or raw_data.empty:
        raise HTTPException(status_code=500, detail="Plant telemetry data not loaded.")
        
    # Extract the maximum time step currently in the simulation data
    max_t = raw_data['time_step'].max()
    
    # Grab the rolling window of the last 10 time steps across all stations
    recent_window = raw_data[raw_data['time_step'] >= (max_t - 9)].copy()
    
    # Run inference using your teammate's class
    results = predictor.run_prediction(recent_window)
    return results


@app.post("/api/v1/trace/defect")
def trace_latent_defect(request: DefectTraceRequest):
    tracker = app_state["tracker"]
    raw_data = app_state["raw_data"]
    dag = app_state["factory_dag"]
    
    if not tracker or raw_data is None:
        raise HTTPException(status_code=500, detail="AI models are not initialized")
        
    root_cause = tracker.trace_root_cause(
        telemetry_df=raw_data, 
        dag=dag, 
        final_station=request.final_station_id,
        defect_time_step=request.defect_time_step
    )
    
    if root_cause:
        return {"success": True, "root_cause_station": root_cause}
    else:
        raise HTTPException(status_code=404, detail="No anomaly detected in upstream temporal path")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)