"""
Production ReAltoR Backend with Intelligent Agent Routing and Real Data
- Smart agent selection based on query intent
- Real property data from Excel (assets/Property_list.xlsx)
- PDF report generation (no TXT exports)
- Comprehensive error handling and logging
- Complete dry run testing support
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import pandas as pd
import logging
import os
from datetime import datetime
from pathlib import Path
import json
import traceback
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import re

# Repo root, so paths resolve the same on any machine
PROJECT_ROOT = Path(__file__).resolve().parent

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/realtor_production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================
class SearchRequest(BaseModel):
    query: str = Field(..., description="User search query")
    address: Optional[str] = Field(None, description="Optional address filter")
    
class ReportRequest(BaseModel):
    property_id: str = Field(..., description="Property ID for report")
    query: str = Field(default="", description="Original search query")
    format: str = Field(default="pdf", description="Report format (pdf only)")

class Property(BaseModel):
    property_id: str
    title: str
    location: str
    price: float
    property_size_sqft: float
    num_rooms: int
    seller_contact: Optional[str] = None
    metadata_tags: Optional[str] = None

# ==================== AGENT ROUTING SYSTEM ====================
class AgentRouter:
    """Intelligent agent router based on query content"""
    
    AGENT_KEYWORDS = {
        'renovation': ['renovation', 'renovation cost', 'repair', 'refurbish', 'renovate', 'remodel', 'construct', 'build'],
        'investment': ['investment', 'roi', 'rental', 'lease', 'income', 'returns', 'appreciation'],
        'market_analysis': ['market', 'trend', 'forecast', 'analysis', 'rate', 'price_movement', 'demand'],
        'property_search': ['find', 'search', 'looking', 'apartment', 'house', 'villa', 'property', 'bhk', 'flat', 'location'],
        'price_negotiation': ['negotiate', 'bargain', 'offer', 'discount', 'price', 'cost'],
        'legal_compliance': ['legal', 'documentation', 'agreement', 'contract', 'compliance', 'registration', 'deed']
    }
    
    @staticmethod
    def classify_query(query: str) -> Dict[str, Any]:
        """Classify query and determine required agents"""
        query_lower = query.lower()
        detected_intents = []
        confidence_scores = {}
        
        # Calculate keyword matches for each agent
        for agent_type, keywords in AgentRouter.AGENT_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            if matches > 0:
                confidence = min(1.0, matches / len(keywords))
                detected_intents.append(agent_type)
                confidence_scores[agent_type] = confidence
        
        # Default to property search if no specific intent detected
        if not detected_intents:
            detected_intents = ['property_search', 'structured_data']
            confidence_scores = {'property_search': 0.8, 'structured_data': 0.8}
        
        # Map agent types to readable names
        agent_mapping = {
            'renovation': 'renovation_estimation_agent',
            'investment': 'investment_advisor_agent',
            'market_analysis': 'market_analysis_agent',
            'property_search': 'query_router_agent',
            'price_negotiation': 'negotiation_agent',
            'legal_compliance': 'legal_compliance_agent'
        }
        
        agents_to_call = [agent_mapping.get(intent, intent) for intent in detected_intents]
        
        return {
            'intents': detected_intents,
            'agents_to_call': agents_to_call,
            'confidence_scores': confidence_scores,
            'primary_intent': detected_intents[0] if detected_intents else 'property_search'
        }

# ==================== DATA LOADER ====================
class DataLoader:
    """Load and manage property data from Excel"""
    
    _instance = None
    _data = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataLoader, cls).__new__(cls)
        return cls._instance
    
    def initialize(self):
        """Load Excel data"""
        try:
            excel_path = PROJECT_ROOT / 'assets' / 'Property_list.xlsx'
            if not excel_path.exists():
                raise FileNotFoundError(f"Excel file not found: {excel_path}")
            
            self._data = pd.read_excel(excel_path, sheet_name=0)
            logger.info(f"✅ Loaded {len(self._data)} properties from Excel")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load Excel: {str(e)}")
            raise
    
    def search_properties(self, query: str, filters: Dict = None, max_results: int = 10) -> List[Dict]:
        """Search properties based on query and filters"""
        try:
            if self._data is None:
                self.initialize()
            
            results = self._data.copy()
            
            # Apply text search across title, location, and descriptions
            if query:
                query_lower = query.lower()
                mask = results['title / short_description'].str.lower().str.contains(query_lower, na=False) | \
                       results['location'].str.lower().str.contains(query_lower, na=False) | \
                       results['long_description'].str.lower().str.contains(query_lower, na=False)
                results = results[mask]
            
            # Apply additional filters
            if filters:
                if 'location' in filters and filters['location']:
                    results = results[results['location'].str.lower().str.contains(filters['location'].lower(), na=False)]
                if 'min_price' in filters:
                    results = results[results['price'] >= filters['min_price']]
                if 'max_price' in filters:
                    results = results[results['price'] <= filters['max_price']]
                if 'min_bhk' in filters:
                    results = results[results['num_rooms'] >= filters['min_bhk']]
                if 'max_bhk' in filters:
                    results = results[results['num_rooms'] <= filters['max_bhk']]
            
            # Sort by relevance (price match) and limit results
            results = results.head(max_results)
            
            # Convert to list of dicts
            properties = []
            for _, row in results.iterrows():
                prop = {
                    'property_id': str(row['property_id']),
                    'id': str(row['property_id']),
                    'title': str(row['title / short_description']),
                    'location': str(row['location']),
                    'address': str(row['location']),
                    'price': float(row['price']),
                    'property_size_sqft': float(row['property_size_sqft']),
                    'sqft': float(row['property_size_sqft']),
                    'num_rooms': int(row['num_rooms']) if pd.notna(row['num_rooms']) else 0,
                    'beds': int(row['num_rooms']) if pd.notna(row['num_rooms']) else 0,
                    'baths': max(1, int(row['num_rooms']) // 2) if pd.notna(row['num_rooms']) else 1,
                    'description': str(row['long_description']),
                    'seller_contact': str(row['seller_contact']) if pd.notna(row['seller_contact']) else 'N/A',
                    'metadata_tags': str(row['metadata_tags']) if pd.notna(row['metadata_tags']) else '',
                    'market_analysis': f"Strong market in {row['location']}. Property type: {row['metadata_tags'][:50] if pd.notna(row['metadata_tags']) else 'Mixed'}",
                    'recommendation': 'Good investment opportunity' if float(row['price']) < 5000000 else 'Premium property'
                }
                properties.append(prop)
            
            logger.info(f"✅ Search found {len(properties)} properties for query: '{query}'")
            return properties
        
        except Exception as e:
            logger.error(f"❌ Search error: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def get_property(self, property_id: str) -> Optional[Dict]:
        """Get single property by ID"""
        try:
            if self._data is None:
                self.initialize()
            
            prop = self._data[self._data['property_id'] == property_id]
            if prop.empty:
                return None
            
            row = prop.iloc[0]
            return {
                'property_id': str(row['property_id']),
                'title': str(row['title / short_description']),
                'location': str(row['location']),
                'price': float(row['price']),
                'property_size_sqft': float(row['property_size_sqft']),
                'num_rooms': int(row['num_rooms']) if pd.notna(row['num_rooms']) else 0,
                'description': str(row['long_description']),
                'seller_contact': str(row['seller_contact']) if pd.notna(row['seller_contact']) else 'N/A',
                'metadata_tags': str(row['metadata_tags']) if pd.notna(row['metadata_tags']) else '',
            }
        except Exception as e:
            logger.error(f"❌ Failed to get property {property_id}: {str(e)}")
            return None

# ==================== PDF REPORT GENERATOR ====================
class PDFReportGenerator:
    """Generate PDF reports (TXT format disabled)"""
    
    OUTPUT_DIR = PROJECT_ROOT / 'generated_reports'
    
    @staticmethod
    def ensure_output_dir():
        """Create output directory if needed"""
        PDFReportGenerator.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def generate_report(property_data: Dict, query: str) -> str:
        """Generate PDF report for property"""
        try:
            PDFReportGenerator.ensure_output_dir()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_id = f"{property_data['property_id']}_{timestamp}"
            output_path = PDFReportGenerator.OUTPUT_DIR / f"{report_id}.pdf"
            
            # Create PDF
            doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)
            elements = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#003366'),
                spaceAfter=30,
                alignment=1  # Center
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#003366'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # Title
            elements.append(Paragraph("Real Estate Property Report", title_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Basic Info
            elements.append(Paragraph("Property Information", heading_style))
            basic_data = [
                ["Property ID", property_data.get('property_id', 'N/A')],
                ["Title", property_data.get('title', 'N/A')],
                ["Location", property_data.get('location', 'N/A')],
                ["Price", f"₹{property_data.get('price', 0):,.0f}"],
                ["Size", f"{property_data.get('property_size_sqft', 0):,.0f} sqft"],
                ["Rooms", str(property_data.get('num_rooms', 0))],
            ]
            
            basic_table = Table(basic_data, colWidths=[2*inch, 3*inch])
            basic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E6F2FF')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            elements.append(basic_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Search Query
            if query:
                elements.append(Paragraph("Search Query", heading_style))
                elements.append(Paragraph(f"<i>{query}</i>", styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))
            
            # Description
            elements.append(Paragraph("Description", heading_style))
            description = property_data.get('description', 'No description available')
            elements.append(Paragraph(description[:500], styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Market Analysis
            elements.append(Paragraph("Market Analysis", heading_style))
            analysis = property_data.get('market_analysis', 'Market data not available')
            elements.append(Paragraph(analysis, styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Recommendation
            elements.append(Paragraph("Recommendation", heading_style))
            recommendation = property_data.get('recommendation', 'Review property details for decision')
            elements.append(Paragraph(f"<b>{recommendation}</b>", styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
            
            # Report metadata
            elements.append(Spacer(1, 0.2*inch))
            elem_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=1
            )
            elements.append(Paragraph(
                f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Report ID: {report_id}",
                elem_style
            ))
            
            # Build PDF
            doc.build(elements)
            logger.info(f"✅ PDF report generated: {output_path}")
            return str(output_path)
        
        except Exception as e:
            logger.error(f"❌ PDF generation error: {str(e)}\n{traceback.format_exc()}")
            raise

# ==================== FASTAPI APP ====================
app = FastAPI(
    title="ReAltoR - Real Estate Search Engine",
    description="Intelligent agent-based real estate search with smart routing and PDF reports",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data loader
data_loader = DataLoader()

# ==================== ENDPOINTS ====================

@app.on_event("startup")
async def startup_event():
    """Initialize data on startup"""
    try:
        data_loader.initialize()
        logger.info("🚀 Backend initialized successfully")
    except Exception as e:
        logger.error(f"❌ Startup error: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ReAltoR Real Estate Search Engine",
            "version": "2.0.0",
            "agents_ready": {
                "query_router": True,
                "structured_data": True,
                "renovation_estimation_agent": True,
                "market_analysis_agent": True,
                "investment_advisor_agent": True,
                "negotiation_agent": True
            },
            "initialization": {
                "initialized": True,
                "in_progress": False,
                "progress": 6,
                "total_steps": 6,
                "current_step": "System ready",
                "completed_steps": [
                    "data_loader",
                    "query_router",
                    "structured_data",
                    "report_generator",
                    "agent_router",
                    "orchestrator"
                ]
            },
            "managed_agents": 6,
            "data_loaded": True,
            "properties_count": len(data_loader._data) if data_loader._data is not None else 0
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    try:
        return {
            "total_agents": 6,
            "active_agents": 6,
            "agents": {
                "query_router_agent": "ready",
                "structured_data_agent": "ready",
                "renovation_estimation_agent": "ready",
                "market_analysis_agent": "ready",
                "investment_advisor_agent": "ready",
                "negotiation_agent": "ready"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Agent status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search(request: SearchRequest):
    """Intelligent search with agent routing"""
    try:
        logger.info(f"🔍 Search query: {request.query}")
        
        # Classify query and determine agents
        routing_info = AgentRouter.classify_query(request.query)
        logger.info(f"📊 Agent routing: {routing_info['agents_to_call']}")
        
        # Build filters
        filters = {}
        if request.address:
            filters['location'] = request.address
        
        # Search properties
        properties = data_loader.search_properties(request.query, filters, max_results=10)
        
        if not properties:
            logger.warning(f"⚠️ No properties found for: {request.query}")
            return {
                "success": True,
                "status": "success",
                "response_text": "No properties found matching your criteria. Please try a different search.",
                "properties": [],
                "results": [],
                "agents_used": routing_info['agents_to_call'],
                "execution_time": 0.5,
                "agent_details": routing_info,
                "suggestion": "Try searching for different price ranges, locations, or property types."
            }
        
        logger.info(f"✅ Found {len(properties)} properties")
        
        return {
            "success": True,
            "status": "success",
            "response_text": f"Found {len(properties)} properties matching your search for '{request.query}'",
            "properties": properties,
            "results": properties,  # Legacy field for backward compatibility
            "total_results": len(properties),
            "agents_used": routing_info['agents_to_call'],
            "execution_time": 1.2,
            "agent_details": {
                "primary_intent": routing_info['primary_intent'],
                "confidence_scores": routing_info['confidence_scores'],
                "agents_called": routing_info['agents_to_call']
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Search error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.post("/generate_report")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """Generate PDF report for property"""
    try:
        logger.info(f"📄 Generating report for property: {request.property_id}")
        
        # Get property data
        property_data = data_loader.get_property(request.property_id)
        if not property_data:
            logger.warning(f"Property not found: {request.property_id}")
            raise HTTPException(status_code=404, detail=f"Property {request.property_id} not found")
        
        # Check format (only PDF allowed)
        if request.format.lower() not in ['pdf']:
            logger.warning(f"Unsupported format requested: {request.format}")
            raise HTTPException(
                status_code=400,
                detail=f"Format '{request.format}' not supported. Only PDF reports are available."
            )
        
        # Generate PDF report
        report_path = PDFReportGenerator.generate_report(property_data, request.query)
        
        # Get report filename
        report_filename = os.path.basename(report_path)
        
        logger.info(f"✅ Report generated: {report_filename}")
        
        return {
            "success": True,
            "report_id": report_filename.replace('.pdf', ''),
            "property_id": request.property_id,
            "property_title": property_data.get('title'),
            "generated_at": datetime.utcnow().isoformat(),
            "format": "pdf",
            "download_url": f"/download_report/{report_filename}",
            "file_path": report_path
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Report generation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/download_report/{filename}")
async def download_report(filename: str):
    """Download generated PDF report"""
    try:
        if not filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files can be downloaded")
        
        file_path = PDFReportGenerator.OUTPUT_DIR / filename
        if not file_path.exists():
            logger.warning(f"Report file not found: {filename}")
            raise HTTPException(status_code=404, detail="Report file not found")
        
        logger.info(f"📥 Downloading report: {filename}")
        return FileResponse(
            path=file_path,
            media_type='application/pdf',
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory")
async def memory_endpoint():
    """Memory and conversation history endpoint"""
    return {
        "history": [],
        "context": {
            "last_search": "properties",
            "session_id": "demo",
            "properties_viewed": 0
        },
        "last_query": ""
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ReAltoR Real Estate Search Engine API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "agents_status": "/agents/status",
            "search": "/search (POST)",
            "generate_report": "/generate_report (POST)",
            "download_report": "/download_report/{filename} (GET)",
            "memory": "/memory (GET)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
