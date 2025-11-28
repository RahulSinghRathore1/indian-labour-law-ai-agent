import re
import hashlib
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException
from src.utils.logger import logger

class TextProcessor:
    
    BOILERPLATE_PATTERNS = [
        r'copyright\s*©?\s*\d{4}',
        r'all rights reserved',
        r'privacy policy',
        r'terms of use',
        r'cookie policy',
        r'powered by',
        r'site map',
        r'contact us',
        r'follow us on',
        r'share on',
        r'print this page',
        r'download pdf',
        r'related links',
        r'quick links',
        r'important links',
        r'skip to main content',
        r'skip to navigation',
    ]
    
    def __init__(self):
        self.boilerplate_regex = re.compile(
            '|'.join(self.BOILERPLATE_PATTERNS),
            re.IGNORECASE
        )
    
    def clean_html(self, html_content):
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 
                         'aside', 'iframe', 'noscript', 'meta', 'link']):
            tag.decompose()
        
        for element in soup.find_all(class_=re.compile(
            r'(sidebar|menu|nav|footer|header|advertisement|banner|popup|modal)',
            re.IGNORECASE
        )):
            element.decompose()
        
        text = soup.get_text(separator=' ')
        
        return self.normalize_text(text)
    
    def normalize_text(self, text):
        if not text:
            return ""
        
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        text = re.sub(r'[ \t]+', ' ', text)
        
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        text = re.sub(r'[^\S\n]+', ' ', text)
        
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        text = re.sub(r'[–—]', '-', text)
        
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not self.boilerplate_regex.search(line):
                if len(line) > 20 or not re.match(r'^[\W\d\s]+$', line):
                    cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        return text.strip()
    
    def detect_language(self, text):
        if not text or len(text) < 50:
            return 'unknown'
        
        try:
            sample = text[:1000] if len(text) > 1000 else text
            lang = detect(sample)
            return lang
        except LangDetectException:
            logger.warning("Could not detect language")
            return 'unknown'
    
    def generate_content_hash(self, text):
        if not text:
            return ""
        
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def extract_metadata(self, html_content, url=""):
        metadata = {
            'title': '',
            'publication_date': None,
            'category': 'Unknown'
        }
        
        if not html_content:
            return metadata
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        if not metadata['title']:
            h1 = soup.find('h1')
            if h1:
                metadata['title'] = h1.get_text().strip()
        
        date_patterns = [
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
            r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b',
            r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
        ]
        
        text = soup.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['publication_date'] = match.group(1)
                break
        
        url_lower = url.lower()
        title_lower = metadata['title'].lower()
        
        if 'amendment' in url_lower or 'amendment' in title_lower:
            metadata['category'] = 'Amendment'
        elif 'notification' in url_lower or 'notification' in title_lower:
            metadata['category'] = 'Notification'
        elif 'rule' in url_lower or 'rules' in title_lower:
            metadata['category'] = 'Rule'
        elif 'act' in url_lower or 'act' in title_lower:
            metadata['category'] = 'Act'
        elif 'circular' in url_lower or 'circular' in title_lower:
            metadata['category'] = 'Circular'
        elif 'order' in url_lower or 'order' in title_lower:
            metadata['category'] = 'Order'
        
        return metadata
    
    def process(self, html_content, url=""):
        cleaned_text = self.clean_html(html_content)
        
        metadata = self.extract_metadata(html_content, url)
        
        language = self.detect_language(cleaned_text)
        
        content_hash = self.generate_content_hash(cleaned_text)
        
        return {
            'content': cleaned_text,
            'title': metadata['title'],
            'publication_date': metadata['publication_date'],
            'category': metadata['category'],
            'language': language,
            'content_hash': content_hash
        }

text_processor = TextProcessor()
