from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import json
from pathlib import Path

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Relative path from metrics.py to the JSON file
telemetry_file = Path(__file__).parent.parent/ "q-vercel-latency.json"

# Load telemetry data
with open(telemetry_file) as f:
    telemetry = pd.DataFrame(json.load(f))

@app.post("/")
async def metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)
    
    result = {}
    for region in regions:
        df = telemetry[telemetry["region"] == region]
        if df.empty:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            }
            continue
        
        avg_latency = df["latency_ms"].mean()
        p95_latency = np.percentile(df["latency_ms"], 95)
        avg_uptime = df["uptime"].mean()
        breaches = (df["latency_ms"] > threshold).sum()
        
        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": int(breaches)
        }
        
    return JSONResponse(result)


