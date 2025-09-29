from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

root = Path(__file__).parent
telemetry_file = root / "q-vercel-latency.json"

@app.post("/api/telemetry")
async def telemetry_endpoint(request: Request):
    try:
        body = await request.json()
        regions = body.get("regions")
        threshold = body.get("threshold_ms")

        if not regions or threshold is None:
            raise HTTPException(status_code=400, detail="Missing keys: regions or threshold_ms")

        data = pd.read_json(telemetry_file)
        result = {}

        for region in regions:
            region_data = data[data["region"] == region]
            avg_latency = region_data["latency_ms"].mean()
            p95_latency = region_data["latency_ms"].quantile(0.95)
            avg_uptime = region_data["uptime"].mean()
            breaches = (region_data["latency_ms"] > threshold).sum()

            result[region] = {
                "avg_latency": round(avg_latency, 2) if pd.notnull(avg_latency) else None,
                "p95_latency": round(p95_latency, 2) if pd.notnull(p95_latency) else None,
                "avg_uptime": round(avg_uptime, 2) if pd.notnull(avg_uptime) else None,
                "breaches": int(breaches)
            }

        return JSONResponse(content=result)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
