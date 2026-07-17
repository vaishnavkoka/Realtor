# 🔒 Security Audit Report - agentic_langgraph

**Date**: 17 April 2026  
**Status**: ⚠️ **ISSUES FOUND - FIX REQUIRED BEFORE PUSH**

---

## 📋 Executive Summary

Your codebase contains **3 moderate security issues** that should be fixed before pushing to a public repository. None of these expose **actual API keys in the repository**, but they represent bad practices and potential risks.

---

## ⚡ QUICK FIXES REFERENCE

| File | Line | Issue | Fix |
|------|------|-------|-----|
| `src/database_schema.py` | 88 | Hardcoded password in default URL | Use `os.getenv('DATABASE_URL', ...)` |
| `agents/planner_agent.py` | 70 | Placeholder API key default | Remove default, use `os.getenv('GROQ_API_KEY')` |
| `agents/memory_enhanced_planner.py` | 75 | Placeholder API key default | Remove default, use `os.getenv('GROQ_API_KEY')` |

**Critical**: Before pushing, revoke all 5 real API keys in `.env` - they are currently exposed but protected by .gitignore.

---

## 🔴 CRITICAL FINDINGS

### 1. ⚠️ **Real API Keys in .env File** (Should be VERIFIED)

**Location**: `.env` (file root)

**Issue**: The `.env` file contains REAL, active API keys:
```env
GROQ_API_KEY=<redacted>
HUGGINGFACE_API_KEY=<redacted>
SERPER_API_KEY=<redacted>
TAVILY_API_KEY=<redacted>
COHERE_API_KEY=<redacted>
```

> The key values are redacted here. Quoting them in a tracked file would have
> published exactly what this finding warns about.

**Status**: ✅ **PROTECTED BY .gitignore** (.env is correctly in .gitignore)

**Risk Level**: 🟡 **MEDIUM** - Only if .env is accidentally committed

**Action Required**:
- ✅ .env IS in .gitignore - Good!
- ⚠️ BUT these keys should be REVOKED after pushing code
- 🔧 Create new test API keys for public repository  
- 🔧 Replace current keys with temporary/test keys

---

### 2. ⚠️ **Hardcoded Database Passwords**

**Location**: `src/database_schema.py`, line 88

**Issue**:
```python
'default_url': 'postgresql://realestate:password@localhost:5432/realestate_db'
```

**Risk**: If this gets checked into git or used in CI/CD, credentials are exposed

**Fix**:
```python
'default_url': os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/realestate')
```

---

### 3. ⚠️ **Default API Key Placeholders in Code**

**Locations**: 
- `agents/planner_agent.py`, line 70
- `agents/memory_enhanced_planner.py`, line 75

**Issue**:
```python
groq_api_key=os.getenv('GROQ_API_KEY', 'your-groq-api-key-here')
```

**Risk**: While not actual keys, it's bad practice and shows inconsistency

**Fix**: Remove default values entirely to force explicit env variable setting:
```python
groq_api_key=os.getenv('GROQ_API_KEY')
```

---

## ✅ SECURE PRACTICES (WELL DONE!)

✅ All API keys are loaded from environment variables via `os.getenv()`  
✅ `.env` file is properly in `.gitignore`  
✅ `.env.example` provides template without credentials  
✅ No actual API keys found hard-coded in Python source files  
✅ CORS credentials are explicitly set (not overly permissive)  
✅ No database passwords in connection strings from imports (via os.getenv)  

---

## 🛠️ Recommendations Before Push

### **IMMEDIATE (Before first push)**

1. **Revoke all API keys in .env**
   ```bash
   # Visit and regenerate these:
   - Groq: https://console.groq.com/keys
   - HuggingFace: https://huggingface.co/settings/tokens
   - Serper: https://serper.dev/
   - Tavily: https://tavily.com/
   - Cohere: https://dashboard.cohere.ai/
   ```

2. **Create a .env with test/temporary keys only**
   - Generate new free tier API keys
   - Use these in the repository's .env
   - Never commit real .env

3. **Fix database_schema.py**
   - Replace hardcoded 'password' with environment variable
   - Already partially done in config/settings.py, just need to update default example

4. **Remove default placeholder values**
   - In planner_agent.py and memory_enhanced_planner.py
   - Force environment variables without defaults

### **BEFORE PUSHING TO PUBLIC REPO**

- [ ] Verify .gitignore is correct
- [ ] Confirm .env is NOT in git status as modified/staged
- [ ] Run `git status --ignored` to verify .env is ignored
- [ ] Use a secret scanning tool: 
  ```bash
  pip install detect-secrets
  detect-secrets scan --all-files
  ```

### **OPTIONAL (BEST PRACTICES)**

- Add `.env.local` and `.env.*.local` to .gitignore (already done ✅)
- Use GitHub Secrets for CI/CD pipelines
- Consider using Python-dotenv with validation
- Add pre-commit hook to prevent credential commits:
  ```bash
  pip install pre-commit
  # Add hook to check for credentials
  ```

---

## 📝 Files to Review

| File | Issue | Severity | Fix Required |
|------|-------|----------|--------------|
| `.env` | Real API keys stored | 🟡 MEDIUM | Replace with test keys ✅ |
| `src/database_schema.py` | Hardcoded password example | 🟡 MEDIUM | Use env var for default ⚠️ |
| `agents/planner_agent.py` | Default placeholder value | 🟡 MEDIUM | Remove default ⚠️ |
| `agents/memory_enhanced_planner.py` | Default placeholder value | 🟡 MEDIUM | Remove default ⚠️ |
| `config/settings.py` | ✅ Correctly uses env vars | ✅ GOOD | No action needed |
| `.env.example` | ✅ Template only, no real keys | ✅ GOOD | No action needed |

---

## 🔍 Files Checked

✅ config/settings.py - All environment variable based  
✅ models/free_models.py - Uses APIKeys from config  
✅ agents/langgraph_orchestrator.py - Uses os.getenv safely  
✅ agents/web_research_agent.py - Uses APIKeys from config  
✅ backend.py - No hardcoded credentials  
✅ frontend.py - No hardcoded credentials  
✅ .gitignore - Correctly includes .env patterns  

---

## 🚀 Before Pushing - Checklist

```bash
# 1. Verify no .env is staged
git status

# 2. Check git history for .env
git log --name-only | grep "\.env" | grep -v "\.env\."

# 3. Scan for secrets
pip install detect-secrets
detect-secrets scan

# 4. Verify .gitignore is working
git check-ignore -v .env

# 5. Do a final grep for sensitive patterns
grep -r "password" agentic_langgraph/ --include="*.py" | grep -v "password@localhost" | grep -v "default_url"
grep -r "your-" agentic_langgraph/ --include="*.py"
```

---

## ✅ SAFE TO PUSH IF

- [ ] .env is NOT committed to git
- [ ] All real API keys have been revoked
- [ ] Placeholder .env uses test keys only or has been removed
- [ ] database_schema.py default uses env var instead of hardcoded password
- [ ] Default placeholder values removed from planner agents

---

**Last Checked**: 17 April 2026 20:15 UTC  
**Audited By**: Security Code Review Agent  
**Recommendation**: ⚠️ **DO NOT PUSH YET** - Follow fixes above first
