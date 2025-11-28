from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import atexit
from src.crawler.web_crawler import web_crawler
from src.database.upsert_service import upsert_service
from src.utils.logger import logger
from main import app

scheduler = BackgroundScheduler()

def scheduled_crawl():
    logger.info(f"Scheduled crawl started at {datetime.utcnow().isoformat()}")
    
    try:
        with app.app_context():
            items = web_crawler.crawl_all()
            
            if items:
                result = upsert_service.process_batch(items)
                logger.info(f"Scheduled crawl completed: {result}")
            else:
                logger.warning("Scheduled crawl: No items found")
                
    except Exception as e:
        logger.error(f"Scheduled crawl failed: {e}")

def start_scheduler():
    scheduler.add_job(
        scheduled_crawl,
        trigger=CronTrigger(hour=2, minute=0),
        id='daily_crawl',
        name='Daily Labour Law Crawl',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started - Daily crawl scheduled for 2:00 AM UTC")
    
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

if __name__ == '__main__':
    start_scheduler()
    
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        stop_scheduler()
