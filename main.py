import os
from src.database.db import db, create_app

app = create_app()

with app.app_context():
    import models
    db.create_all()

from src.api.routes import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Indian Labour Law AI Agent</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                min-height: 100vh;
                color: #fff;
            }
            .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
            header { text-align: center; margin-bottom: 60px; }
            h1 { font-size: 2.5rem; margin-bottom: 10px; color: #00d4ff; }
            .subtitle { color: #888; font-size: 1.1rem; }
            .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }
            .card {
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                padding: 30px;
                border: 1px solid rgba(255,255,255,0.1);
                transition: transform 0.3s, box-shadow 0.3s;
            }
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 40px rgba(0,212,255,0.2);
            }
            .card h3 { color: #00d4ff; margin-bottom: 15px; font-size: 1.3rem; }
            .card p { color: #aaa; line-height: 1.6; margin-bottom: 20px; }
            .endpoint {
                background: rgba(0,0,0,0.3);
                padding: 10px 15px;
                border-radius: 8px;
                font-family: monospace;
                font-size: 0.9rem;
                color: #00ff88;
                margin-bottom: 10px;
            }
            .stats {
                display: flex;
                justify-content: center;
                gap: 40px;
                margin: 40px 0;
                flex-wrap: wrap;
            }
            .stat {
                text-align: center;
                padding: 20px 40px;
                background: rgba(255,255,255,0.05);
                border-radius: 10px;
            }
            .stat-value { font-size: 2rem; color: #00d4ff; font-weight: bold; }
            .stat-label { color: #888; margin-top: 5px; }
            .features { margin-top: 60px; }
            .feature-list {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                list-style: none;
            }
            .feature-list li {
                padding: 15px 20px;
                background: rgba(0,212,255,0.1);
                border-radius: 8px;
                border-left: 3px solid #00d4ff;
            }
            footer {
                text-align: center;
                margin-top: 60px;
                padding: 20px;
                color: #666;
                border-top: 1px solid rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Indian Labour Law AI Agent</h1>
                <p class="subtitle">Automated crawler for Indian labour law updates with semantic analysis</p>
            </header>
            
            <div class="stats" id="stats">
                <div class="stat">
                    <div class="stat-value" id="totalLaws">-</div>
                    <div class="stat-label">Total Laws</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="lastCrawl">-</div>
                    <div class="stat-label">Last Crawl</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="totalSessions">-</div>
                    <div class="stat-label">Crawl Sessions</div>
                </div>
            </div>
            
            <div class="cards">
                <div class="card">
                    <h3>Search Laws</h3>
                    <p>Semantic search through all indexed labour laws using AI-powered similarity matching.</p>
                    <div class="endpoint">POST /api/laws/search</div>
                    <div class="endpoint">{"query": "minimum wage"}</div>
                </div>
                
                <div class="card">
                    <h3>Get Law Details</h3>
                    <p>Retrieve full text, summary, and metadata for a specific law by ID.</p>
                    <div class="endpoint">GET /api/laws/:id</div>
                </div>
                
                <div class="card">
                    <h3>Trigger Crawl</h3>
                    <p>Manually trigger a new crawl session to fetch latest law updates.</p>
                    <div class="endpoint">POST /api/crawl/start</div>
                </div>
                
                <div class="card">
                    <h3>View Audit Logs</h3>
                    <p>Check crawl history, decisions made, and any errors encountered.</p>
                    <div class="endpoint">GET /api/logs</div>
                </div>
            </div>
            
            <div class="features">
                <h2 style="text-align: center; margin-bottom: 30px; color: #00d4ff;">Key Features</h2>
                <ul class="feature-list">
                    <li>Semantic duplicate detection using embeddings</li>
                    <li>LLM-powered law summarization via Groq API</li>
                    <li>Smart upsert logic (Insert/Update/Skip)</li>
                    <li>Comprehensive audit logging</li>
                    <li>Rate-limited, reliable crawling</li>
                    <li>PostgreSQL database with versioning</li>
                </ul>
            </div>
            
            <footer>
                <p>Built for crawling official Indian labour law sources</p>
            </footer>
        </div>
        
        <script>
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('totalLaws').textContent = data.total_laws || 0;
                    document.getElementById('totalSessions').textContent = data.total_sessions || 0;
                    document.getElementById('lastCrawl').textContent = data.last_crawl || 'Never';
                })
                .catch(() => {
                    document.getElementById('totalLaws').textContent = '0';
                    document.getElementById('totalSessions').textContent = '0';
                    document.getElementById('lastCrawl').textContent = 'Never';
                });
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
