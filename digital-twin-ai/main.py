from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import pandas as pd

# Import your dynamic modules mapped to your exact folder structure
from src.data import loader
from src.data import topology_loader
from src.models.defect_tracker import LatentDefectTracker

# --- Global State (In-Memory Data) ---
app_state = {
    "tracker": None,
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
        
        # 3. Dynamically discover ML features while PREVENTING DATA LEAKAGE
        # We must hide the 'cheat' target columns from the Unsupervised AI
        exclude_cols = [
            'time_step', 'station_id', 'is_parallel', 
            'part_defect_risk', 'bottleneck_risk', 'defect_risk'
        ]
        feature_columns = [col for col in app_state["raw_data"].columns if col not in exclude_cols]
        print(f"Discovered AI features: {feature_columns}")
        
        # 4. Initialize and Train the Defect Tracker
        app_state["tracker"] = LatentDefectTracker(feature_columns=feature_columns)
        app_state["tracker"].train_healthy_baseline(app_state["raw_data"])
        
        print("--- Backend AI Engines Fully Loaded and Ready! ---")
        
    except Exception as e:
        print(f"CRITICAL STARTUP ERROR: {e}")
        
    yield 
    
    print("Shutting down Digital Twin engines...")


app = FastAPI(title="Digital Twin AI API", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW Data Contract (Time-Series Based) ---
class DefectTraceRequest(BaseModel):
    final_station_id: str
    defect_time_step: int  # Shifted from vehicle_id to discrete time snapshot


# --- API Endpoints ---
@app.get("/api/v1/topology")
def get_factory_topology():
    """
    Returns the graph nodes and edges to the React UI so it can render the dashboard.
    """
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

@app.post("/api/v1/trace/defect")
def trace_latent_defect(request: DefectTraceRequest):
    """
    Triggers the Time-Space reverse DAG traversal to find root causes.
    """
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