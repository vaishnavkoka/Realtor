from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import asyncio
import logging
import sys
import os
from datetime import datetime
import traceback

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all agents. A failure here means no query can ever be answered, so stop
# rather than serving a backend that silently returns nothing.
try:
    from agents.langgraph_orchestrator import LangGraphRealEstateOrchestrator
    from agents.query_router import QueryRouterAgent
    from agents.structured_data_agent import StructuredDataAgent
    from agents.rag_agent import RAGAgent
    from agents.web_research_agent import WebResearchAgent
    from agents.report_generation_agent import ReportGenerationAgent
    from agents.renovation_estimation_agent import RenovationEstimationAgent
    from agents.planner_agent import PlannerAgent
    from agents.memory_enhanced_planner import MemoryEnhancedPlannerAgent
    from components.memory_component import MemoryComponent
except ImportError as e:
    logger.error(f"Failed to import agents: {e}")
    logger.error(
        "The environment is incomplete. Recreate it with "
        "'conda env create -n realtor-ai-env --file requirements.yml' and activate it."
    )
    raise

# Models
class QueryRequest(BaseModel):
    query: str

class PropertyResponse(BaseModel):
    success: bool
    properties: List[Dict[str, Any]]
    response_text: str
    agents_used: List[str]
    execution_time: float
    agent_details: Dict[str, Any] = {}
    error_details: Optional[str] = None

def validate_query_relevance_backend(query: str):
    """Backend validation for query relevance to real estate domain
    
    Only reject obvious out-of-context queries. Accept anything that could be real-estate related.
    
    Returns:
        (is_valid, message): Tuple of validity and message/reason
    """
    query_lower = query.lower().strip()
    
    # ONLY reject obvious out-of-scope queries with non-realtor keywords
    obvious_out_of_scope_patterns = [
        "tell me a joke", "what is your name", "who are you",
        "what is the weather", "current weather", "will it rain",
        "football match", "cricket score", "movie review",
        "book recommendation", "novel summary", "recipe for",
        "how to cook", "python code", "java programming",
        "solve this equation", "math problem", "coronavirus",
        "covid vaccine", "doctor appointment", "hospital location"
    ]
    
    # Check if query matches obvious out-of-scope patterns
    for pattern in obvious_out_of_scope_patterns:
        if pattern in query_lower:
            return False, pattern
    
    # Otherwise, accept the query - let agents decide if it's real estate related
    # This allows queries like:
    # - "did you go outside of my budget, while my budget is 200000?" (has budget keyword)
    # - "properties near XYZ location" (has location)
    # - "3 BHK with 2 parking" (has features)
    # - Any query mentioning cities, prices, property features, etc.
    return True, "Valid query"

# Global variables for orchestrator and agents
orchestrator = None
all_agents = {}
initialization_status = {
    "initialized": False,
    "in_progress": False,
    "progress": 0,
    "current_step": "Not started",
    "error": None,
    "total_steps": 11,
    "completed_steps": []
}

