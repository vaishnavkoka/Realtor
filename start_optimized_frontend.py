import streamlit as st
import requests
import time
import os

st.set_page_config(
    page_title="🏠 ReAltoR - Loading",
    page_icon="🏠",
    layout="centered"
)

# Minimal loading screen
st.title("🏠 ReAltoR Search Engine")
st.subheader("Initializing AI Agents...")

progress_bar = st.progress(0)
status_text = st.empty()

API_BASE_URL = "http://localhost:8000"

def wait_for_backend():
    """Wait for backend to be ready"""
    for attempt in range(60):  # 60 second timeout
        try:
            response = requests.get(f"{API_BASE_URL}/ping", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        
        progress_bar.progress(min((attempt / 60) * 0.5, 0.5))
        status_text.write(f"⏳ Waiting for Backend... ({attempt + 1}/60)")
        time.sleep(1)
    
    return False

def wait_for_agents():
    """Wait for agents to initialize"""
    for attempt in range(120):  # 120 seconds for agent init
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=2)
            data = response.json()
            
            if data.get("agents_ready"):
                return True, data
                
        except:
            pass
        
        progress_bar.progress(min(0.5 + (attempt / 120) * 0.5, 0.99))
        status_text.write(f"🚀 Initializing Agents... ({attempt + 1}/120)")
        time.sleep(1)
    
    return False, {}

# Step 1: Wait for backend
status_text.write("🔌 Connecting to Backend...")
if not wait_for_backend():
    st.error("❌ Backend connection timeout. Please ensure it's running on port 8000")
    st.stop()

status_text.write("✅ Backend Connected! Loading Agents...")

# Step 2: Wait for agents
agents_ready, health_data = wait_for_agents()

if agents_ready:
    progress_bar.progress(1.0)
    status_text.write("✅ All Systems Ready!")
    time.sleep(1)
    st.balloons()
    st.success("🎉 ReAltoR is ready! Refreshing...")
    time.sleep(2)
    st.switch_page("pages/main.py")
else:
    st.warning("⚠️  Agents still loading (this is normal for first run)")
    st.info("🔄 Redirecting to main app...")
    time.sleep(2)
    st.switch_page("pages/main.py")
