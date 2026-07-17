# 🤖 Multi-Agent Architecture - Detailed Guide

## Overview
The ReAltoR Search Engine uses **LangGraph** to orchestrate a sophisticated multi-agent system. Each agent specializes in specific tasks and works together to provide comprehensive real estate search and analysis capabilities.

---

## 🏗️ Agent Architecture

### 1. Query Router Agent
**File**: `agents/query_router.py`  
**Purpose**: Intelligent query routing and intent classification

**Responsibilities**:
- Parse incoming user queries
- Classify query intent (search, analysis, estimation, research)
- Route queries to appropriate agents
- Handle multi-intent queries requiring multiple agents
- Maintain conversation context

**Input**:
```python
{
    "query": "Find 2BHK apartments under 50 lakhs near downtown",
    "conversation_history": [...]
}
```

**Output**:
```python
{
    "intent": "property_search",
    "confidence": 0.95,
    "required_agents": ["structured_data_agent", "rag_agent"],
    "parameters": {
        "bhk": 2,
        "max_price": 5000000,
        "location": "downtown"
    }
}
```

**Key Features**:
- Intent classification using LLM
- Parameter extraction from natural language
- Multi-agent requirement detection
- Confidence scoring

---

### 2. Structured Data Agent
**File**: `agents/structured_data_agent.py`  
**Purpose**: Database queries and property filtering

**Responsibilities**:
- Query SQLite database for properties
- Filter by structured criteria (price, location, BHK, etc.)
- Join related data (amenities, reviews, etc.)
- Return ranked results
- Handle complex queries with multiple conditions

**Input**:
```python
{
    "filters": {
        "bhk": 2,
        "min_price": 3000000,
        "max_price": 5000000,
        "location": "downtown",
        "amenities": ["gym", "pool"]
    },
    "sort_by": "price",
    "limit": 10
}
```

**Output**:
```python
{
    "results": [
        {
            "id": 1,
            "name": "Luxury Apartment",
            "price": 4500000,
            "bhk": 2,
            "location": "downtown",
            "rating": 4.5
        },
        ...
    ],
    "total_count": 23
}
```

**Key Features**:
- SQLAlchemy ORM for safe queries
- Complex filter combinations
- Pagination support
- Result ranking and sorting

---

### 3. RAG Agent
**File**: `agents/rag_agent.py`  
**Purpose**: Semantic search and knowledge retrieval

**Responsibilities**:
- Perform semantic search using embeddings
- Retrieve relevant documents from vector store
- Answer questions about properties and market
- Handle context-aware queries
- Synthesize information from multiple sources

**Input**:
```python
{
    "query": "What are the best neighborhoods for young professionals?",
    "top_k": 5,
    "include_metadata": True
}
```

**Output**:
```python
{
    "results": [
        {
            "content": "Downtown area is perfect for young professionals...",
            "source": "market_report_2024",
            "relevance_score": 0.92,
            "metadata": {"region": "downtown", "type": "neighborhood"}
        },
        ...
    ],
    "summary": "Downtown and tech hub areas are best for young professionals..."
}
```

**Key Features**:
- FAISS vector similarity search
- HuggingFace embeddings
- Relevance scoring
- Document metadata retrieval

---

### 4. Web Research Agent
**File**: `agents/web_research_agent.py`  
**Purpose**: Real-time market research and trends

**Responsibilities**:
- Search current web for real estate market data
- Gather market trends and statistics
- Collect competitor/comparable properties
- Aggregate price trends
- Find recent market news

**Input**:
```python
{
    "research_query": "Real estate prices in downtown 2024",
    "max_results": 10,
    "date_range": "last_3_months"
}
```

**Output**:
```python
{
    "research_results": [
        {
            "title": "Real Estate Market Report Q1 2024",
            "link": "...",
            "snippet": "Market prices increased by 5% in Q1...",
            "date": "2024-04-01"
        },
        ...
    ],
    "market_summary": "Market trends show steady growth..."
}
```

**Key Features**:
- Serper API integration for search
- Tavily research API for deep analysis
- Result aggregation and summarization
- Trend extraction

---

### 5. Renovation Estimation Agent
**File**: `agents/renovation_estimation_agent.py`  
**Purpose**: Calculate renovation costs by property type

**Responsibilities**:
- Estimate renovation costs based on BHK and type
- Provide cost breakdown by category
- Handle different renovation types (full, partial, cosmetic)
- Consider location and quality factors
- Generate renovation reports

