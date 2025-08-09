from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os

# Reuse the existing autogen entrypoint
from app.backend.app.autogen_agent_v2 import create_mcp_server_params, stream_task, check_mcp_servers, submit_user_input

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
    # Optional session id to continue a conversation (not required for one-shot)
    session: str | None = None

class InputRequest(BaseModel):
    session: str
    text: str

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
        # Stream as NDJSON for structured events
        return StreamingResponse(stream_agent_output(req.prompt), media_type="application/x-ndjson")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp-check")
async def mcp_check():
    try:
        results = await check_mcp_servers()
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/input")
async def input_to_session(req: InputRequest):
    ok = await submit_user_input(req.session, req.text)
    if not ok:
        raise HTTPException(status_code=404, detail="session not found")
    return {"status": "ok"}
