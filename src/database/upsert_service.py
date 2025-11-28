from datetime import datetime
from src.database.db import db
from models import LabourLaw, AuditLog, CrawlSession
from src.embeddings.embedding_service import embedding_service
from src.preprocessor.text_processor import text_processor
from src.summarizer.groq_summarizer import groq_summarizer
from src.utils.logger import logger
import uuid

class UpsertService:
    
    def __init__(self, similarity_threshold=0.85, content_similarity_threshold=0.95):
        self.similarity_threshold = similarity_threshold
        self.content_similarity_threshold = content_similarity_threshold
    
    def create_session(self):
        session_id = str(uuid.uuid4())[:8]
        
        crawl_session = CrawlSession(
            session_id=session_id,
            status='running',
            started_at=datetime.utcnow()
        )
        db.session.add(crawl_session)
        db.session.commit()
        
        return session_id
    
    def complete_session(self, session_id, stats):
        session = CrawlSession.query.filter_by(session_id=session_id).first()
        if session:
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            session.total_pages = stats.get('total', 0)
            session.inserted = stats.get('inserted', 0)
            session.updated = stats.get('updated', 0)
            session.skipped = stats.get('skipped', 0)
            session.errors = stats.get('errors', 0)
            db.session.commit()
    
    def log_action(self, session_id, action, url, source, status, message, law_id=None, details=None):
        log = AuditLog(
            crawl_session_id=session_id,
            action=action,
            law_id=law_id,
            url=url,
            source=source,
            status=status,
            message=message
        )
        if details:
            log.set_details(details)
        db.session.add(log)
        db.session.commit()
    
    def find_similar_law(self, embedding):
        existing_laws = LabourLaw.query.all()
        
        if not existing_laws:
            return None, 0.0
        
        best_match = None
        best_similarity = 0.0
        
        for law in existing_laws:
            law_embedding = law.get_embedding()
            if law_embedding:
                similarity = embedding_service.calculate_similarity(embedding, law_embedding)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = law
        
        if best_similarity >= self.similarity_threshold:
            return best_match, best_similarity
        
        return None, best_similarity
    
    def process_item(self, item, session_id):
        url = item.get('url', '')
        source = item.get('source', 'Unknown')
        
        try:
            processed = text_processor.process(
                item.get('html', item.get('content', '')),
                url
            )
            
            content = processed['content']
            if not content or len(content) < 100:
                self.log_action(
                    session_id, 'SKIP', url, source, 'skipped',
                    'Content too short or empty'
                )
                return 'skipped'
            
            embedding = embedding_service.generate_embedding(content)
            if not embedding:
                self.log_action(
                    session_id, 'ERROR', url, source, 'error',
                    'Failed to generate embedding'
                )
                return 'error'
            
            existing_by_url = LabourLaw.query.filter_by(url=url).first()
            
            if existing_by_url:
                if existing_by_url.content_hash == processed['content_hash']:
                    self.log_action(
                        session_id, 'SKIP', url, source, 'skipped',
                        'Content unchanged (same hash)',
                        law_id=existing_by_url.id
                    )
                    return 'skipped'
                
                summary = groq_summarizer.summarize(content, processed['title'])
                
                existing_by_url.content = content
                existing_by_url.summary = summary
                existing_by_url.title = processed['title'] or existing_by_url.title
                existing_by_url.category = processed['category']
                existing_by_url.language = processed['language']
                existing_by_url.content_hash = processed['content_hash']
                existing_by_url.set_embedding(embedding)
                existing_by_url.version += 1
                existing_by_url.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                self.log_action(
                    session_id, 'UPDATE', url, source, 'success',
                    f'Updated existing law (version {existing_by_url.version})',
                    law_id=existing_by_url.id
                )
                return 'updated'
            
            similar_law, similarity = self.find_similar_law(embedding)
            
            if similar_law:
                if similar_law.content_hash == processed['content_hash']:
                    self.log_action(
                        session_id, 'SKIP', url, source, 'skipped',
                        f'Semantically similar law exists (similarity: {similarity:.2f})',
                        law_id=similar_law.id
                    )
                    return 'skipped'
                
                summary = groq_summarizer.summarize(content, processed['title'])
                
                similar_law.content = content
                similar_law.summary = summary
                similar_law.title = processed['title'] or similar_law.title
                similar_law.url = url
                similar_law.category = processed['category']
                similar_law.language = processed['language']
                similar_law.content_hash = processed['content_hash']
                similar_law.set_embedding(embedding)
                similar_law.version += 1
                similar_law.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                self.log_action(
                    session_id, 'UPDATE', url, source, 'success',
                    f'Updated similar law (similarity: {similarity:.2f}, version {similar_law.version})',
                    law_id=similar_law.id
                )
                return 'updated'
            
            summary = groq_summarizer.summarize(content, processed['title'])
            
            new_law = LabourLaw(
                title=processed['title'] or 'Untitled Law',
                content=content,
                summary=summary,
                url=url,
                source=source,
                category=processed['category'],
                language=processed['language'],
                content_hash=processed['content_hash']
            )
            new_law.set_embedding(embedding)
            
            db.session.add(new_law)
            db.session.commit()
            
            self.log_action(
                session_id, 'INSERT', url, source, 'success',
                'Inserted new law',
                law_id=new_law.id
            )
            return 'inserted'
                
        except Exception as e:
            logger.error(f"Error processing item {url}: {e}")
            self.log_action(
                session_id, 'ERROR', url, source, 'error',
                str(e)
            )
            return 'error'
    
    def process_batch(self, items):
        session_id = self.create_session()
        
        stats = {
            'total': len(items),
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        logger.info(f"Starting batch processing with session {session_id}")
        
        for i, item in enumerate(items):
            logger.info(f"Processing item {i+1}/{len(items)}: {item.get('url', 'unknown')}")
            
            result = self.process_item(item, session_id)
            stats[result] = stats.get(result, 0) + 1
        
        self.complete_session(session_id, stats)
        
        logger.info(f"Batch processing completed: {stats}")
        
        return {
            'session_id': session_id,
            'stats': stats
        }

upsert_service = UpsertService()
