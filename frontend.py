import streamlit as st
import requests
import json
from datetime import datetime
import time
import pandas as pd
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import base64
import logging
import socket
from typing import Optional, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced error messages
ERROR_MESSAGES = {
    "connection_refused": "Backend server is not running. From the project root, start it with: `uvicorn backend:app --host 0.0.0.0 --port 8000 --reload`",
    "timeout": "Backend server is taking too long to respond. It might be overloaded or initializing agents.",
    "network": "Network connection error. Check your internet connection or firewall settings.",
    "server_error": "Backend server encountered an error. Check the server logs for details.",
    "invalid_json": "Backend returned invalid response. The server might be having issues.",
    "unknown": "An unexpected error occurred. Please refresh the page and try again."
}

def main():
    st.set_page_config(
        page_title="🏠 AI Real Estate Search",
        page_icon="🏠",
        layout="wide"
    )
    
    # Title and description
    st.title("🤖 ReAltoR Search Engine")
    st.markdown("*Multi-agent system with intelligent property search, memory, and reporting*")
    
    # Check system status
    if not check_system_status():
        return
    
    # Sidebar for additional features
    create_sidebar()
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search", "🧠 Memory & History", "📊 Reports", "⚙️ Settings"])
    
    with tab1:
        search_interface()
    
    with tab2:
        memory_interface()
    
    with tab3:
        report_interface()
    
    with tab4:
        settings_interface()

def check_system_status():
    """Check API and agent status with detailed error reporting"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        connected, msg, health_data = check_api_connection()
        
        if connected and health_data:
            init_status = health_data.get("initialization", {})
            
            if init_status.get("initialized"):
                st.success("✅ API Connected")
            elif init_status.get("in_progress"):
                st.warning("⏳ API Connected - Initializing Agents...")
                
                # Show initialization progress
                progress_container = st.container()
                with progress_container:
                    progress_pct = init_status.get("progress", 0) / init_status.get("total_steps", 11)
                    st.progress(progress_pct, text=f"Step {init_status.get('progress', 0)}/{init_status.get('total_steps', 11)}")
                    
                    current_step = init_status.get("current_step", "Initializing...")
                    st.caption(f"🔄 {current_step}")
                    
                    completed = init_status.get("completed_steps", [])
                    if completed:
                        st.caption(f"✅ Completed: {len(completed)} agent(s)")
                    
                    # Auto-rerun to update progress
                    import time
                    time.sleep(1)
                    st.rerun()
                    
            else:
                st.error("❌ API Connected but Not Ready")
                if init_status.get("error"):
                    st.error(f"Initialization Error: {init_status.get('error')}")
        else:
            st.error("❌ API Disconnected")
            
            # Show detailed error message
            if msg in ERROR_MESSAGES:
                st.error(ERROR_MESSAGES[msg])
            
            # Show diagnostic information
            with st.expander("🔧 Troubleshooting Information"):
                st.markdown("**Common Solutions:**")
                st.markdown("""
                1. **Backend not started?** From the project root, start it with:
                   ```bash
                   uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
                   ```
                
                2. **Backend initializing?** Early startup takes 10-30 seconds. Wait and refresh.
                
                3. **Port already in use?** Kill existing process:
                   ```bash
                   pkill -f "uvicorn backend"
                   ```
                
                4. **Check backend status:**
                   ```bash
                   ps aux | grep uvicorn
                   ```
                """)
                
                # Show diagnostics
                st.markdown("**Connection Diagnostics:**")
                diagnostics = diagnose_connection_issues()
                for detail in diagnostics["details"]:
                    st.markdown(f"- {detail}")
                
                if st.button("🔄 Retry Connection"):
                    st.rerun()
            
            st.stop()
    
    with col2:
        if connected and health_data:
            agents_count = health_data.get("managed_agents", 0)
            init_status = health_data.get("initialization", {})
            if init_status.get("initialized"):
                st.info(f"🤖 {agents_count} Agents Active")
            else:
                init_progress = init_status.get("progress", 0)
                st.info(f"🤖 {init_progress}/9 Agents Loading...")
        else:
            st.warning("⚠️ Agents Status Unknown")
    
    with col3:
        if connected and health_data:
            orchestrator_available = health_data.get("orchestrator_available", False)
            if orchestrator_available:
                st.success("🧠 LangGraph Ready")
            else:
                st.warning("⚠️ Orchestrator Loading...")
        else:
            st.warning("⚠️ LangGraph Status Unknown")
    
    return True

def search_interface():
    """Main search interface"""
    st.subheader("🔍 Property Search")
    
    # Example queries
    st.markdown("**💡 Try these example queries:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏢 Studio ", use_container_width=True):
            st.session_state.search_query = "Studio"
    with col2:
        if st.button("🏡 Villa in Nagpur", use_container_width=True):
            st.session_state.search_query = "villa in Nagpur"
    with col3:
        if st.button("🔨 Renovation Cost", use_container_width=True):
            st.session_state.search_query = "renovation cost for 3BHK apartment in Mumbai"
    with col4:
        if st.button("🏠 Houses under 50L", use_container_width=True):
            st.session_state.search_query = "house under 50 lakhs"
    
    st.markdown("---")
    
    # Main search box
    search_query = st.text_area(
        "🔍 Enter your property search query:",
        value=st.session_state.get("search_query", ""),
        placeholder="Examples:\n• Find 2BHK apartments in Mumbai under 80 lakhs\n• What is the renovation cost for a 1200 sqft house?\n• Show me villas in Bangalore with parking\n• Properties in Delhi with 3 bedrooms",
        height=120
    )
    
    # Search button
    if st.button("🚀 Search with AI Agents", type="primary", use_container_width=True):
        if search_query.strip():
            search_with_agents(search_query)
        else:
            st.warning("Please enter a search query")
    
    # AI Visual Report Generator - Prominently placed on main page
    st.markdown("---")
    st.subheader("🤖 AI-Powered Visual Report Generator")
    st.markdown("*Generate personalized reports with charts and visualizations based on your preferences and search history*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**🎯 Generate intelligent reports with:**")
        st.markdown("• 📊 Visual charts based on your search patterns")
        st.markdown("• 🏠 Property recommendations matching your preferences") 
        st.markdown("• 📈 Market trends analysis for your preferred locations")
        st.markdown("• 💰 Budget analysis and investment insights")
        st.markdown("• 🧠 Personalized insights from your search memory")
    
    with col2:
        if st.button("🤖 Generate AI Visual Report", type="secondary", use_container_width=True, key="main_page_report"):
            generate_intelligent_visual_report()
        
        # Quick stats preview
        search_count = len(st.session_state.get("search_history", []))
        preferences_set = bool(st.session_state.get("user_preferences", {}))
        
        if search_count > 0:
            st.metric("🔍 Searches Done", search_count)
        if preferences_set:
            st.success("✅ Preferences Set")
        else:
            st.info("💡 Set preferences in Memory tab")

def validate_query_relevance(query):
    """Validate if query is relevant to real estate/realtors domain
    
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