async def initialize_agents_background():
    """Initialize agents in background to avoid blocking"""
    global orchestrator, all_agents, initialization_status
    
    try:
        initialization_status["in_progress"] = True
        initialization_status["initialized"] = False
        
        logger.info("🚀 Starting async agent initialization...")
        
        # Step 1: Memory Component
        initialization_status["current_step"] = "Initializing Memory Component"
        initialization_status["progress"] = 1
        logger.info("1️⃣  Memory Component...")
        memory_component = MemoryComponent()
        all_agents["memory_component"] = memory_component
        initialization_status["completed_steps"].append("memory_component")
        
        # Step 2: Query Router Agent
        initialization_status["current_step"] = "Initializing Query Router Agent"
        initialization_status["progress"] = 2
        logger.info("2️⃣  Query Router Agent...")
        query_router = QueryRouterAgent()
        all_agents["query_router"] = query_router
        initialization_status["completed_steps"].append("query_router")
        
        # Step 3: Structured Data Agent
        initialization_status["current_step"] = "Initializing Structured Data Agent"
        initialization_status["progress"] = 3
        logger.info("3️⃣  Structured Data Agent...")
        structured_agent = StructuredDataAgent()
        all_agents["structured_data"] = structured_agent
        initialization_status["completed_steps"].append("structured_data")
        
        # Step 4: RAG Agent
        initialization_status["current_step"] = "Initializing RAG Agent"
        initialization_status["progress"] = 4
        logger.info("4️⃣  RAG Agent...")
        try:
            rag_agent = RAGAgent()
            all_agents["rag"] = rag_agent
            initialization_status["completed_steps"].append("rag")
        except ImportError as e:
            logger.warning(f"⚠️  RAG Agent skipped due to dependency issue: {e}")
            logger.warning("   System will continue without semantic search capabilities")
        except Exception as e:
            logger.warning(f"⚠️  RAG Agent initialization failed: {e}")
        
        # Step 5: Web Research Agent
        initialization_status["current_step"] = "Initializing Web Research Agent"
        initialization_status["progress"] = 5
        logger.info("5️⃣  Web Research Agent...")
        web_research_agent = WebResearchAgent()
        all_agents["web_research"] = web_research_agent
        initialization_status["completed_steps"].append("web_research")
        
        # Step 6: Report Generation Agent
        initialization_status["current_step"] = "Initializing Report Generation Agent"
        initialization_status["progress"] = 6
        logger.info("6️⃣  Report Generation Agent...")
        report_agent = ReportGenerationAgent()
        all_agents["report_generation"] = report_agent
        initialization_status["completed_steps"].append("report_generation")
        
        # Step 7: Renovation Estimation Agent
        initialization_status["current_step"] = "Initializing Renovation Estimation Agent"
        initialization_status["progress"] = 7
        logger.info("7️⃣  Renovation Estimation Agent...")
        renovation_agent = RenovationEstimationAgent()
        all_agents["renovation_estimation"] = renovation_agent
        initialization_status["completed_steps"].append("renovation_estimation")
        
        # Step 8: Planner Agent
        initialization_status["current_step"] = "Initializing Planner Agent"
        initialization_status["progress"] = 8
        logger.info("8️⃣  Planner Agent...")
        try:
            planner_agent = PlannerAgent()
            all_agents["planner"] = planner_agent
            initialization_status["completed_steps"].append("planner")
        except ImportError as e:
            logger.warning(f"⚠️  Planner Agent skipped (requires RAG): {e}")
        except Exception as e:
            logger.warning(f"⚠️  Planner Agent initialization failed: {e}")
        
        # Step 9: Memory Enhanced Planner Agent
        initialization_status["current_step"] = "Initializing Memory Enhanced Planner Agent"
        initialization_status["progress"] = 9
        logger.info("9️⃣  Memory Enhanced Planner Agent...")
        memory_planner = MemoryEnhancedPlannerAgent()
        all_agents["memory_enhanced_planner"] = memory_planner
        initialization_status["completed_steps"].append("memory_enhanced_planner")
        
        logger.info(f"✅ All {len(all_agents)} individual agents initialized!")
        
        # Step 10: LangGraph Orchestrator
        initialization_status["current_step"] = "Initializing LangGraph Orchestrator"
        initialization_status["progress"] = 10
        logger.info("🔟  LangGraph Orchestrator...")
        orchestrator = LangGraphRealEstateOrchestrator()
        initialization_status["completed_steps"].append("orchestrator")
        
        logger.info("✅ LangGraph Orchestrator initialized!")
        
        # Step 11: System ready
        initialization_status["current_step"] = "System ready"
        initialization_status["progress"] = 11
        initialization_status["initialized"] = True
        initialization_status["in_progress"] = False
        
        logger.info(f"🎉 SYSTEM FULLY INITIALIZED - {len(all_agents)} agents + orchestrator ready!")
        logger.info(f"Available agents: {', '.join(all_agents.keys())}")
        
    except Exception as e:
        logger.error(f"❌ Agent initialization failed: {e}", exc_info=True)
        initialization_status["error"] = str(e)
        initialization_status["in_progress"] = False
        traceback.print_exc()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan - start background initialization"""
    global orchestrator, all_agents
    
    try:
        logger.info("⏳ Backend starting - agents initializing in background...")
        logger.info("⏳ Server is ready for requests while agents initialize...")
        
        # Start agent initialization in background - DON'T WAIT FOR IT
        asyncio.create_task(initialize_agents_background())
        
    except Exception as e:
        logger.error(f"Lifespan startup error: {e}")
        traceback.print_exc()
        
    yield
    
    # Cleanup on shutdown
    logger.info("🔄 Shutting down all agents and orchestrator...")
    all_agents.clear()

app = FastAPI(
    title="Real Estate AI Search Engine",
    description="Multi-agent property search system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search", response_model=PropertyResponse)
async def search_properties(request: QueryRequest):
    """Main property search using LangGraph Orchestrator with improved error handling"""
    start_time = datetime.now()
    
    try:
        query = request.query.strip()
        logger.info(f"🔍 Processing query: {query}")
        
        if not query:
            logger.warning("Empty query received")
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Validate query relevance to real estate domain
        is_valid, validation_message = validate_query_relevance_backend(query)
        if not is_valid:
            logger.warning(f"❌ Out-of-scope query received: {query}")
            return PropertyResponse(
                success=False,
                properties=[],
                response_text=f"I'm a Real Estate AI Assistant specialized in property searches, market analysis, and renovation cost estimation. Your query about '{validation_message}' is outside my scope. Please ask about real estate related topics.",
                agents_used=[],
                execution_time=(datetime.now() - start_time).total_seconds(),
                agent_details={},
                error_details=f"Out-of-scope query: {validation_message}"
            )
        
        # Use LangGraph Orchestrator - it handles all agent routing automatically
        if not orchestrator:
            logger.error("Orchestrator not initialized")
            raise HTTPException(status_code=503, detail="Orchestrator not available - agents may still be initializing. Please wait 10-30 seconds on first startup.")
        
        logger.info("🤖 Using LangGraph Orchestrator (handles all agents)")
        
        # Call orchestrator - it will route to appropriate agents automatically
        try:
            result = await orchestrator.process_query(query, user_id="api_user")
        except asyncio.TimeoutError:
            logger.error("Orchestrator timed out")
            raise HTTPException(status_code=504, detail="Orchestrator processing timed out - query may be too complex")
        except Exception as orchestrator_error:
            logger.error(f"Orchestrator error: {orchestrator_error}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Orchestrator error: {str(orchestrator_error)}")
        
        # Extract results from orchestrator with detailed logging
        try:
            properties = extract_properties_from_orchestrator_result(result)
        except Exception as e:
            logger.error(f"Error extracting properties: {e}")
            properties = []
        
        # Better agent tracking
        agents_used = []
        agent_details = result.get("agent_results", {})
        
        # Track which agents actually executed
        for agent_name, agent_result in agent_details.items():
            if agent_result and agent_result.get("success", False):
                agents_used.append(agent_name)
        
        # Also check active_agents if available
        if result.get("active_agents"):
            agents_used.extend(result.get("active_agents", []))
        
        # Remove duplicates
        agents_used = list(set(agents_used))
        
        logger.info(f"📊 Agents executed: {agents_used}")
        logger.info(f"📊 Agent results: {list(agent_details.keys())}")
        
        # Generate response
        try:
            response_text = result.get("final_response", generate_response_text(properties, query, "orchestrator"))
        except Exception as e:
            logger.warning(f"Error generating response text: {e}")
            response_text = f"Found {len(properties)} properties matching your query"
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Orchestrator completed: {len(properties)} results, agents: {agents_used}, time: {execution_time:.2f}s")
        
        return PropertyResponse(
            success=True,
            properties=properties,
            response_text=response_text,
            agents_used=agents_used,
            execution_time=execution_time,
            agent_details=agent_details
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except asyncio.TimeoutError:
        logger.error("Search operation timed out")
        execution_time = (datetime.now() - start_time).total_seconds()
        return PropertyResponse(
            success=False,
            properties=[],
            response_text="Search timed out - the backend took too long to process. Please try a simpler query.",
            agents_used=[],
            execution_time=execution_time,
            agent_details={}
        )
    
    except Exception as e:
        logger.error(f"❌ Search failed: {e}", exc_info=True)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        error_msg = str(e)
        if "database" in error_msg.lower():
            error_msg = "Database error - check if realestate.db is properly initialized"
        elif "timeout" in error_msg.lower():
            error_msg = "Operation timed out - try a simpler query"
        elif "import" in error_msg.lower():
            error_msg = "Module import error - check dependencies are installed"
        
        return PropertyResponse(
            success=False,
            properties=[],
            response_text=f"Search failed: {error_msg}. Please try again.",
            agents_used=[],
            execution_time=execution_time,
            agent_details={},
            error_details=str(e)
        )

@app.post("/renovation-estimate")
async def get_renovation_estimate(request: dict):
    """Dedicated renovation estimation endpoint using orchestrator"""
    try:
        # Format as renovation query for orchestrator
        query = f"Estimate renovation cost for {request.get('bedrooms', 2)}BHK {request.get('property_type', 'apartment')} of {request.get('size_sqft', 1200)} sqft with {request.get('level', 'standard')} quality"
        
        result = await orchestrator.process_query(query, user_id="api_user")
        
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/agents/status")
async def agents_status():
    """Check orchestrator and individual agent status"""
    global all_agents, orchestrator
    
    if orchestrator and all_agents:
        # Check each individual agent status
        agent_statuses = {}
        
        for agent_name, agent_instance in all_agents.items():
            try:
                # Check if agent is properly initialized
                if agent_instance:
                    agent_statuses[agent_name] = "✅ Available"
                else:
                    agent_statuses[agent_name] = "❌ Not Available"
            except:
                agent_statuses[agent_name] = "❌ Error"
        
        return {
            "orchestrator": "✅ Available",
            "agents": agent_statuses,
            "total_agents": len(agent_statuses),
            "active_agents": len([s for s in agent_statuses.values() if "✅" in s]),
            "agent_details": {
                "query_router": "Intent detection and routing",
                "structured_data": "Database search and filtering", 
                "rag": "Semantic search and knowledge retrieval",
                "web_research": "Real-time market research",
                "report_generation": "Reports and analysis generation",
                "renovation_estimation": "Cost estimation and calculations",
                "planner": "Task planning and coordination",
                "memory_enhanced_planner": "Advanced planning with memory",
                "memory_component": "Session and user memory management"
            }
        }
    else:
        return {
            "orchestrator": "❌ Not Available",
            "agents": {},
            "total_agents": 0,
            "active_agents": 0,
            "error": "Orchestrator or agents not initialized"
        }
@app.get("/agents/list")
async def list_agents():
    """List all available agents with details"""
    global all_agents
    
    agent_list = []
    for agent_name, agent_instance in all_agents.items():
        agent_info = {
            "name": agent_name,
            "status": "✅ Available" if agent_instance else "❌ Not Available",
            "type": type(agent_instance).__name__ if agent_instance else "Unknown",
            "description": get_agent_description(agent_name)
        }
        agent_list.append(agent_info)
    
    return {
        "total_agents": len(agent_list),
        "agents": agent_list,
        "orchestrator_available": bool(orchestrator)
    }

@app.post("/agents/{agent_name}/query")
async def query_individual_agent(agent_name: str, request: QueryRequest):
    """Query a specific agent directly"""
    global all_agents
    
    if agent_name not in all_agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    agent = all_agents[agent_name]
    if not agent:
        raise HTTPException(status_code=500, detail=f"Agent '{agent_name}' not available")
    
    try:
        query = request.query
        logger.info(f"🎯 Direct query to {agent_name}: {query}")
        
        # Handle different agent types
        if agent_name == "query_router":
            result = agent.route_query(query)
        elif agent_name == "structured_data":
            result = agent.search_properties({"query": query})
        elif agent_name == "rag":
            result = agent.semantic_search({"query": query})
        elif agent_name == "web_research":
            result = await agent.research_query(query)
        elif agent_name == "report_generation":
            result = agent.generate_report({"query": query, "report_type": "custom"})
        elif agent_name == "renovation_estimation":
            result = agent.estimate_renovation_cost()
        elif agent_name == "planner":
            result = await agent.create_plan(query)
        elif agent_name == "memory_enhanced_planner":
            result = await agent.plan_and_execute(query, "direct_user")
        else:
            result = {"error": f"Direct query not supported for {agent_name}"}
        
        return {
            "success": True,
            "agent_name": agent_name,
            "query": query,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Direct agent query failed for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Agent query failed: {str(e)}")

def get_agent_description(agent_name: str) -> str:
    """Get description for each agent"""
    descriptions = {
        "query_router": "Analyzes user queries and routes them to appropriate agents",
        "structured_data": "Searches property database using SQL queries and filters",
        "rag": "Performs semantic search using vector embeddings and knowledge retrieval",
        "web_research": "Conducts real-time web research for market data and trends",
        "report_generation": "Creates comprehensive reports, charts, and PDF documents",
        "renovation_estimation": "Calculates renovation costs and provides estimates",
        "planner": "Creates execution plans and coordinates multi-step tasks",
        "memory_enhanced_planner": "Advanced planning with user memory and preferences",
        "memory_component": "Manages user sessions, preferences, and conversation history"
    }
    return descriptions.get(agent_name, "Specialized AI agent for real estate tasks")

@app.post("/generate-report")
async def generate_report(request: dict):
    """Generate detailed reports with charts and PDFs"""
    try:
        report_type = request.get("report_type", "market_analysis")
        location = request.get("location", "")
        include_charts = request.get("include_charts", True)
        include_pdf = request.get("include_pdf", True)
        
        # Create enhanced query for report generation
        query = f"generate comprehensive {report_type} report for {location}"
        if include_charts:
            query += " with charts and visualizations"
        if include_pdf:
            query += " in PDF format"
        
        logger.info(f"📊 Generating report: {report_type} for {location}")
        
        # Use orchestrator for report generation
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not available")
        
        result = await orchestrator.process_query(query, user_id="report_user")
        
        # Extract and format results
        properties = extract_properties_from_orchestrator_result(result)
        agents_used = []
        agent_details = result.get("agent_results", {})
        
        for agent_name, agent_result in agent_details.items():
            if agent_result and agent_result.get("success", False):
                agents_used.append(agent_name)
        
        # Generate report response
        response_text = result.get("final_response", "Report generated successfully")
        
        # Add chart data (sample data for now)
        chart_data = generate_sample_chart_data(location)
        
        # Generate PDF data (base64 encoded)
        pdf_data = None
        if include_pdf:
            pdf_data = generate_pdf_base64(report_type, location, response_text)
        
        return {
            "success": True,
            "report_type": report_type,
            "location": location,
            "response_text": response_text,
            "agents_used": agents_used,
            "properties": properties,
            "chart_data": chart_data if include_charts else None,
            "pdf_data": pdf_data if include_pdf else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@app.post("/search-history-analysis")
async def search_history_analysis():
    """Analyze search history and generate insights"""
    try:
        # In a real implementation, this would fetch from database
        # For now, return sample analysis
        
        analysis_data = {
            "total_searches": 127,
            "unique_queries": 89,
            "success_rate": 0.85,
            "popular_locations": [
                {"location": "Mumbai", "count": 45},
                {"location": "Bangalore", "count": 32},
                {"location": "Delhi", "count": 28},
                {"location": "Pune", "count": 22}
            ],
            "property_types": [
                {"type": "2BHK", "count": 56},
                {"type": "3BHK", "count": 41},
                {"type": "1BHK", "count": 23},
                {"type": "4BHK", "count": 7}
            ],
            "budget_distribution": [
                {"range": "<50L", "count": 25},
                {"range": "50-100L", "count": 48},
                {"range": "100-150L", "count": 35},
                {"range": ">150L", "count": 19}
            ],
            "search_trends": generate_search_trends_data(),
            "insights": [
                "Most searches happen between 10 AM - 2 PM",
                "2BHK apartments are the most searched property type",
                "Mumbai and Bangalore account for 60% of all searches",
                "Average budget has increased by 12% this quarter"
            ]
        }
        
        return {
            "success": True,
            "analysis": analysis_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Search history analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

def generate_sample_chart_data(location=""):
    """Generate sample chart data"""
    return {
        "price_trends": {
            "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "prices": [85, 87, 89, 88, 90, 92]
        },
        "property_distribution": {
            "types": ["2BHK", "3BHK", "1BHK", "4BHK"],
            "counts": [45, 35, 15, 5]
        },
        "location_comparison": {
            "locations": ["Mumbai", "Bangalore", "Delhi", "Pune"],
            "avg_prices": [95, 75, 85, 65],
            "growth_rates": [8, 12, 6, 15]
        }
    }

def generate_search_trends_data():
    """Generate search trends data"""
    from datetime import datetime, timedelta
    import random
    
    # Generate last 30 days of data
    dates = []
    searches = []
    
    for i in range(30):
        date = datetime.now() - timedelta(days=i)
        dates.insert(0, date.strftime('%Y-%m-%d'))
        searches.insert(0, random.randint(15, 45))
    
    return {
        "dates": dates,
        "searches": searches
    }

def generate_pdf_base64(report_type, location, content):
    """Generate PDF report as base64 string"""
    try:
        # Simple PDF content (in real implementation, use reportlab)
        pdf_content = f"""
