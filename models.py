from datetime import datetime
from src.database.db import db
import json

class LabourLaw(db.Model):
    __tablename__ = 'labour_laws'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    url = db.Column(db.String(1000), unique=True)
    source = db.Column(db.String(255))
    category = db.Column(db.String(100))
    publication_date = db.Column(db.Date)
    language = db.Column(db.String(50), default='en')
    embedding = db.Column(db.Text)
    content_hash = db.Column(db.String(64))
    version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_embedding(self, embedding_list):
        self.embedding = json.dumps(embedding_list)
    
    def get_embedding(self):
        if self.embedding:
            return json.loads(self.embedding)
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'url': self.url,
            'source': self.source,
            'category': self.category,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'language': self.language,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    crawl_session_id = db.Column(db.String(50))
    action = db.Column(db.String(50))
    law_id = db.Column(db.Integer, db.ForeignKey('labour_laws.id'), nullable=True)
    url = db.Column(db.String(1000))
    source = db.Column(db.String(255))
    status = db.Column(db.String(50))
    message = db.Column(db.Text)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    law = db.relationship('LabourLaw', backref='audit_logs')
    
    def set_details(self, details_dict):
        self.details = json.dumps(details_dict)
    
    def get_details(self):
        if self.details:
            return json.loads(self.details)
        return {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'crawl_session_id': self.crawl_session_id,
            'action': self.action,
            'law_id': self.law_id,
            'url': self.url,
            'source': self.source,
            'status': self.status,
            'message': self.message,
            'details': self.get_details(),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class CrawlSession(db.Model):
    __tablename__ = 'crawl_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(50), default='running')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    total_pages = db.Column(db.Integer, default=0)
    inserted = db.Column(db.Integer, default=0)
    updated = db.Column(db.Integer, default=0)
    skipped = db.Column(db.Integer, default=0)
    errors = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_pages': self.total_pages,
            'inserted': self.inserted,
            'updated': self.updated,
            'skipped': self.skipped,
            'errors': self.errors
        }