def search_with_agents(query: str, max_retries: int = 3):
    """Execute search using AI agents with retry logic"""
    
    # First, validate if query is relevant to real estate domain
    is_valid, validation_message = validate_query_relevance(query)
    
    if not is_valid:
        st.warning("⚠️ Query Out of Scope for Real Estate Assistant")
        st.error(f"❌ This query is about '{validation_message}', which is outside the scope of our Real Estate AI Assistant.")
        st.markdown("""
        **I'm specialized in helping with real estate queries like:**
        - 🏠 Finding properties (apartments, villas, houses, plots)
        - 💰 Price estimates and market analysis
        - 🔨 Renovation costs and interior design planning
        - 📍 Location and neighborhood information
        - 🏢 Commercial or residential property search
        - 🎯 Property investments and recommendations
        
        **Please try asking something related to real estate. For example:**
        - "Show me 2BHK apartments in Mumbai under 80 lakhs"
        - "What is the renovation cost for a 1200 sqft house?"
        - "Find me villas in Bangalore with parking"
        - "Properties in Delhi with 3 bedrooms"
        """)
        return
    
    # Create status container
    status_container = st.container()
    with status_container:
        st.info(f"🤖 AI Agents processing: '{query}'")
        
        # Progress simulation
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        stages = [
            "🧠 Analyzing query intent...",
            "🗃️ Searching property database...", 
            "📚 Checking knowledge base...",
            "🔨 Processing estimates...",
            "📊 Synthesizing results..."
        ]
        
        for i, stage in enumerate(stages):
            progress_bar.progress((i + 1) * 20)
            status_text.text(stage)
            time.sleep(0.4)
    
    # Make API call with retry logic
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            logger.info(f"Attempting search (attempt {retry_count + 1}/{max_retries}): {query}")
            
            response = requests.post(
                f"{API_BASE_URL}/search",
                json={"query": query},
                timeout=60  # Longer timeout for agent processing
            )
            
            # Clear progress
            status_container.empty()
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    # Store results in session state to persist across reruns
                    st.session_state.last_search_results = result
                    st.session_state.last_search_query = query
                    display_results(result, query)
                    save_search_history(query, result)
                    return
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {e}")
                    st.error("❌ Backend returned invalid response data")
                    st.code(response.text[:500])
                    return
                    
            elif response.status_code == 500:
                status_container.empty()
                st.error("❌ Server Error (500)")
                with st.expander("Error Details"):
                    st.code(response.text)
                return
                
            elif response.status_code == 400:
                status_container.empty()
                st.error("❌ Invalid Request (400)")
                with st.expander("Error Details"):
                    st.code(response.text)
                return
            else:
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Got status {response.status_code}, retrying...")
                    time.sleep(2 ** retry_count)  # Exponential backoff
                    
        except requests.exceptions.Timeout as e:
            last_error = f"Timeout: Backend took too long to respond"
            logger.warning(f"Timeout on attempt {retry_count + 1}: {e}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(3)  # Wait before retry
                
        except requests.exceptions.ConnectionError as e:
            status_container.empty()
            st.error("❌ Connection Error - Backend Unreachable")
            st.error(ERROR_MESSAGES["connection_refused"])
            
            with st.expander("🔧 Troubleshooting"):
                diagnostics = diagnose_connection_issues()
                for detail in diagnostics["details"]:
                    st.markdown(f"- {detail}")
                if st.button("🔄 Retry After Starting Backend"):
                    st.rerun()
            return
            
        except requests.exceptions.RequestException as e:
            last_error = f"Request Error: {str(e)}"
            logger.error(f"Request error on attempt {retry_count + 1}: {e}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2)
                
        except Exception as e:
            last_error = f"Unexpected Error: {str(e)}"
            logger.error(f"Unexpected error on attempt {retry_count + 1}: {e}", exc_info=True)
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2)
    
    # All retries exhausted
    status_container.empty()
    st.error(f"❌ Search failed after {max_retries} attempts")
    
    with st.expander("Error Details"):
        st.markdown(f"**Last Error:** {last_error}")
        st.markdown("""
        **Possible causes:**
        - Backend server is not running
        - Network connection issue
        - Backend is overloaded
        - Agents are taking too long to initialize
        
        **Solutions:**
        1. Ensure backend is running on port 8000
        2. Wait a few seconds and try again
        3. Check if agents are still initializing (first startup can take 10-30 seconds)
        """)

def display_results(result: dict, query: str):
    """Display search results with error handling"""
    
    try:
        if not result.get("success"):
            st.error("❌ Search failed")
            error_msg = result.get("response_text", "Unknown error")
            st.error(error_msg)
            
            if result.get("error_details"):
                with st.expander("Error Details"):
                    st.code(str(result.get("error_details")))
            return
        
        properties = result.get("properties", [])
        agents_used = result.get("agents_used", [])
        execution_time = result.get("execution_time", 0)
        agent_details = result.get("agent_details", {})
        
        # Results summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏠 Properties", len(properties))
        with col2:
            st.metric("🤖 Agents", len(agents_used))
        with col3:
            st.metric("⏱️ Time", f"{execution_time:.2f}s")
        with col4:
            if properties and any(p.get("price", 0) > 0 for p in properties):
                prices = [p.get("price", 0) for p in properties if p.get("price", 0) > 0]
                avg_price = sum(prices) // len(prices) if prices else 0
                st.metric("💰 Avg Price", f"₹{avg_price:,}" if avg_price > 0 else "Estimates")
            else:
                st.metric("💰 Results", "Found")
        
        # AI Response
        st.subheader("🎯 AI Agent Response")
        response_text = result.get("response_text", "")
        if response_text:
            st.success(response_text)
        else:
            st.info("No specific response generated")
        
        # Agent execution details (expandable)
        with st.expander("🤖 Agent Execution Details"):
            if agents_used:
                st.markdown("**Agents Used:**")
                for agent in agents_used:
                    st.markdown(f"• ✅ {agent.replace('_', ' ').title()} Agent")
            else:
                st.info("No agents were used for this query")
            
            if agent_details:
                st.markdown("**Agent Output Details:**")
                for agent_name, details in agent_details.items():
                    try:
                        st.markdown(f"**{agent_name.title()} Agent:**")
                        if isinstance(details, dict):
                            # Show simplified view
                            if "intent" in details:
                                st.markdown(f"- Intent: {details['intent']}")
                            if "entities" in details:
                                st.markdown(f"- Extracted entities: {details.get('extracted_entities', {})}")
                            if "properties" in details:
                                st.markdown(f"- Properties found: {len(details['properties'])}")
                        st.markdown("---")
                    except Exception as e:
                        logger.error(f"Error displaying agent {agent_name} details: {e}")
                        st.warning(f"Could not parse details for {agent_name}")
        
        # Display properties if found
        if properties:
            st.subheader(f"📋 Found {len(properties)} Properties")
            
            # Create a dataframe for properties
            try:
                props_data = []
                for prop in properties:
                    props_data.append({
                        "Property ID": prop.get("property_id", "N/A"),
                        "Title": prop.get("title", "N/A")[:50],
                        "Location": prop.get("location", "N/A"),
                        "Price": f"₹{prop.get('price', 0):,}" if prop.get('price', 0) > 0 else "N/A",
                        "Size": f"{prop.get('property_size_sqft', 'N/A')} sqft",
                        "Rooms": prop.get("num_rooms", "N/A"),
                    })
                
                if props_data:
                    df = pd.DataFrame(props_data)
                    st.dataframe(df, use_container_width=True)
            except Exception as e:
                logger.error(f"Error displaying properties table: {e}")
                st.warning("Could not format properties table")
                # Show raw data as fallback
                st.json(properties[:3])
        else:
            st.info("No properties were found matching your query")
    
    except Exception as e:
        logger.error(f"Error displaying results: {e}", exc_info=True)
        st.error(f"Error displaying results: {e}")
        st.info("The backend returned data but we had trouble displaying it")
    
    # Display properties
    if properties:
        st.subheader(f"📋 Property Results ({len(properties)})")
        
        for i, prop in enumerate(properties, 1):
            with st.container():
                
                # Check if renovation estimate
                if prop.get("source") == "Renovation_Agent":
                    display_renovation_result(prop, i)
                else:
                    display_property_result(prop, i)
                
                if i < len(properties):
                    st.markdown("---")
    
    # Save to history
    save_search_history(query, result)

def display_property_result(prop: dict, index: int):
    """Display property result with expandable details"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        title = prop.get("title", "Property")
        location = prop.get("location", "Location not specified")
        
        st.markdown(f"**{index}. 🏠 {title}**")
        st.markdown(f"📍 {location}")
        
        # Property details
        details = []
        if prop.get("num_rooms"):
            details.append(f"🏠 {prop['num_rooms']} rooms")
        if prop.get("property_size_sqft"):
            details.append(f"📐 {prop['property_size_sqft']} sqft")
        if prop.get("num_bathrooms"):
            details.append(f"🚿 {prop['num_bathrooms']} bathrooms")
        if prop.get("parking_spaces"):
            details.append(f"🚗 {prop['parking_spaces']} parking")
        
        if details:
            st.markdown(" • ".join(details))
        
        if prop.get("description"):
            st.markdown(f"*{prop['description'][:150]}...*")
        
        # Expandable details section to preserve results on page
        with st.expander(f"📋 View Full Details", key=f"details_{index}_{prop.get('property_id', index)}"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**Property Information:**")
                st.markdown(f"- **ID:** {prop.get('property_id', 'N/A')}")
                st.markdown(f"- **Title:** {prop.get('title', 'N/A')}")
                st.markdown(f"- **Location:** {prop.get('location', 'N/A')}")
                st.markdown(f"- **Size:** {prop.get('property_size_sqft', 'N/A')} sqft")
                st.markdown(f"- **Rooms:** {prop.get('num_rooms', 'N/A')}")
                st.markdown(f"- **Bathrooms:** {prop.get('num_bathrooms', 'N/A')}")
            
            with col_b:
                st.markdown("**Pricing & Features:**")
                price = prop.get("price", 0)
                if price > 0:
                    st.markdown(f"- **Price:** ₹{price:,}")
                    if prop.get("property_size_sqft", 0) > 0:
                        price_per_sqft = price / prop["property_size_sqft"]
                        st.markdown(f"- **Price/sqft:** ₹{price_per_sqft:,.0f}")
                else:
                    st.markdown("- **Price:** On Request")
                st.markdown(f"- **Parking:** {prop.get('parking_spaces', 'N/A')}")
                st.markdown(f"- **Source:** {prop.get('source', 'Database')}")
                if prop.get('relevance_score'):
                    st.markdown(f"- **Match Score:** {prop.get('relevance_score', 0):.2%}")
            
            st.markdown("---")
            if prop.get("description"):
                st.markdown(f"**Description:** {prop.get('description')}")
            st.markdown("**Full Data:**")
            st.json(prop)
    
    with col2:
        price = prop.get("price", 0)
        if price > 0:
            st.markdown(f"**💰 ₹{price:,}**")
            
            if prop.get("property_size_sqft", 0) > 0:
                price_per_sqft = price / prop["property_size_sqft"]
                st.markdown(f"₹{price_per_sqft:,.0f}/sqft")
        else:
            st.markdown("**💰 Price on request**")
        
        # Source
        source = prop.get("source", "Database")
        if source == "RAG_Agent":
            st.markdown("🧠 *AI Knowledge*")
            if prop.get("relevance_score"):
                st.markdown(f"Score: {prop['relevance_score']:.2f}")
        else:
            st.markdown("🗃️ *Database*")

def display_renovation_result(prop: dict, index: int):
    """Display renovation estimate with expandable breakdown"""
    st.markdown(f"**{index}. 🔨 {prop.get('title', 'Renovation Estimate')}**")
    
    renovation_details = prop.get("renovation_details", {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_cost = renovation_details.get("total_cost", 0)
        st.metric("💰 Total Cost", f"₹{total_cost:,}")
    
    with col2:
        timeline = renovation_details.get("timeline", "Not specified")
        st.markdown(f"**⏱️ Timeline:** {timeline}")
    
    with col3:
        property_area = renovation_details.get("property_area", "N/A")
        st.markdown(f"**📐 Area:** {property_area}")
    
    # Expandable breakdown section to preserve results on page
    with st.expander(f"📊 View Cost Breakdown", key=f"breakdown_{index}_{prop.get('title', index)}"):
        breakdown = renovation_details.get("breakdown", {})
        if breakdown:
            # Display breakdown details
            for category, items in breakdown.items():
                st.markdown(f"**{category}:**")
                if isinstance(items, dict):
                    for item, cost in items.items():
                        st.markdown(f"- {item}: ₹{cost:,}")
                elif isinstance(items, (list, int, float)):
                    st.markdown(f"₹{items:,}" if isinstance(items, (int, float)) else str(items))
            st.markdown("---")
            st.json(breakdown)
        else:
            st.info("Detailed breakdown not available")
    
    # Additional details
    if renovation_details.get("description"):
        st.caption(renovation_details.get("description"))

# Utility functions
def check_api_connection(verbose=False):
    """Check API connection with detailed error handling"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API connection successful")
            health_data = response.json()
            return True, "Connected", health_data
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection error: {e}")
        return False, "connection_refused", None
    except requests.exceptions.Timeout as e:
        logger.error(f"❌ Timeout error: {e}")
        return False, "timeout", None
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request error: {e}")
        return False, "network", None
    except Exception as e:
        logger.error(f"❌ Unknown error: {e}")
        return False, "unknown", None
    
    return False, "unknown", None