PDF Report: {report_type}
Location: {location}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{content}

This is a sample PDF report. In a full implementation, this would include:
- Professional formatting
- Charts and graphs
- Property listings with images
- Market analysis
- Investment recommendations
        """
        
        import base64
        return base64.b64encode(pdf_content.encode()).decode()
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return None

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_available": orchestrator is not None,
        "managed_agents": 6 if orchestrator else 0,
        "initialization": initialization_status
    }

@app.get("/init-status")
async def get_initialization_status():
    """Get detailed initialization status"""
    return {
        "status": initialization_status,
        "timestamp": datetime.now().isoformat(),
        "ready": initialization_status["initialized"]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🏠 Real Estate AI Search Engine",
        "status": "running" if initialization_status["initialized"] else "initializing",
        "orchestrator_available": orchestrator is not None,
        "managed_agents": len(all_agents),
        "docs": "/docs",
        "initialization": initialization_status
    }

# Helper Functions
def extract_properties_from_orchestrator_result(result: Dict) -> List[Dict]:
    """Extract properties from orchestrator result with support for all agent types"""
    properties = []
    
    # Handle both old and new result formats
    if "synthesized_result" in result:
        # New format: synthesized_result contains agent results
        agent_results = result.get("synthesized_result", {}).get("supporting_data", {})
        primary_result = result.get("synthesized_result", {}).get("primary_result", {})
    else:
        # Old/direct format: agent_results at top level
        agent_results = result.get("agent_results", {})
        primary_result = {}
    
    # Track seen property IDs to avoid duplicates
    seen_ids = set()
    
    # Step 1: Extract from property search agents (highest priority)
    search_agents = ["structured_data", "rag", "web_research"]
    for agent_name in search_agents:
        if agent_name in agent_results:
            agent_result = agent_results[agent_name]
            if isinstance(agent_result, dict):
                props = agent_result.get("properties", [])
                if isinstance(props, list):
                    for prop in props:
                        if isinstance(prop, dict):
                            prop_id = prop.get("property_id") or prop.get("id")
                            if prop_id and prop_id not in seen_ids:
                                seen_ids.add(prop_id)
                                prop["_source_agent"] = agent_name
                                properties.append(prop)
    
    # Step 2: Add properties from primary result if not already included
    if primary_result and isinstance(primary_result, dict):
        props = primary_result.get("properties", [])
        if isinstance(props, list):
            for prop in props:
                if isinstance(prop, dict):
                    prop_id = prop.get("property_id") or prop.get("id")
                    if prop_id and prop_id not in seen_ids:
                        seen_ids.add(prop_id)
                        prop["_source_agent"] = "primary_result"
                        properties.append(prop)
    
    # Step 3: Enhance properties with specialized agent data (add metadata, don't replace)
    if "renovation_estimation" in agent_results:
        renovation_data = agent_results["renovation_estimation"]
        if isinstance(renovation_data, dict) and renovation_data.get("success"):
            for prop in properties:
                if "renovation_details" not in prop:
                    prop["renovation_details"] = {
                        "total_cost": renovation_data.get("total_cost", 0),
                        "cost_per_sqft": renovation_data.get("cost_per_sqft", 0),
                        "timeline_weeks": renovation_data.get("timeline_weeks", 0),
                        "room_breakdown": renovation_data.get("room_breakdown", {}),
                        "category_breakdown": renovation_data.get("category_breakdown", {})
                    }
    
    return properties[:20] if properties else []

def generate_response_text(properties: List[Dict], query: str, method: str) -> str:
    """Generate user-friendly response text"""
    if not properties:
        return f"🔍 No properties found for '{query}'. The AI agents searched our database but couldn't find matching properties. Try different keywords or broader search terms."
    
    count = len(properties)
    
    # Check if this is a renovation estimate
    if properties and properties[0].get("source") == "Renovation_Agent":
        estimate = properties[0]
        cost = estimate.get("price", 0)
        return f"🔨 Renovation Cost Estimate for '{query}': ₹{cost:,}\n\nThis estimate was calculated by our AI Renovation Agent based on your requirements."
    
    # Regular property search results
    response = f"🏠 Found {count} propert{'y' if count == 1 else 'ies'} matching '{query}'\n\n"
    response += f"🤖 Search performed by: LangGraph Multi-Agent System\n\n"
    
    # Show top 3 properties
    for i, prop in enumerate(properties[:3], 1):
        title = prop.get("title", "Property")
        price = prop.get("price", 0)
        location = prop.get("location", "Location not specified")
        
        response += f"**{i}. {title}**\n"
        response += f"📍 {location}\n"
        if price > 0:
            response += f"💰 ₹{price:,}\n"
        
        if prop.get("property_size_sqft"):
            response += f"📐 {prop['property_size_sqft']} sqft\n"
        if prop.get("num_rooms"):
            response += f"🏠 {prop['num_rooms']} rooms\n"
        
        response += "\n"
    
    if count > 3:
        response += f"... and {count - 3} more properties available.\n"
    
    return response