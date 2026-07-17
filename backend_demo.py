"""
Lightweight ReAltoR Backend - Simplified version for demonstration
Avoids complex ML dependencies while maintaining API structure
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request models
class SearchRequest(BaseModel):
    query: str
    address: str = None

class ReportRequest(BaseModel):
    property_id: str = "default"

app = FastAPI(
    title="Real Estate AI Search Engine - Demo",
    description="Lightweight demonstration backend",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Real Estate AI Search Engine - Demo",
        "version": "1.0.0",
        "agents_ready": {
            "query_router": True,
            "structured_data": True,
            "web_research": True,
            "report_generation": True,
            "renovation": True,
            "orchestrator": True
        },
        "initialization": {
            "initialized": True,
            "in_progress": False,
            "progress": 6,
            "total_steps": 6,
            "current_step": "System ready",
            "completed_steps": [
                "memory_component",
                "query_router",
                "structured_data",
                "web_research",
                "report_generation",
                "orchestrator"
            ]
        },
        "managed_agents": 6,
        "orchestrator_available": True,
        "note": "Demo backend - Full ML features available on production backend"
    }

# Search endpoint
@app.post("/search")
async def search(request: SearchRequest):
    """Simplified search endpoint - accepts JSON body"""
    query = request.query
    address = request.address
    logger.info(f"Search query: {query} in {address or 'any location'}")
    
    return {
        "success": True,
        "status": "success",
        "response_text": "Search completed successfully",
        "properties": [
            {
                "property_id": "demo_1",
                "id": "demo_1",
                "title": f"Beautiful Property in {address or 'Mumbai'}",
                "location": address or "123 Main St",
                "address": address or "123 Main St",
                "price": 450000,
                "property_size_sqft": 2000,
                "sqft": 2000,
                "num_rooms": 3,
                "beds": 3,
                "baths": 2,
                "market_analysis": "Strong market in this area",
                "recommendation": "Good investment opportunity"
            }
        ],
        "results": [
            {
                "property_id": "demo_1",
                "id": "demo_1",
                "title": f"Beautiful Property in {address or 'Mumbai'}",
                "location": address or "123 Main St",
                "address": address or "123 Main St",
                "price": 450000,
                "property_size_sqft": 2000,
                "sqft": 2000,
                "num_rooms": 3,
                "beds": 3,
                "baths": 2,
                "market_analysis": "Strong market in this area",
                "recommendation": "Good investment opportunity"
            }
        ],
        "agents_used": ["query_router", "structured_data", "web_research"],
        "execution_time": 1.5,
        "agent_details": {}
    }

# Memory endpoint
@app.get("/memory")
async def get_memory():
    """Get conversation memory"""
    return {
        "history": [],
        "context": {},
        "last_query": None
    }

# Status endpoint  
@app.get("/status")
async def get_status():
    """Get system status"""
    return {
        "backend_ready": True,
        "agents": {
            "query_router": {"status": "ready"},
            "structured_data": {"status": "ready"},
            "web_research": {"status": "ready"},
            "report_generation": {"status": "ready"},
            "renovation": {"status": "ready"}
        },
        "initialization_complete": True
    }

# Agents status endpoint (required by frontend)
@app.get("/agents/status")
async def get_agents_status():
    """Get agents status"""
    return {
        "total_agents": 6,
        "active_agents": 6,
        "agents": {
            "query_router": "ready",
            "structured_data": "ready",
            "web_research": "ready",
            "report_generation": "ready",
            "renovation": "ready",
            "orchestrator": "ready"
        }
    }

# Report endpoint
@app.post("/generate_report")
async def generate_report(request: ReportRequest):
    """Generate property report"""
    return {
        "report_id": request.property_id,
        "generated_at": datetime.utcnow().isoformat(),
        "property": {
            "address": "123 Main St",
            "price": 450000
        },
        "analysis": {
            "market": "Strong",
            "investment": "Recommended",
            "renovation_needed": False
        }
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Real Estate AI Search Engine - Demo Backend",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/search",
            "/memory",
            "/status",
            "/generate_report",
            "/docs"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Real Estate Search Engine Demo Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
