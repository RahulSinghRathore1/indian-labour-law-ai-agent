from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import threading
from src.database.db import db
from models import LabourLaw, AuditLog, CrawlSession
from src.embeddings.embedding_service import embedding_service
from src.crawler.web_crawler import web_crawler
from src.database.upsert_service import upsert_service
from src.utils.logger import logger

api_bp = Blueprint('api', __name__)

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    try:
        total_laws = LabourLaw.query.count()
        total_sessions = CrawlSession.query.count()
        
        last_session = CrawlSession.query.order_by(
            CrawlSession.started_at.desc()
        ).first()
        
        last_crawl = None
        if last_session and last_session.started_at:
            last_crawl = last_session.started_at.strftime('%Y-%m-%d %H:%M')
        
        return jsonify({
            'total_laws': total_laws,
            'total_sessions': total_sessions,
            'last_crawl': last_crawl
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/laws', methods=['GET'])
def list_laws():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category')
        
        query = LabourLaw.query
        
        if category:
            query = query.filter_by(category=category)
        
        query = query.order_by(LabourLaw.updated_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        laws = [law.to_dict() for law in pagination.items]
        
        return jsonify({
            'laws': laws,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Error listing laws: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/laws/<int:law_id>', methods=['GET'])
def get_law(law_id):
    try:
        law = LabourLaw.query.get(law_id)
        
        if not law:
            return jsonify({'error': 'Law not found'}), 404
        
        return jsonify(law.to_dict())
    except Exception as e:
        logger.error(f"Error getting law {law_id}: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/laws/search', methods=['POST'])
def search_laws():
    try:
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        query_embedding = embedding_service.generate_embedding(query)
        
        if not query_embedding:
            return jsonify({'error': 'Failed to generate query embedding'}), 500
        
        laws = LabourLaw.query.all()
        
        results = []
        for law in laws:
            law_embedding = law.get_embedding()
            if law_embedding:
                similarity = embedding_service.calculate_similarity(
                    query_embedding, law_embedding
                )
                if similarity > 0.3:
                    result = law.to_dict()
                    result['similarity_score'] = round(similarity, 4)
                    results.append(result)
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        results = results[:limit]
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results)
        })
    except Exception as e:
        logger.error(f"Error searching laws: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/crawl/start', methods=['POST'])
def start_crawl():
    try:
        from main import app
        
        def run_crawl():
            with app.app_context():
                logger.info("Starting crawl job...")
                items = web_crawler.crawl_all()
                if items:
                    result = upsert_service.process_batch(items)
                    logger.info(f"Crawl completed: {result}")
                else:
                    logger.warning("No items found during crawl")
        
        thread = threading.Thread(target=run_crawl)
        thread.start()
        
        return jsonify({
            'message': 'Crawl started in background',
            'status': 'running'
        })
    except Exception as e:
        logger.error(f"Error starting crawl: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/crawl/status', methods=['GET'])
def crawl_status():
    try:
        session = CrawlSession.query.order_by(
            CrawlSession.started_at.desc()
        ).first()
        
        if not session:
            return jsonify({'message': 'No crawl sessions found'})
        
        return jsonify(session.to_dict())
    except Exception as e:
        logger.error(f"Error getting crawl status: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/crawl/url', methods=['POST'])
def crawl_single_url():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        item = web_crawler.crawl_url(url)
        
        if not item:
            return jsonify({'error': 'Failed to fetch URL'}), 400
        
        result = upsert_service.process_batch([item])
        
        return jsonify({
            'message': 'URL processed successfully',
            'result': result
        })
    except Exception as e:
        logger.error(f"Error crawling URL: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/logs', methods=['GET'])
def get_logs():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        session_id = request.args.get('session_id')
        action = request.args.get('action')
        
        query = AuditLog.query
        
        if session_id:
            query = query.filter_by(crawl_session_id=session_id)
        if action:
            query = query.filter_by(action=action)
        
        query = query.order_by(AuditLog.timestamp.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        logs = [log.to_dict() for log in pagination.items]
        
        return jsonify({
            'logs': logs,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions', methods=['GET'])
def get_sessions():
    try:
        sessions = CrawlSession.query.order_by(
            CrawlSession.started_at.desc()
        ).limit(20).all()
        
        return jsonify({
            'sessions': [s.to_dict() for s in sessions]
        })
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })
