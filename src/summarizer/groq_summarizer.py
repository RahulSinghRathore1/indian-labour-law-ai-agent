import os
from groq import Groq
from src.utils.logger import logger

class GroqSummarizer:
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.client = None
        self.model = 'llama-3.1-8b-instant'
        
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info("Groq client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
    
    def summarize(self, text, title=""):
        if not self.client:
            logger.warning("Groq client not initialized. Returning placeholder summary.")
            return self._generate_fallback_summary(text, title)
        
        if not text or len(text) < 100:
            return "Content too short to summarize."
        
        try:
            truncated_text = text[:8000] if len(text) > 8000 else text
            
            prompt = f"""You are a legal document summarizer specializing in Indian labour laws. 
Summarize the following law/regulation in a clear, factual manner.

IMPORTANT RULES:
1. Be factual - do not provide legal interpretation or advice
2. Maintain important legal definitions exactly as stated
3. Include key provisions, applicability, and effective dates if mentioned
4. Keep the summary concise but comprehensive (200-400 words)
5. Use bullet points for multiple provisions

Title: {title}

Content:
{truncated_text}

Summary:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise legal document summarizer. Provide factual summaries without interpretation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content
            logger.info(f"Successfully generated summary for: {title[:50]}...")
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._generate_fallback_summary(text, title)
    
    def summarize_batch(self, items):
        results = []
        
        for item in items:
            text = item.get('content', '')
            title = item.get('title', '')
            summary = self.summarize(text, title)
            results.append({
                **item,
                'summary': summary
            })
        
        return results
    
    def _generate_fallback_summary(self, text, title):
        if not text:
            return "No content available for summarization."
        
        sentences = text.split('.')
        first_sentences = '. '.join(sentences[:5]).strip()
        
        if len(first_sentences) > 500:
            first_sentences = first_sentences[:500] + "..."
        
        return f"[Auto-generated excerpt] {title}: {first_sentences}"

groq_summarizer = GroqSummarizer()
