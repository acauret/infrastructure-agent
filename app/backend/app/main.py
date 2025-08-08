from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os

# Reuse the existing autogen entrypoint
from app.backend.app.autogen_agent_v2 import create_mcp_server_params, stream_task

app = FastAPI(title="Infrastructure Agent API")

# CORS for local dev / docker-compose
api_base = os.getenv("NEXT_PUBLIC_API_BASE", "http://localhost:8000")
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    prompt: str

@app.get("/health")
async def health():
    return {"status": "ok"}

async def stream_agent_output(prompt: str):
    # Stream real agent execution
    async for line in stream_task(prompt):
        yield line

@app.post("/run")
async def run(req: RunRequest):
    try:
        return StreamingResponse(stream_agent_output(req.prompt), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