**Input**:
```python
{
    "property_id": 1,
    "bhk": 2,
    "renovation_type": "full",
    "quality_level": "premium",
    "location": "downtown"
}
```

**Output**:
```python
{
    "property_id": 1,
    "total_estimated_cost": 800000,
    "breakdown": {
        "flooring": 150000,
        "walls_paint": 80000,
        "kitchen": 200000,
        "bathroom": 150000,
        "electrical": 100000,
        "plumbing": 100000,
        "miscellaneous": 20000
    },
    "labor_cost": 100000,
    "material_cost": 700000,
    "duration_days": 45
}
```

**Key Features**:
- BHK-wise cost calculations
- Quality level adjustments
- Location-based pricing
- Detailed cost breakdown

---

### 6. Report Generation Agent
**File**: `agents/report_generation_agent.py`  
**Purpose**: Synthesize findings into comprehensive reports

**Responsibilities**:
- Aggregate results from other agents
- Synthesize information into coherent reports
- Apply user preferences to findings
- Generate market analysis reports
- Create property recommendation reports
- Format reports for PDF/email

**Input**:
```python
{
    "agent_results": {
        "structured_data": [...],
        "rag_results": [...],
        "web_research": [...],
        "renovations": [...]
    },
    "user_preferences": {
        "report_type": "comprehensive",
        "format": "pdf",
        "language": "english"
    }
}
```

**Output**:
```python
{
    "report": {
        "title": "Real Estate Market Analysis Report",
        "created_at": "2024-04-10",
        "executive_summary": "...",
        "detailed_analysis": {
            "market_overview": "...",
            "properties": [...],
            "recommendations": [...]
        },
        "file_path": "reports/report_2024_04_10.pdf"
    }
}
```

**Key Features**:
- Multi-format output (PDF, HTML, JSON)
- User preference application
- Data visualization
- Professional formatting

---

### 7. LangGraph Orchestrator
**File**: `agents/langgraph_orchestrator.py`  
**Purpose**: Coordinate multi-agent workflow

**Responsibilities**:
- Create and manage graph workflow
- Route between agents based on intent
- Handle parallel vs sequential execution
- Manage state across agent calls
- Error handling and fallbacks
- Result aggregation

**Workflow Types**:

#### Simple Search Workflow
```
User Query → QueryRouter → StructuredDataAgent → Report Generator
```

#### Complex Analysis Workflow
```
User Query → QueryRouter ─┬→ StructuredDataAgent ─┐
                          ├→ RAGAgent            ├→ Report Generator
                          ├→ WebResearchAgent    ┤
                          └→ RenovationAgent ────┘
```

#### Sequential Workflow
```
User Query → QueryRouter → StructuredDataAgent →
    RenovationAgent (for selected property) → Report Generator
```

**Key Features**:
- StateGraph-based orchestration
- Conditional routing
- Error recovery
- Result caching

---

## 📊 State Management

### Global State Schema
```python
{
    "query": str,                    # Original user query
    "intent": str,                   # Detected query intent
    "conversation_context": List,    # Message history
    "agent_results": Dict,           # Results from executed agents
    "current_agent": str,            # Currently executing agent
    "execution_path": List,          # Path of agent executions
    "errors": List,                  # Any errors encountered
    "timestamp": datetime            # Query timestamp
}
```

### Agent Result Schema
```python
{
    "agent_name": str,
    "status": "success" | "error",
    "result": Any,
    "execution_time": float,
    "cache_hit": bool,
    "error_message": Optional[str]
}
```

---

## 🔄 Execution Patterns

### Pattern 1: Parallel Execution
**When**: Multiple independent agent calls
```python
# Structured data search + Web research can run in parallel
# They don't depend on each other

graph.add_node("parallel_research", execute_parallel_agents)
```

### Pattern 2: Sequential Execution
**When**: Output of one agent is input to another
```python
# StructuredDataAgent → RenovationAgent
# Must run sequentially (need property ID from first agent)

graph.add_edge("structured_data", "renovation_estimation")
```

### Pattern 3: Conditional Execution
**When**: Agent selection depends on query intent
```python
# If intent is "search" → StructuredDataAgent
# If intent is "research" → WebResearchAgent
# If intent is "analysis" → RAGAgent + WebResearchAgent

graph.add_conditional_edges("query_router", route_based_on_intent)
```

---

## 🛡️ Error Handling

