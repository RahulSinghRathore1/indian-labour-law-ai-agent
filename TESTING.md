# Testing Guide - Indian Labour Law AI Agent

## How Users Will Use This App

### **1. Web Dashboard Users**
Access the beautiful dashboard at `http://localhost:5000`

**What they see:**
- Total laws indexed
- Last crawl timestamp
- 4 main action cards
- List of features

**What they can do:**
- Search for labour laws
- View detailed law information
- Trigger manual crawls
- Check system statistics

---

### **2. API Users (Developers)**
Integrate with their own applications using REST APIs

**Endpoints available:**
- Search laws semantically
- Get law details
- Trigger crawls
- View audit logs
- Check system health

---

### **3. CLI Users (DevOps/Admins)**
Use command-line tools for automation and monitoring

**Commands:**
- `python orchestrator.py crawl` - Run full crawl
- `python orchestrator.py search "query"` - Search from CLI
- `python orchestrator.py stats` - View statistics

---

## Complete Testing Checklist for Reviewers

### **Pre-Testing Setup**
```bash
# 1. Start the application
python main.py

# 2. Verify app is running
curl http://localhost:5000/api/health
# Expected: {"status": "healthy", "timestamp": "..."}
```

---

## **Test 1: Web Dashboard (Visual Testing)**

**Steps:**
1. Open browser: `http://localhost:5000`
2. Observe the homepage

**Verify:**
- [ ] Title displays: "Indian Labour Law AI Agent"
- [ ] Subtitle shows: "Automated crawler for Indian labour law updates..."
- [ ] 3 stats cards visible (Total Laws, Last Crawl, Crawl Sessions)
- [ ] 4 action cards visible (Search, Details, Trigger Crawl, View Logs)
- [ ] 6 key features listed below
- [ ] Stats update in real-time (try API call, refresh page)

---

## **Test 2: Health Check Endpoint**

**Command:**
```bash
curl http://localhost:5000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-28T16:05:03.123456"
}
```

**Verify:**
- [ ] Status is "healthy"
- [ ] Timestamp is current

---

## **Test 3: System Statistics**

**Command:**
```bash
curl http://localhost:5000/api/stats
```

**Expected Response (before any crawls):**
```json
{
  "total_laws": 0,
  "total_sessions": 0,
  "last_crawl": null
}
```

**Verify:**
- [ ] Returns valid JSON
- [ ] All fields present
- [ ] Numbers are >= 0

---

## **Test 4: Start Crawl (Most Important Test)**

**Command:**
```bash
curl -X POST http://localhost:5000/api/crawl/start
```

**Expected Response:**
```json
{
  "message": "Crawl started in background",
  "status": "running"
}
```

**Verify:**
- [ ] Returns 200 status code
- [ ] Message indicates crawl started
- [ ] Response is immediate (async)

**Wait 30-60 seconds for crawl to complete**

---

## **Test 5: Verify Crawl Completed**

**Command (after 30 sec wait):**
```bash
curl http://localhost:5000/api/stats
```

**Expected Response:**
```json
{
  "total_laws": 2,
  "total_sessions": 1,
  "last_crawl": "2025-11-28 16:05"
}
```

**Verify:**
- [ ] `total_laws` > 0 (laws were added)
- [ ] `total_sessions` = 1 (one crawl completed)
- [ ] `last_crawl` timestamp is recent

---

## **Test 6: List All Laws**

**Command:**
```bash
curl http://localhost:5000/api/laws?page=1&per_page=10
```

**Expected Response:**
```json
{
  "laws": [
    {
      "id": 1,
      "title": "Labour Code on Wages",
      "category": "Act",
      "source": "Ministry of Labour",
      "summary": "This code establishes...",
      "url": "https://...",
      "created_at": "2025-11-28T16:05:00",
      "updated_at": "2025-11-28T16:05:00",
      "version": 1
    }
  ],
  "total": 2,
  "pages": 1,
  "current_page": 1
}
```

**Verify:**
- [ ] Laws array is not empty
- [ ] Each law has id, title, category, source
- [ ] Summary field is populated (Groq worked!)
- [ ] Version field exists
- [ ] Timestamps are recent

---

## **Test 7: Get Specific Law Details**

**Command:**
```bash
curl http://localhost:5000/api/laws/1
```

**Expected Response:**
```json
{
  "id": 1,
  "title": "Labour Code on Wages",
  "content": "Full law text...",
  "summary": "AI-generated summary from Groq...",
  "category": "Act",
  "source": "Ministry of Labour",
  "language": "en",
  "version": 1
}
```

**Verify:**
- [ ] Law with ID 1 exists
- [ ] Content field has full text
- [ ] Summary field is NOT empty (Groq generated it)
- [ ] Summary is NOT "[Auto-generated excerpt]" (means Groq API worked)
- [ ] Language detected correctly

