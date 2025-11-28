import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import os
from src.utils.logger import logger

class EmbeddingService:
    _instance = None
    _vectorizer = None
    _corpus_vectors = None
    _corpus_texts = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if EmbeddingService._vectorizer is None:
            self._initialize_vectorizer()
    
    def _initialize_vectorizer(self):
        try:
            logger.info("Initializing TF-IDF vectorizer for embeddings")
            EmbeddingService._vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95
            )
            logger.info("TF-IDF vectorizer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vectorizer: {e}")
            raise
    
    def generate_embedding(self, text):
        if not text:
            return None
        
        try:
            text = text[:10000] if len(text) > 10000 else text
            
            if not EmbeddingService._corpus_texts:
                EmbeddingService._corpus_texts = [text]
                EmbeddingService._vectorizer.fit([text])
                embedding = EmbeddingService._vectorizer.transform([text]).toarray()[0]
            else:
                temp_texts = EmbeddingService._corpus_texts + [text]
                EmbeddingService._vectorizer.fit(temp_texts)
                embedding = EmbeddingService._vectorizer.transform([text]).toarray()[0]
            
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return self._generate_hash_embedding(text)
    
    def _generate_hash_embedding(self, text):
        try:
            words = text.lower().split()
            embedding = [0.0] * 256
            
            for i, word in enumerate(words[:500]):
                hash_val = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
                idx = hash_val % 256
                embedding[idx] += 1.0 / (i + 1)
            
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = [x / norm for x in embedding]
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating hash embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts):
        if not texts:
            return []
        
        try:
            truncated_texts = [t[:10000] if len(t) > 10000 else t for t in texts]
            
            EmbeddingService._vectorizer.fit(truncated_texts)
            embeddings = EmbeddingService._vectorizer.transform(truncated_texts).toarray()
            
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [self._generate_hash_embedding(t) for t in texts]
    
    def calculate_similarity(self, embedding1, embedding2):
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        try:
            vec1 = np.array(embedding1).reshape(1, -1)
            vec2 = np.array(embedding2).reshape(1, -1)
            
            min_len = min(vec1.shape[1], vec2.shape[1])
            vec1 = vec1[:, :min_len]
            vec2 = vec2[:, :min_len]
            
            if np.all(vec1 == 0) or np.all(vec2 == 0):
                return 0.0
            
            similarity = cosine_similarity(vec1, vec2)[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return self._jaccard_similarity(embedding1, embedding2)
    
    def _jaccard_similarity(self, embedding1, embedding2):
        try:
            set1 = set(i for i, v in enumerate(embedding1) if v > 0)
            set2 = set(i for i, v in enumerate(embedding2) if v > 0)
            
            if not set1 or not set2:
                return 0.0
            
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            
            return intersection / union if union > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating Jaccard similarity: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding, embeddings_list, threshold=0.85):
        if not query_embedding or not embeddings_list:
            return None, 0.0
        
        best_match_idx = None
        best_similarity = 0.0
        
        for idx, embedding in enumerate(embeddings_list):
            similarity = self.calculate_similarity(query_embedding, embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_idx = idx
        
        if best_similarity >= threshold:
            return best_match_idx, best_similarity
        
        return None, best_similarity

embedding_service = EmbeddingService()
