import argparse
import sys
from datetime import datetime
from src.crawler.web_crawler import web_crawler
from src.database.upsert_service import upsert_service
from src.utils.logger import logger
from main import app
from src.database.db import db
from models import LabourLaw, CrawlSession, AuditLog

def run_crawl():
    logger.info("="*60)
    logger.info("Starting Labour Law Crawl Job")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("="*60)
    
    with app.app_context():
        items = web_crawler.crawl_all()
        
        if not items:
            logger.warning("No items found during crawl")
            return
        
        logger.info(f"Found {len(items)} items to process")
        
        result = upsert_service.process_batch(items)
        
        logger.info("="*60)
        logger.info("Crawl Job Completed")
        logger.info(f"Session ID: {result['session_id']}")
        logger.info(f"Total Processed: {result['stats']['total']}")
        logger.info(f"Inserted: {result['stats']['inserted']}")
        logger.info(f"Updated: {result['stats']['updated']}")
        logger.info(f"Skipped: {result['stats']['skipped']}")
        logger.info(f"Errors: {result['stats']['errors']}")
        logger.info("="*60)

def crawl_url(url):
    logger.info(f"Crawling single URL: {url}")
    
    with app.app_context():
        item = web_crawler.crawl_url(url)
        
        if not item:
            logger.error(f"Failed to fetch URL: {url}")
            return
        
        result = upsert_service.process_batch([item])
        
        logger.info(f"Result: {result}")

def show_stats():
    with app.app_context():
        total_laws = LabourLaw.query.count()
        total_sessions = CrawlSession.query.count()
        
        last_session = CrawlSession.query.order_by(
            CrawlSession.started_at.desc()
        ).first()
        
        print("\n" + "="*50)
        print("Labour Law Agent Statistics")
        print("="*50)
        print(f"Total Laws in Database: {total_laws}")
        print(f"Total Crawl Sessions: {total_sessions}")
        
        if last_session:
            print(f"\nLast Crawl Session:")
            print(f"  Session ID: {last_session.session_id}")
            print(f"  Status: {last_session.status}")
            print(f"  Started: {last_session.started_at}")
            print(f"  Completed: {last_session.completed_at or 'N/A'}")
            print(f"  Inserted: {last_session.inserted}")
            print(f"  Updated: {last_session.updated}")
            print(f"  Skipped: {last_session.skipped}")
            print(f"  Errors: {last_session.errors}")
        
        by_category = db.session.query(
            LabourLaw.category, 
            db.func.count(LabourLaw.id)
        ).group_by(LabourLaw.category).all()
        
        if by_category:
            print(f"\nLaws by Category:")
            for category, count in by_category:
                print(f"  {category}: {count}")
        
        print("="*50 + "\n")

def list_laws(limit=10):
    with app.app_context():
        laws = LabourLaw.query.order_by(
            LabourLaw.updated_at.desc()
        ).limit(limit).all()
        
        print("\n" + "="*70)
        print(f"Recent Laws (showing {len(laws)})")
        print("="*70)
        
        for law in laws:
            print(f"\nID: {law.id}")
            print(f"Title: {law.title[:60]}..." if len(law.title) > 60 else f"Title: {law.title}")
            print(f"Category: {law.category}")
            print(f"Source: {law.source}")
            print(f"Updated: {law.updated_at}")
            print("-"*70)

def search_laws(query, limit=5):
    from src.embeddings.embedding_service import embedding_service
    
    with app.app_context():
        query_embedding = embedding_service.generate_embedding(query)
        
        if not query_embedding:
            print("Failed to generate query embedding")
            return
        
        laws = LabourLaw.query.all()
        
        results = []
        for law in laws:
            law_embedding = law.get_embedding()
            if law_embedding:
                similarity = embedding_service.calculate_similarity(
                    query_embedding, law_embedding
                )
                if similarity > 0.3:
                    results.append((law, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:limit]
        
        print("\n" + "="*70)
        print(f"Search Results for: '{query}'")
        print("="*70)
        
        if not results:
            print("No matching laws found.")
            return
        
        for law, score in results:
            print(f"\nID: {law.id} | Similarity: {score:.4f}")
            print(f"Title: {law.title[:60]}..." if len(law.title) > 60 else f"Title: {law.title}")
            print(f"Category: {law.category}")
            if law.summary:
                summary_preview = law.summary[:200] + "..." if len(law.summary) > 200 else law.summary
                print(f"Summary: {summary_preview}")
            print("-"*70)

def main():
    parser = argparse.ArgumentParser(
        description='Indian Labour Law AI Agent CLI'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    crawl_parser = subparsers.add_parser('crawl', help='Run a full crawl')
    
    url_parser = subparsers.add_parser('crawl-url', help='Crawl a single URL')
    url_parser.add_argument('url', help='URL to crawl')
    
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    
    list_parser = subparsers.add_parser('list', help='List recent laws')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of laws to show')
    
    search_parser = subparsers.add_parser('search', help='Search laws')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=5, help='Number of results')
    
    server_parser = subparsers.add_parser('server', help='Start the web server')
    
    args = parser.parse_args()
    
    if args.command == 'crawl':
        run_crawl()
    elif args.command == 'crawl-url':
        crawl_url(args.url)
    elif args.command == 'stats':
        show_stats()
    elif args.command == 'list':
        list_laws(args.limit)
    elif args.command == 'search':
        search_laws(args.query, args.limit)
    elif args.command == 'server':
        print("Starting web server...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