---

## **Test 8: Semantic Search (Core Feature)**

**Command:**
```bash
curl -X POST http://localhost:5000/api/laws/search \
  -H "Content-Type: application/json" \
  -d '{"query": "minimum wage", "limit": 5}'
```

**Expected Response:**
```json
{
  "query": "minimum wage",
  "results": [
    {
      "id": 1,
      "title": "Labour Code on Wages",
      "summary": "...",
      "similarity_score": 0.92
    }
  ],
  "total": 1
}
```

**Verify:**
- [ ] Results returned for query
- [ ] Each result has similarity_score (0-1 range)
- [ ] Results sorted by similarity (highest first)
- [ ] Similarity scores make sense (0.9+ = very similar)

---

## **Test 9: Try Different Search Queries**

**Test Case 1: Labour-related query**
```bash
curl -X POST http://localhost:5000/api/laws/search \
  -H "Content-Type: application/json" \
  -d '{"query": "worker safety", "limit": 3}'
```

**Test Case 2: Generic query**
```bash
curl -X POST http://localhost:5000/api/laws/search \
  -H "Content-Type: application/json" \
  -d '{"query": "employment", "limit": 3}'
```

**Verify:**
- [ ] Different queries return relevant results
- [ ] No results crash the system (returns empty array)
- [ ] Limit parameter works (max 3 results returned)

---

## **Test 10: View Audit Logs**

**Command:**
```bash
curl http://localhost:5000/api/logs?page=1&per_page=10
```

**Expected Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "crawl_session_id": "abc123",
      "action": "INSERT",
      "law_id": 1,
      "url": "https://labour.gov.in/...",
      "source": "Ministry of Labour",
      "status": "success",
      "message": "Inserted new law",
      "timestamp": "2025-11-28T16:05:00"
    }
  ],
  "total": 5,
  "pages": 1,
  "current_page": 1
}
```

**Verify:**
- [ ] Logs show INSERT/UPDATE/SKIP actions
- [ ] Each log has status (success/error)
- [ ] Message field describes what happened
- [ ] Timestamps are accurate

---

## **Test 11: View Crawl Sessions**

**Command:**
```bash
curl http://localhost:5000/api/sessions
```

**Expected Response:**
```json
{
  "sessions": [
    {
      "session_id": "abc123",
      "status": "completed",
      "started_at": "2025-11-28T16:05:00",
      "completed_at": "2025-11-28T16:05:45",
      "total_pages": 5,
      "inserted": 2,
      "updated": 0,
      "skipped": 3,
      "errors": 0
    }
  ]
}
```

**Verify:**
- [ ] Session shows statistics (inserted, updated, skipped, errors)
- [ ] Total = inserted + updated + skipped + errors
- [ ] completed_at is after started_at
- [ ] Status is "completed" or "running"

---

## **Test 12: Database Verification**

**Connect to PostgreSQL:**
```bash
psql -U postgres -d labour_laws_db
```

**Check laws table:**
```sql
SELECT id, title, category, summary FROM labour_laws LIMIT 5;
```

**Verify:**
- [ ] Laws table has data
- [ ] Summary column is NOT NULL (Groq worked!)
- [ ] Title and category are present

**Check audit logs:**
```sql
SELECT action, status, COUNT(*) FROM audit_logs GROUP BY action, status;
```

**Verify:**
- [ ] INSERT records exist
- [ ] Status mostly "success"
- [ ] Some "skipped" records (duplicates)

**Check embeddings stored:**
```sql
SELECT id, LENGTH(embedding) as embedding_size FROM labour_laws LIMIT 1;
```

**Verify:**
- [ ] Embedding column has data (length > 100)

---

## **Test 13: Duplicate Detection (Semantic Matching)**

**Verify the system correctly handles duplicates:**

1. Run a crawl:
```bash
curl -X POST http://localhost:5000/api/crawl/start
```

2. Wait for completion, check stats:
```bash
curl http://localhost:5000/api/stats
```
Note the inserted count.

3. Run crawl again immediately:
```bash
curl -X POST http://localhost:5000/api/crawl/start
```

4. Wait 30 seconds, check stats again:
```bash
curl http://localhost:5000/api/stats
```

**Verify:**
- [ ] Second crawl doesn't increase total_laws (duplicates skipped)
- [ ] Logs show "SKIP" actions
- [ ] Inserted count from second crawl = 0 or very low

---

## **Test 14: CLI Testing**

**Test crawl command:**
```bash
python orchestrator.py crawl
```

**Expected output:**
```
============================================================
Starting Labour Law Crawl Job
Timestamp: 2025-11-28T16:05:00.123456
============================================================
Found 5 items to process
Processing item 1/5: https://labour.gov.in/...
...
============================================================
Crawl Job Completed
Session ID: abc123
Total Processed: 5
Inserted: 2
Updated: 0
Skipped: 3
Errors: 0
============================================================
```

**Verify:**
- [ ] Crawl runs to completion
- [ ] Statistics match database

**Test search command:**
```bash
python orchestrator.py search "minimum wage" --limit 3
```

**Expected output:**
```
======================================================================
Search Results for: 'minimum wage'
======================================================================