### Agent-Level Error Handling
```python
class AgentResult:
    success: bool
    result: Optional[Any]
    error: Optional[str]
    fallback_executed: bool
    
    def use_fallback(self):
        # Load cached result or use default
```

### Workflow-Level Recovery
```
Agent Fails → Check for Fallback → Use Cached Result
         ↓ (if available)              ↓
      Use Default       → Continue Workflow
         ↓
      Log Error & Return Partial Results
```

---

## 🔌 API Integration Points

### LLM Integration
```python
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=GROQ_API_KEY
)
```

### Search APIs
- **Serper API**: Web search for real estate data
- **Tavily API**: Deep research and analysis

### Embedding Model
- **HuggingFace**: `sentence-transformers/all-MiniLM-L6-v2`

### Database
- **SQLite**: Structured property data
- **FAISS**: Vector similarity search

---

## ⚙️ Configuration

### Agent Settings (in `config/settings.py`)

```python
# Agent timeouts
AGENT_TIMEOUT = 30  # seconds

# Rate limiting
GROQ_RATE_LIMIT = 25000  # per day
SERPER_RATE_LIMIT = 100  # per minute

# Vector search parameters
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.5

# Database settings
DATABASE_URL = "sqlite:///realestate.db"
FAISS_INDEX_PATH = "data/faiss_index"
```

---

## 📈 Performance Optimization

### Caching Strategies
1. **Query Result Caching**: Cache structured queries (24 hours)
2. **Embedding Caching**: Cache vector DB queries (7 days)
3. **API Response Caching**: Cache external API calls (varies by API)

### Parallel Execution
```python
# Run independent agents in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    web_research_future = executor.submit(web_research_agent.run, query)
    rag_future = executor.submit(rag_agent.run, query)
    
    web_results = web_research_future.result()
    rag_results = rag_future.result()
```

### Rate Limiting
```python
rate_limiter = RateLimiter({
    "groq": 25000,     # per day
    "serper": 100,     # per minute
    "tavily": 50       # per day
})

@rate_limiter.limit("groq")
def call_groq_api():
    pass
```

---

## 🧪 Testing Individual Agents

### Testing StructuredDataAgent
```bash
python -m pytest agents/test_structured_data_agent.py
```

### Testing RAGAgent
```bash
python -m pytest agents/test_rag_agent.py -v
```

### Testing Full Workflow
```bash
python agents/langgraph_orchestrator.py --test --query "Find 2BHK apartments"
```

---

## 🔍 Debugging & Logging

### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# See all agent calls and results
logger = logging.getLogger("agents")
logger.setLevel(logging.DEBUG)
```

### Trace Workflow Execution
```bash
# Set environment variable
export LANGGRAPH_DEBUG=true

# Run your query
python backend.py
```

---

## 📚 Example Workflows

### Example 1: Simple Property Search
```
Query: "Find 2BHK apartments under 50 lakhs"

1. QueryRouter → Detects: property_search intent
2. StructuredDataAgent → Database query (filtered results)
3. ReportGenerator → Format and return results
```

### Example 2: Comprehensive Market Analysis
```
Query: "Give me comprehensive analysis of downtown real estate"

1. QueryRouter → Detects: market_analysis intent
2. Parallel:
   - StructuredDataAgent → Top properties in area
   - WebResearchAgent → Current market trends
   - RAGAgent → Historical data & insights
3. RenovationAgent → Cost estimation for properties
4. ReportGenerator → Comprehensive report

Result: PDF report with market overview, properties, trends, costs, recommendations
```

### Example 3: Investment Analysis
```
Query: "Which 2BHK properties have good ROI potential?"

1. QueryRouter → Property investment analysis
2. StructuredDataAgent → Find 2BHK properties
3. RenovationAgent → Estimate renovation costs
4. WebResearchAgent → Market appreciation trends
5. ReportGenerator → Calculate ROI scenarios

Result: Ranked properties with ROI projections
```

---

## 🎯 Next Steps for Implementation

1. **Test Individual Agents**: Start with basic agent functionality
2. **Validate Agent Integration**: Test agent-to-agent communication
3. **Setup LangGraph Workflow**: Create the orchestration graph
4. **Implement Error Handling**: Error recovery and fallbacks
5. **Add Caching Layer**: Optimize performance
6. **Build Frontend Integration**: Connect to Streamlit UI
7. **Load Testing**: Performance validation
8. **Deployment**: Production setup

---

**Document Version**: 1.0  
**Last Updated**: April 10, 2026  
**Status**: Implementation Guide - Active
