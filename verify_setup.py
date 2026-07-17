#!/usr/bin/env python3
"""
ReAltoR Project Verification Script
Checks project setup and dependency requirements
"""

import os
import sys
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_directory_structure():
    """Verify all required directories exist"""
    print_header("📁 Checking Directory Structure")
    
    required_dirs = {
        'agents': 'Multi-agent system',
        'backend.py': 'FastAPI backend',
        'frontend.py': 'Streamlit frontend',
        'models': 'LLM integrations',
        'config': 'Configuration',
        'utils': 'Utilities',
        'src': 'Core data modules',
        'data': 'Data storage',
    }
    
    all_exist = True
    for item, desc in required_dirs.items():
        path = Path(item)
        status = "✅" if path.exists() else "❌"
        all_exist = all_exist and path.exists()
        print(f"{status} {item:<20} - {desc}")
    
    return all_exist

def check_python_version():
    """Check Python version"""
    print_header("🐍 Checking Python Version")
    
    version = sys.version_info
    required_version = (3, 11)
    is_compatible = version >= required_version
    
    status = "✅" if is_compatible else "⚠️"
    print(f"{status} Python {version.major}.{version.minor}.{version.micro}")
    print(f"   Required: Python 3.11+")
    
    return is_compatible

def check_dependencies():
    """Check critical dependencies"""
    print_header("📦 Checking Dependencies")
    
    dependencies = [
        'langgraph',
        'langchain',
        'fastapi',
        'streamlit',
        'sqlalchemy',
        'numpy',
        'faiss',
    ]
    
    all_installed = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
            all_installed = False
    
    if not all_installed:
        print("\n⚠️  Some dependencies missing. Run:")
        print("   conda env create -n realtor-ai-env --file requirements.yml")
    
    return all_installed

def check_env_file():
    """Check environment configuration"""
    print_header("🔑 Checking Environment Configuration")
    
    env_file = Path(".env")
    example_file = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file exists")
        with open(env_file) as f:
            content = f.read()
            keys_found = {
                'GROQ_API_KEY': 'GROQ_API_KEY' in content,
                'HUGGINGFACE_API_KEY': 'HUGGINGFACE_API_KEY' in content,
            }
            for key, found in keys_found.items():
                status = "✅" if found else "⚠️"
                print(f"{status} {key}")
    else:
        print("❌ .env file not found")
        if example_file.exists():
            print("📝 Found .env.example - Copy it to .env and add your API keys:")
            print("   cp .env.example .env")
    
    return env_file.exists()

def check_data_files():
    """Check if data files exist"""
    print_header("📊 Checking Data Files")
    
    data_files = {
        'data/vector_store': 'FAISS vector store directory',
        'assets/Property_list.xlsx': 'Sample property data',
    }
    
    all_exist = True
    for file_path, desc in data_files.items():
        path = Path(file_path)
        status = "✅" if path.exists() else "⚠️"
        all_exist = all_exist and path.exists()
        print(f"{status} {file_path:<30} - {desc}")
    
    if not all_exist:
        print("\n📌 Note: Data files will be created when you run:")
        print("   python src/data_ingestion.py")
    
    return all_exist

def print_next_steps():
    """Print recommended next steps"""
    print_header("🚀 Next Steps")
    
    print("""
1. Setup Conda Environment:
   conda env create -n realtor-ai-env --file requirements.yml
   conda activate realtor-ai-env

2. Configure Environment Variables:
   cp .env.example .env
   nano .env  (Add your API keys)

3. Initialize Data:
   python src/data_ingestion.py

4. Start Backend API:
   python backend.py

5. Start Frontend UI (in another terminal):
   streamlit run frontend.py

6. Access the application:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
""")

def main():
    """Run all checks"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         🏠 ReAltoR Search Engine - Setup Checker         ║
    ║     Multi-Agent Real Estate Search System                ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    results = {
        'Directory Structure': check_directory_structure(),
        'Python Version': check_python_version(),
        'Dependencies': check_dependencies(),
        'Environment Config': check_env_file(),
        'Data Files': check_data_files(),
    }
    
    print_header("📋 Verification Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✨ All checks passed! Ready to proceed with implementation.")
    else:
        print("\n⚠️  Some checks failed. Please address the issues above.")
    
    print_next_steps()

if __name__ == '__main__':
    main()