ID: 1 | Similarity: 0.9234
Title: Labour Code on Wages
Category: Act
Summary: This code establishes...
----------------------------------------------------------------------
```

**Verify:**
- [ ] Search returns results
- [ ] Similarity scores display
- [ ] Results are relevant

**Test stats command:**
```bash
python orchestrator.py stats
```

**Expected output:**
```
==================================================
Labour Law Agent Statistics
==================================================
Total Laws in Database: 2
Total Crawl Sessions: 1

Last Crawl Session:
  Session ID: abc123
  Status: completed
  Inserted: 2
  Updated: 0
  Skipped: 3
  Errors: 0

Laws by Category:
  Act: 1
  Rule: 1
==================================================
```

**Verify:**
- [ ] Statistics match database
- [ ] Categories break down correctly

---

## **Test 15: Error Handling**

**Test invalid law ID:**
```bash
curl http://localhost:5000/api/laws/99999
```

**Expected:** 404 status with error message

**Verify:**
- [ ] Returns 404 status code
- [ ] Error message is clear

**Test invalid search (no query):**
```bash
curl -X POST http://localhost:5000/api/laws/search \
  -H "Content-Type: application/json" \
  -d '{"query": ""}'
```

**Expected:** 400 status with error

**Verify:**
- [ ] Returns 400 status code
- [ ] Message indicates query is required

---

## **Test 16: Groq Integration Verification**

**Check logs for Groq initialization:**
```bash
grep "Groq" logs/crawler_*.log
```

**Expected to find:**
```
Groq client initialized successfully
Successfully generated summary for: ...
```

**Verify:**
- [ ] Groq client initialized without errors
- [ ] Summaries generated for multiple laws

**Test without Groq key (optional):**
Remove GROQ_API_KEY from .env, restart app, run crawl

**Expected:**
- [ ] App still works (fallback to excerpt)
- [ ] Summary shows "[Auto-generated excerpt]"

---

## **Test 17: Load Testing (Optional)**

**Make multiple concurrent requests:**
```bash
for i in {1..10}; do curl http://localhost:5000/api/stats & done
```

**Verify:**
- [ ] All requests succeed
- [ ] No connection errors
- [ ] App doesn't crash

---

## **Test 18: Documentation Accuracy**

**Verify:**
- [ ] This testing guide matches actual API responses
- [ ] All endpoints return documented format
- [ ] Error codes match (400, 404, 500)
- [ ] Field names in responses match documentation

---

## **Final Verification Checklist**

```
✅ Web Dashboard loads and displays correctly
✅ Health check endpoint works
✅ Stats endpoint returns correct data
✅ Crawl can be triggered and completes
✅ Laws are stored in database
✅ Groq summaries are generated (not empty)
✅ Semantic search returns relevant results
✅ Audit logs track all operations
✅ Duplicate detection works (semantic matching)
✅ CLI commands work correctly
✅ Error handling is graceful
✅ Database schema is correct
✅ All required fields present in responses
✅ Pagination works
✅ Timestamps are accurate
```

---

## **Success Criteria**

The project is working correctly if:

1. **Crawling:** Laws can be fetched from labour.gov.in
2. **Summarization:** Each law has an AI-generated summary (not empty)
3. **Embeddings:** Laws have semantic embeddings stored
4. **Semantic Search:** Search by meaning, not just keywords
5. **Duplicate Detection:** Same law from different sources is recognized
6. **Database:** All data persists correctly
7. **Audit Trail:** Every action is logged
8. **Web UI:** Dashboard shows real-time statistics
9. **APIs:** All endpoints work as documented
10. **Error Handling:** Graceful errors with meaningful messages

---

## **Performance Benchmarks**

Expected performance:
- Single API request: < 100ms
- Search query: < 500ms
- Full crawl: 30-60 seconds
- Database insert: < 50ms

---

## **Testing Tools**

**Curl (Command line):**
- Already included, use examples in this guide

**Postman (Visual):**
- Import the endpoints into Postman
- Save requests for reuse

**Python (Automation):**
```python
import requests

# Test search
response = requests.post('http://localhost:5000/api/laws/search', 
    json={'query': 'minimum wage'})
print(response.json())
```

---

Done! Now reviewers can systematically test all features using this guide.
