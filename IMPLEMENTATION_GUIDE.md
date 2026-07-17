# 🏠 ReAltoR Search Engine - Implementation Guide

**Project**: Multi-Agent Real Estate Search System with LangGraph  
**Location**: the repo root  
**Status**: ✅ Repository Cloned & Ready for Setup  

---

## 📋 Implementation Checklist

### Phase 1: Environment Setup
- [ ] **1.1** Install Conda environment from `requirements.yml`
- [ ] **1.2** Create `.env` file with API keys
- [ ] **1.3** Verify Python 3.11+ installation
- [ ] **1.4** Test import of core dependencies

### Phase 2: Data Configuration
- [ ] **2.1** Run `src/data_ingestion.py` to create SQLite database
- [ ] **2.2** Generate FAISS vector store for semantic search
- [ ] **2.3** Verify property data loaded (80+ records)
- [ ] **2.4** Check database schema and vector index

### Phase 3: Agent System Setup
- [ ] **3.1** Validate QueryRouter agent initialization
- [ ] **3.2** Test StructuredDataAgent (database queries)
- [ ] **3.3** Test RAGAgent (semantic search)
- [ ] **3.4** Test WebResearchAgent (market research)
- [ ] **3.5** Test RenovationEstimationAgent (cost calculations)
- [ ] **3.6** Test ReportGenerationAgent (report synthesis)
- [ ] **3.7** Verify LangGraphOrchestrator workflow

### Phase 4: Backend & API
- [ ] **4.1** Validate FastAPI server startup (`backend.py`)
- [ ] **4.2** Test API Gateway endpoints
- [ ] **4.3** Verify rate limiting functionality
- [ ] **4.4** Test error handling and fallbacks

### Phase 5: Frontend & UI
- [ ] **5.1** Launch Streamlit app (`frontend.py`)
- [ ] **5.2** Test property search functionality
- [ ] **5.3** Test report generation UI
- [ ] **5.4** Test user preference configuration

### Phase 6: End-to-End Testing
- [ ] **6.1** Execute multi-agent workflow for complex query
- [ ] **6.2** Verify all agents activate correctly
- [ ] **6.3** Test API rate limiting
- [ ] **6.4** Generate sample reports
- [ ] **6.5** Performance profiling

---

## 🚀 Quick Start Commands

```bash
# Navigate to project
cd /path/to/Realtor

# 1. Create Conda environment
conda env create -n realtor-ai-env --file requirements.yml
conda activate realtor-ai-env

# 2. Setup environment variables
cp .env.example .env
nano .env  # Add your API keys

# 3. Initialize data
python src/data_ingestion.py

# 4. Start backend API
python backend.py

# 5. In another terminal, start frontend
streamlit run frontend.py
```

---

## 📁 Project Structure

```
agentic_langgraph/
├── agents/                          # Multi-agent system
│   ├── langgraph_orchestrator.py   # Master orchestrator
│   ├── query_router.py             # Intent detection & routing
│   ├── structured_data_agent.py    # Database queries
│   ├── rag_agent.py                # Semantic search
│   ├── web_research_agent.py       # Market research
│   ├── report_generation_agent.py  # Report synthesis
│   └── renovation_estimation_agent.py # Cost calculations
│
├── backend.py                       # FastAPI server
├── frontend.py                      # Streamlit UI
├── api_gateway.py                  # Request routing & rate limiting
│
├── models/                          # LLM integrations
│   ├── llm_models.py               # LLM factory
│   └── rate_limiter.py             # Rate limiting implementation
│
├── config/                          # Configuration
│   ├── settings.py                 # App settings
│   └── rate_limiting.py            # Rate limits config
│
├── components/                      # Reusable components
│   └── memory_component.py         # Agent memory
│
├── src/                             # Core data modules
│   ├── data_ingestion.py           # Data setup & DB initialization
│   └── database_schema.py          # SQLAlchemy models
│
├── utils/                           # Utilities
│   └── rate_limiter.py             # Shared rate limiter
│
├── data/                            # Data storage
│   └── vector_store/               # FAISS indices
│
├── assets/                          # Static assets
│   ├── certificates/               # SSL certificates
│   └── Property_list.xlsx          # Sample data
│
└── requirements.yml                 # Conda environment spec
```

---

## 🤖 Multi-Agent System Overview

### Agent 1: QueryRouter
**Purpose**: Analyze user intent and route to appropriate agents  
**Input**: User query  
**Output**: Query intent classification & routing decision  

### Agent 2: StructuredDataAgent
**Purpose**: Search and filter properties from structured database  
**Input**: Property criteria (budget, location, size)  
**Output**: Matching properties from SQLite DB  

### Agent 3: RAGAgent
**Purpose**: Semantic search and knowledge retrieval  
**Input**: User query  
**Output**: Contextually relevant information from vector store  

### Agent 4: WebResearchAgent
**Purpose**: Real-time market research and trends  
**Input**: Market query parameters  
**Output**: Current market insights and trends  

### Agent 5: RenovationEstimationAgent
**Purpose**: Calculate renovation costs by BHK  
**Input**: Property BHK, renovation type  
**Output**: Cost breakdown and estimates  

### Agent 6: ReportGenerationAgent
**Purpose**: Synthesize findings into comprehensive reports  
**Input**: Results from other agents + user preferences  
**Output**: Formatted market/property reports  

### Orchestrator: LangGraphOrchestrator
**Purpose**: Coordinate multi-agent workflow  
**Features**:
- Parallel agent execution for independent tasks
- Sequential execution for dependent tasks
- Result aggregation and synthesis
- Error handling and fallback mechanisms
- State management across workflow steps

---

## 🔧 Configuration

### Environment Variables (.env)
```env
# API Keys (Required)
GROQ_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here
SERPER_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
COHERE_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///./realestate.db

# Vector Store
FAISS_INDEX_PATH=data/faiss_index

# Logging
LOG_LEVEL=INFO
DEBUG=true
```

### Rate Limiting Configuration
Default limits (configurable in `config/rate_limiting.py`):
- **Groq**: 25,000 requests/day
- **Serper**: 2,400 searches/month
- **Tavily**: 950 searches/month

---

## 📊 API Endpoints (FastAPI Backend)

### Main Endpoints
- `POST /search` - Execute property search
- `POST /query` - Process multi-agent query
- `GET /properties/{id}` - Fetch property details
- `POST /generate-report` - Generate market report
- `POST /estimate-renovation` - Estimate renovation costs
- `GET /health` - Server health check

---

## 🎯 Implementation Phases

### Week 1: Setup & Initial Testing
- Environment configuration
- Data initialization
- Individual agent testing
- Backend API validation

### Week 2: Integration & Frontend
- Multi-agent workflow testing
- Frontend UI development
- End-to-end testing
- Performance optimization

### Week 3: Advanced Features
- Custom report generation
- Market analysis enhancements
- Caching strategies
- Deployment preparation

---

## 📝 Key Implementation Notes

### Dependencies
- **LangGraph**: Multi-agent orchestration framework
- **LangChain**: LLM integration and chains
- **FastAPI**: Backend API server
- **Streamlit**: Frontend UI
- **FAISS**: Vector similarity search
- **SQLAlchemy**: Database ORM

### Database Schema
- Properties table with 80+ sample records
- Structured queries for filtering
- Vector embeddings for semantic search

### Agent Memory
- Short-term: Request-scoped conversation memory
- Long-term: Persistent user preferences
- Shared: Cross-agent state management

### Error Handling
- Graceful fallbacks when APIs fail
- Rate limit aware retries
- Comprehensive logging

---

## 🧪 Testing Strategy

### Unit Tests
- Test each agent independently
- Verify API endpoints
- Check rate limiting

### Integration Tests
- Test multi-agent workflows
- Verify data flow between agents
- Check frontend-backend interaction

### End-to-End Tests
- Complete user journey testing
- Performance benchmarking
- Load testing

---

## 📚 Reference Documentation

**Project Papers**:
- `ReAltoR.pdf` - Technical architecture document
- `IIT GN AI_ML - 1 Case Study.pdf` - Project case study

**Key Classes**:
- `LangGraphOrchestrator` - Main orchestration engine
- `QueryRouterAgent` - Intent classifier
- `APIGateway` - Request handler
- `RateLimiter` - Rate limiting manager

---

## ⚠️ Important Notes

1. **API Keys Required**: All features require free-tier API keys from external services
2. **Rate Limits**: Respect API quotas to avoid service interruptions
3. **Environment**: Python 3.11 recommended for compatibility
4. **Security**: Never commit `.env` file with real keys
5. **Data**: First run initializes SQLite DB and FAISS indices (~5-10 min)

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'langgraph'"
**Solution**: Ensure Conda environment activated and dependencies installed

### Issue: "GROQ_API_KEY not found"
**Solution**: Create `.env` file with valid API keys

### Issue: "Vector store not initialized"
**Solution**: Run `python src/data_ingestion.py` first

### Issue: Slow queries
**Solution**: Check rate limiting isn't being triggered; verify vector store loaded

---

## 📞 Support & Next Steps

**For Environment Issues**:
```bash
conda env list
conda activate realtor-ai-env
python -c "import langgraph; print(langgraph.__version__)"
```

**For Data Issues**:
```bash
python src/data_ingestion.py --reset  # Force reinitialize
```

**For API Testing**:
```bash
curl http://localhost:8000/health
```

---

**Last Updated**: April 10, 2026  
**Prepared For**: Agentic LangGraph Real Estate Search Implementation