def get_agents_status(verbose=False):
    """Get agents status with error handling"""
    try:
        response = requests.get(f"{API_BASE_URL}/agents/status", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Agents status retrieved")
            return response.json()
        else:
            logger.error(f"❌ Status code: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        logger.warning("⚠️ Agent status check timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ Cannot connect to backend for agent status")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error getting agent status: {e}")
        return None

def get_health_status(verbose=False):
    """Get health status with error handling"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Health status retrieved")
            return response.json()
        else:
            logger.error(f"❌ Health status code: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        logger.warning("⚠️ Health check timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ Cannot connect to backend for health check")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error in health check: {e}")
        return None

def diagnose_connection_issues():
    """Diagnose connection issues and provide helpful info"""
    diagnostics = {
        "api_url": API_BASE_URL,
        "port_accessible": False,
        "api_responds": False,
        "backend_running": False,
        "details": []
    }
    
    try:
        # Try to connect to port 8000
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            diagnostics["port_accessible"] = True
            diagnostics["details"].append("✓ Port 8000 is accessible")
        else:
            diagnostics["details"].append("✗ Port 8000 is not accessible - backend might not be running")
    except Exception as e:
        diagnostics["details"].append(f"✗ Cannot check port: {e}")
    
    # Try to get health
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            diagnostics["api_responds"] = True
            diagnostics["backend_running"] = True
            diagnostics["details"].append("✓ Backend API is responding")
    except requests.exceptions.ConnectionError:
        diagnostics["details"].append("✗ Backend not responding to API requests")
    except requests.exceptions.Timeout:
        diagnostics["details"].append("✗ Backend timeout - might be initializing agents (takes 10-30s)")
    except Exception as e:
        diagnostics["details"].append(f"✗ API check failed: {e}")
    
    return diagnostics

def save_search_history(query: str, result: dict):
    """Save search history"""
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    
    st.session_state.search_history.append({
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "results_count": len(result.get("properties", [])),
        "agents_used": result.get("agents_used", [])
    })
    
    # Keep last 10
    st.session_state.search_history = st.session_state.search_history[-10:]

def create_sidebar():
    """Create sidebar with user preferences and quick actions"""
    with st.sidebar:
        st.header("🏠 Quick Actions")
        
        # User ID for memory
        user_id = st.text_input("👤 User ID (for memory)", value=st.session_state.get("user_id", "default_user"))
        st.session_state.user_id = user_id
        
        # Quick search templates
        st.subheader("⚡ Quick Searches")
        if st.button("🏢 Apartments in Hyderabad", use_container_width=True):
            st.session_state.search_query = " apartments in Hyderabad"
        
        if st.button("🏡 Villas in Bangalore", use_container_width=True):
            st.session_state.search_query = "3BHK villa in Bangalore with garden"
        
        if st.button("🔨 Renovation Calculator", use_container_width=True):
            st.session_state.search_query = "renovation cost for 1200 sqft apartment"
        
        if st.button("📊 Market Analysis", use_container_width=True):
            st.session_state.search_query = "market analysis for properties in Hyderabad"
        
        # Memory stats
        st.subheader("🧠 Memory Stats")
        history_count = len(st.session_state.get("search_history", []))
        st.metric("Search History", history_count)
        
        if st.button("🗑️ Clear History"):
            st.session_state.search_history = []
            st.success("History cleared!")

def memory_interface():
    """Memory and conversation history interface"""
    st.header("🧠 Memory & Conversation History")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Search History")
        
        if "search_history" in st.session_state and st.session_state.search_history:
            for i, search in enumerate(reversed(st.session_state.search_history[-10:])):
                with st.expander(f"🔍 {search['query'][:50]}..." if len(search['query']) > 50 else search['query']):
                    st.write(f"**Time:** {search['timestamp']}")
                    st.write(f"**Results:** {search['results_count']} properties")
                    st.write(f"**Agents:** {', '.join(search['agents_used'])}")
                    
                    if st.button(f"🔄 Repeat Search", key=f"repeat_{i}"):
                        st.session_state.search_query = search['query']
                        st.experimental_rerun()
        else:
            st.info("No search history yet. Start searching to build your memory!")
    
    with col2:
        st.subheader("👤 User Preferences")
        
        # User preferences (stored in session)
        if "user_preferences" not in st.session_state:
            st.session_state.user_preferences = {
                "preferred_locations": [],
                "budget_range": "50-100 lakhs",
                "property_types": [],
                "bhk_preference": "2BHK"
            }
        
        prefs = st.session_state.user_preferences
        
        # Budget preference
        budget_options = ["Under 50 lakhs", "50-100 lakhs", "1-2 crores", "Above 2 crores"]
        prefs["budget_range"] = st.selectbox("💰 Budget Range", budget_options, 
                                           index=budget_options.index(prefs["budget_range"]))
        
        # Location preference
        location_options = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata"]
        prefs["preferred_locations"] = st.multiselect("📍 Preferred Locations", 
                                                     location_options,
                                                     default=prefs["preferred_locations"])
        
        # Property type preference
        property_options = ["Apartment", "Villa", "House", "Studio", "Plot"]
        prefs["property_types"] = st.multiselect("🏠 Property Types",
                                                property_options,
                                                default=prefs["property_types"])
        
        # BHK preference
        bhk_options = ["Studio", "1BHK", "2BHK", "3BHK", "4BHK", "5BHK+"]
        prefs["bhk_preference"] = st.selectbox("🏢 BHK Preference", bhk_options,
                                             index=bhk_options.index(prefs["bhk_preference"]))
        
        if st.button("💾 Save Preferences"):
            st.success("Preferences saved!")
        
        # Export User Memory Section
        st.markdown("---")
        st.subheader("📄 Export Your Data")
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("📥 Download Memory PDF", use_container_width=True):
                generate_user_memory_pdf()
        
        with col4:
            if st.button("📊 Export Search History CSV", use_container_width=True):
                export_search_history_csv()

def report_interface():
    """Report generation interface"""
    st.header("📊 Report Generation")
    
    st.markdown("Generate comprehensive property reports and market analysis")
    
    # Report type selection
    report_type = st.selectbox("📋 Select Report Type", [
        "Property Investment Analysis",
        "Market Trends Report", 
        "Neighborhood Comparison",
        "Property Valuation Report",
        "Rental Yield Analysis"
    ])
    
    # Report parameters
    col1, col2 = st.columns(2)
    
    with col1:
        location = st.text_input("📍 Location", placeholder="e.g., Bangalore, Mumbai")
        property_type = st.selectbox("🏠 Property Type", ["All", "Apartment", "Villa", "House", "Studio"])
    
    with col2:
        budget_min = st.number_input("💰 Min Budget (Lakhs)", min_value=0, value=50)
        budget_max = st.number_input("💰 Max Budget (Lakhs)", min_value=0, value=200)
    
    # Additional parameters based on report type
    if report_type == "Property Investment Analysis":
        investment_horizon = st.selectbox("⏰ Investment Horizon", ["1 Year", "3 Years", "5 Years", "10+ Years"])
        risk_appetite = st.selectbox("📈 Risk Appetite", ["Conservative", "Moderate", "Aggressive"])
    
    elif report_type == "Neighborhood Comparison":
        neighborhoods = st.text_area("🏘️ Neighborhoods to Compare", 
                                   placeholder="Enter neighborhoods separated by commas\ne.g., Koramangala, Whitefield, HSR Layout")
    
    # Generate report button
    if st.button("📊 Generate Report", type="primary", use_container_width=True):
        if location:
            generate_report(report_type, {
                "location": location,
                "property_type": property_type,
                "budget_min": budget_min,
                "budget_max": budget_max,
                "report_type": report_type
            })
        else:
            st.warning("Please enter a location")
    
    # Recent reports
    st.subheader("📁 Recent Reports")
    
    if "generated_reports" not in st.session_state:
        st.session_state.generated_reports = []
    
    if st.session_state.generated_reports:
        for i, report in enumerate(st.session_state.generated_reports[-5:]):
            with st.expander(f"📄 {report['title']} - {report['timestamp'][:10]}"):
                st.markdown(report['content'])
                if st.download_button(
                    f"📥 Download",
                    data=report['content'],
                    file_name=f"{report['title'].replace(' ', '_')}.txt",
                    key=f"download_{i}"
                ):
                    st.success("Report downloaded!")
    else:
        st.info("No reports generated yet")
    
    # Intelligent Report Generator Section
    st.markdown("---")
    st.subheader("🤖 AI-Powered Visual Report Generator")
    st.markdown("*Generate personalized reports with charts and visualizations based on your preferences and search history*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**🎯 This intelligent report will include:**")
        st.markdown("• 📊 Visual charts based on your search patterns")
        st.markdown("• 🏠 Property recommendations matching your preferences") 
        st.markdown("• 📈 Market trends analysis for your preferred locations")
        st.markdown("• 💰 Budget analysis and investment insights")
        st.markdown("• 🧠 Personalized insights from your search memory")
    
    with col2:
        if st.button("🤖 Generate AI Visual Report", type="primary", use_container_width=True):
            generate_intelligent_visual_report()

def generate_intelligent_visual_report():
    """Generate intelligent visual report based on user preferences and memory"""
    try:
        with st.spinner("🤖 AI is analyzing your preferences and generating visual report..."):
            # Get user data
            preferences = st.session_state.get("user_preferences", {})
            search_history = st.session_state.get("search_history", [])
            
            # Create intelligent analysis
            st.subheader("🎯 Your Personalized AI Report")
            
            if not search_history:
                st.warning("⚠️ No search history found. Please perform some searches first to generate a meaningful report.")
                return
            
            # Generate visualizations
            generate_search_pattern_charts(search_history)
            generate_preference_analysis_charts(preferences)
            generate_market_insights(search_history, preferences)
            
            # Create downloadable report
            create_downloadable_visual_report(search_history, preferences)
            
    except Exception as e:
        st.error(f"❌ Failed to generate AI report: {str(e)}")

def generate_search_pattern_charts(search_history):
    """Generate charts showing user's search patterns"""
    st.subheader("📊 Your Search Patterns")
    
    if not search_history:
        st.info("No search data available")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(search_history)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Search frequency over time
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            daily_searches = df.groupby('date').size().reset_index()
            daily_searches.columns = ['Date', 'Searches']
            
            fig1 = px.line(daily_searches, x='Date', y='Searches', 
                          title='📈 Daily Search Activity',
                          color_discrete_sequence=['#1f77b4'])
            fig1.update_layout(height=300)
            st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Results distribution
        if 'results_count' in df.columns:
            fig2 = px.histogram(df, x='results_count', 
                               title='📊 Search Results Distribution',
                               color_discrete_sequence=['#ff7f0e'])
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
    
    # Top search terms
    if 'query' in df.columns:
        st.markdown("**🔥 Your Most Searched Terms:**")
        query_words = []
        for query in df['query']:
            words = str(query).lower().split()
            # Filter common words
            filtered_words = [w for w in words if w not in ['in', 'the', 'for', 'and', 'or', 'with', 'under', 'above']]
            query_words.extend(filtered_words)
        
        if query_words:
            word_freq = pd.Series(query_words).value_counts().head(10)
            fig3 = px.bar(x=word_freq.values, y=word_freq.index, 
                         orientation='h', title='🏷️ Most Searched Keywords',
                         color_discrete_sequence=['#2ca02c'])
            fig3.update_layout(height=400)
            st.plotly_chart(fig3, use_container_width=True)

def generate_preference_analysis_charts(preferences):
    """Generate charts analyzing user preferences"""
    st.subheader("🎯 Your Preferences Analysis")
    
    if not preferences:
        st.info("💡 Set your preferences in the Memory & History tab to see personalized analysis!")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Budget preference visualization
        if 'budget_range' in preferences:
            budget_info = preferences['budget_range']
            st.metric("💰 Preferred Budget", budget_info)
        
        # Location preferences
        if 'preferred_locations' in preferences and preferences['preferred_locations']:
            locations = preferences['preferred_locations']
            fig4 = px.pie(values=[1]*len(locations), names=locations, 
                         title='📍 Preferred Locations Distribution')
            st.plotly_chart(fig4, use_container_width=True)
    
    with col2:
        # Property type preferences
        if 'property_types' in preferences and preferences['property_types']:
            prop_types = preferences['property_types']
            fig5 = px.bar(x=prop_types, y=[1]*len(prop_types),
                         title='🏠 Preferred Property Types',
                         color_discrete_sequence=['#d62728'])
            fig5.update_layout(showlegend=False)
            st.plotly_chart(fig5, use_container_width=True)
        
        # BHK preference
        if 'bhk_preference' in preferences:
            st.metric("🏢 Preferred BHK", preferences['bhk_preference'])

def generate_market_insights(search_history, preferences):
    """Generate market insights based on user data"""
    st.subheader("📈 Market Insights & Recommendations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔍 Total Searches", len(search_history), "This month")
    
    with col2:
        if search_history:
            avg_results = sum(s.get('results_count', 0) for s in search_history) / len(search_history)
            st.metric("📊 Avg Results", f"{avg_results:.1f}", "Per search")
    
    with col3:
        unique_queries = len(set(s.get('query', '') for s in search_history))
        st.metric("🎯 Unique Searches", unique_queries)
    
    # AI Recommendations
    st.markdown("**🤖 AI Recommendations Based on Your Activity:**")
    
    recommendations = []
    
    # Analyze search patterns for recommendations
    if search_history:
        # Check for budget patterns
        budget_mentions = sum(1 for s in search_history if any(word in s.get('query', '').lower() 
                             for word in ['budget', 'cost', 'price', 'cheap', 'expensive']))
        if budget_mentions > len(search_history) * 0.5:
            recommendations.append("💰 You seem budget-conscious. Consider looking at emerging areas for better value.")
    
    if preferences.get('preferred_locations'):
        recommendations.append(f"📍 Focus on {', '.join(preferences['preferred_locations'][:2])} for consistent results.")
    
    if not recommendations:
        recommendations = [
            "🎯 Continue exploring different areas to find the best deals",
            "📊 Your search patterns show good market research habits",
            "💡 Consider setting specific preferences for more targeted results"
        ]
    
    for i, rec in enumerate(recommendations[:3], 1):
        st.markdown(f"{i}. {rec}")

def create_downloadable_visual_report(search_history, preferences):
    """Create downloadable visual report"""
    st.subheader("📥 Download Your Visual Report")
    
    # Create comprehensive report content
    report_content = f"""
AI-POWERED VISUAL REPORT
========================
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

EXECUTIVE SUMMARY
----------------
• Total Searches Performed: {len(search_history)}
• Unique Search Queries: {len(set(s.get('query', '') for s in search_history))}
• Average Results per Search: {sum(s.get('results_count', 0) for s in search_history) / len(search_history) if search_history else 0:.1f}

USER PREFERENCES
---------------
{json.dumps(preferences, indent=2) if preferences else 'No preferences set yet'}

SEARCH ACTIVITY ANALYSIS
-----------------------
"""
    
    # Add search history details
    for i, search in enumerate(search_history[-10:], 1):
        report_content += f"""
{i}. Search Query: {search.get('query', 'Unknown')}
   Date: {search.get('timestamp', 'Unknown')[:10] if search.get('timestamp') else 'Unknown'}
   Results Found: {search.get('results_count', 0)}
   Agents Activated: {', '.join(search.get('agents_used', []))}
"""
    
    report_content += f"""

AI INSIGHTS & RECOMMENDATIONS
----------------------------
1. Your search patterns indicate a systematic approach to property research
2. Focus on your preferred locations for better targeted results
3. Consider diversifying your search criteria for more opportunities
4. Your activity level shows good market engagement

MARKET ANALYSIS
--------------
Based on your search history, you show interest in diverse property options.
Continue exploring different areas and price ranges to maximize opportunities.

Report generated by AI Real Estate Search Engine
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # Create download button
    report_bytes = report_content.encode()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📄 Download Full Report (Text)",
            data=report_bytes,
            file_name=f"AI_Visual_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            type="primary"
        )
    
    with col2:
        # Create HTML version with charts
        html_report = create_html_report_with_charts(search_history, preferences)
        st.download_button(
            label="🌐 Download HTML Report",
            data=html_report.encode(),
            file_name=f"AI_Visual_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            type="secondary"
        )
    
    st.success("✅ Visual report generated! Your personalized analysis is ready for download.")
    
    # Show preview
    with st.expander("👀 Preview Report Content"):
        st.text(report_content)

def create_html_report_with_charts(search_history, preferences):
    """Create HTML report with embedded charts"""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI-Powered Property Search Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        .chart-container {{ margin: 20px 0; padding: 20px; background: #ffffff; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h1>🤖 AI-Powered Property Search Report</h1>
    <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    
    <h2>📊 Executive Summary</h2>
    <div class="metric">
        <strong>Total Searches:</strong> {len(search_history)}<br>
        <strong>Unique Queries:</strong> {len(set(s.get('query', '') for s in search_history))}<br>
        <strong>Average Results:</strong> {sum(s.get('results_count', 0) for s in search_history) / len(search_history) if search_history else 0:.1f}
    </div>
    
    <h2>🎯 User Preferences</h2>
    <div class="metric">
        {json.dumps(preferences, indent=2) if preferences else 'No preferences set yet'}
    </div>
    
    <h2>🔍 Recent Search Activity</h2>
"""
    
    # Add recent searches
    for i, search in enumerate(search_history[-5:], 1):
        html_content += f"""
    <div class="metric">
        <strong>Search {i}:</strong> {search.get('query', 'Unknown')}<br>
        <strong>Date:</strong> {search.get('timestamp', 'Unknown')[:10] if search.get('timestamp') else 'Unknown'}<br>
        <strong>Results:</strong> {search.get('results_count', 0)}
    </div>
"""
    
    html_content += """
    <h2>🤖 AI Recommendations</h2>
    <div class="metric">
        1. Continue systematic property research approach<br>
        2. Focus on preferred locations for better targeting<br>
        3. Consider diversifying search criteria<br>
        4. Maintain consistent market engagement
    </div>
    
    <footer style="margin-top: 50px; text-align: center; color: #7f8c8d;">
        <p>Generated by AI Real Estate Search Engine</p>
    </footer>
</body>
</html>
"""
    
    return html_content

def generate_report(report_type: str, params: dict):
    """Generate a report using the backend"""
    try:
        with st.spinner(f"🔄 Generating {report_type}..."):
            
            # Create report query
            query = f"Generate {report_type} for {params['property_type']} in {params['location']} "
            query += f"with budget between {params['budget_min']}-{params['budget_max']} lakhs"
            
            # Call backend
            response = requests.post(f"{API_BASE_URL}/search", json={"query": query}, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Create report
                report_content = f"# {report_type}\n\n"
                report_content += f"**Location:** {params['location']}\n"
                report_content += f"**Property Type:** {params['property_type']}\n"
                report_content += f"**Budget Range:** ₹{params['budget_min']}-{params['budget_max']} Lakhs\n"
                report_content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                report_content += "---\n\n"
                report_content += result.get("response_text", "No content generated")
                
                # Save report
                if "generated_reports" not in st.session_state:
                    st.session_state.generated_reports = []
                
                st.session_state.generated_reports.append({
                    "title": f"{report_type} - {params['location']}",
                    "content": report_content,
                    "timestamp": datetime.now().isoformat(),
                    "params": params
                })
                
                # Display report
                st.success("✅ Report Generated Successfully!")
                st.markdown(report_content)
                
            else:
                st.error(f"Failed to generate report: {response.status_code}")
                
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")

def settings_interface():
    """Settings and configuration interface"""
    st.header("⚙️ Settings & Configuration")
    
    # API Configuration
    st.subheader("🔌 API Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        api_url = st.text_input("🌐 Backend API URL", value=API_BASE_URL)
        if st.button("🔗 Test Connection"):
            if check_api_connection():
                st.success("✅ API Connection Successful")
            else:
                st.error("❌ API Connection Failed")
    
    with col2:
        timeout = st.number_input("⏱️ Request Timeout (seconds)", min_value=5, max_value=60, value=15)
    
    # Agent Configuration
    st.subheader("🤖 Agent Settings")
    
    agent_settings = st.session_state.get("agent_settings", {
        "enable_parallel": True,
        "enable_fallback": True,
        "max_retries": 3,
        "preferred_agents": ["structured_data", "rag"]
    })
    
    agent_settings["enable_parallel"] = st.checkbox("⚡ Enable Parallel Agent Execution", 
                                                   value=agent_settings["enable_parallel"])
    
    agent_settings["enable_fallback"] = st.checkbox("🔄 Enable Agent Fallback", 
                                                   value=agent_settings["enable_fallback"])
    
    agent_settings["max_retries"] = st.number_input("🔁 Max Retry Attempts", 
                                                   min_value=1, max_value=5, 
                                                   value=agent_settings["max_retries"])
    
    # System Information
    st.subheader("📊 System Information")
    
    system_info = get_system_info()
    if system_info:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🤖 Total Agents", system_info.get("total_agents", "Unknown"))
        
        with col2:
            st.metric("✅ Active Agents", system_info.get("active_agents", "Unknown"))
        
        with col3:
            st.metric("🧠 Orchestrator", "Ready" if system_info.get("orchestrator_available") else "Offline")
    
    # Export/Import Settings
    st.subheader("📁 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Search History"):
            if "search_history" in st.session_state:
                import json
                history_json = json.dumps(st.session_state.search_history, indent=2)
                st.download_button(
                    "📁 Download History",
                    data=history_json,
                    file_name=f"search_history_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
    
    with col2:
        if st.button("🗑️ Clear All Data"):
            if st.button("⚠️ Confirm Clear All Data", type="primary"):
                st.session_state.clear()
                st.success("All data cleared!")
                st.experimental_rerun()

def get_system_info():
    """Get system information"""
    try:
        agents_status = get_agents_status()
        health_status = get_health_status()
        
        return {
            "total_agents": agents_status.get("total_agents", 0) if agents_status else 0,
            "active_agents": agents_status.get("active_agents", 0) if agents_status else 0,
            "orchestrator_available": health_status.get("orchestrator_available", False) if health_status else False
        }
    except:
        return None

def generate_user_memory_pdf():
    """Generate PDF report of user memory and preferences"""
    try:
        with st.spinner("🔄 Generating your memory report..."):
            # Get user data
            preferences = st.session_state.get("user_preferences", {})
            search_history = st.session_state.get("search_history", [])
            
            # Create comprehensive memory report
            report_content = f"""
USER MEMORY & PREFERENCES REPORT
================================
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

USER PREFERENCES
---------------
{json.dumps(preferences, indent=2) if preferences else 'No preferences saved yet'}

SEARCH HISTORY SUMMARY
--------------------
Total Searches: {len(search_history)}
Most Recent Searches:
"""
            
            # Add recent search history
            for i, search in enumerate(search_history[-10:], 1):
                report_content += f"""
{i}. Query: {search['query']}
   Date: {search['timestamp'][:10] if 'timestamp' in search else 'Unknown'}
   Results Found: {search.get('results_count', 0)}
   Agents Used: {', '.join(search.get('agents_used', []))}
"""
            
            # Create downloadable PDF (simulated as text for now)
            pdf_bytes = report_content.encode()
            
            # Offer download
            st.download_button(
                label="📥 Download Memory Report PDF",
                data=pdf_bytes,
                file_name=f"user_memory_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                type="primary"
            )
            
            st.success("✅ Memory report generated! Click download button above.")
            
            # Show preview
            with st.expander("👀 Preview Report"):
                st.text(report_content)
                
    except Exception as e:
        st.error(f"❌ Failed to generate memory report: {str(e)}")

def export_search_history_csv():
    """Generate CSV export of search history"""
    try:
        search_history = st.session_state.get("search_history", [])
        
        if not search_history:
            st.warning("⚠️ No search history to export")
            return
            
        with st.spinner("🔄 Generating CSV export..."):
            # Convert to DataFrame
            df = pd.DataFrame(search_history)
            
            # Convert to CSV
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            # Offer download
            st.download_button(
                label="📊 Download Search History CSV",
                data=csv_data,
                file_name=f"search_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                type="secondary"
            )
            
            st.success("✅ CSV export ready! Click download button above.")
            
            # Show preview
            with st.expander("👀 Preview Data"):
                st.dataframe(df)
                
    except Exception as e:
        st.error(f"❌ Failed to generate CSV export: {str(e)}")

if __name__ == "__main__":
    main()