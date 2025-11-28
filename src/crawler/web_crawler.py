import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import trafilatura
from src.utils.logger import logger

class WebCrawler:
    
    SOURCES = [
        {
            'name': 'Ministry of Labour - Acts',
            'url': 'https://labour.gov.in/acts',
            'type': 'index'
        },
        {
            'name': 'Ministry of Labour - Rules',
            'url': 'https://labour.gov.in/rules',
            'type': 'index'
        },
        {
            'name': 'Ministry of Labour - Whats New',
            'url': 'https://labour.gov.in/whatsnew',
            'type': 'index'
        },
        {
            'name': 'Labour Codes',
            'url': 'https://labour.gov.in/labour-codes',
            'type': 'index'
        }
    ]
    
    def __init__(self, max_retries=3, timeout=30, rate_limit_delay=2):
        self.max_retries = max_retries
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
    
    def fetch_page(self, url):
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1})")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                time.sleep(self.rate_limit_delay)
                
                return {
                    'success': True,
                    'url': url,
                    'content': response.text,
                    'status_code': response.status_code
                }
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP error {e.response.status_code} for {url}")
                if e.response.status_code == 404:
                    return {'success': False, 'url': url, 'error': 'Page not found'}
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error for {url}: {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)
        
        return {'success': False, 'url': url, 'error': f'Failed after {self.max_retries} attempts'}
    
    def extract_content(self, html, url):
        try:
            extracted = trafilatura.extract(
                html,
                include_tables=True,
                include_links=True,
                include_images=False,
                output_format='txt'
            )
            
            if extracted and len(extracted) > 100:
                return extracted
            
            soup = BeautifulSoup(html, 'html.parser')
            
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            main_content = soup.find('main') or soup.find(class_='content') or soup.find('article')
            
            if main_content:
                return main_content.get_text(separator='\n', strip=True)
            
            return soup.get_text(separator='\n', strip=True)
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return ""
    
    def extract_links(self, html, base_url):
        links = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                text = a_tag.get_text(strip=True)
                
                if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    continue
                
                full_url = urljoin(base_url, href)
                
                parsed = urlparse(full_url)
                if not parsed.scheme or not parsed.netloc:
                    continue
                
                lower_href = href.lower()
                lower_text = text.lower()
                
                is_relevant = any([
                    'act' in lower_href or 'act' in lower_text,
                    'rule' in lower_href or 'rule' in lower_text,
                    'notification' in lower_href or 'notification' in lower_text,
                    'amendment' in lower_href or 'amendment' in lower_text,
                    'circular' in lower_href or 'circular' in lower_text,
                    'order' in lower_href or 'order' in lower_text,
                    'labour' in lower_href or 'labour' in lower_text,
                    'labor' in lower_href or 'labor' in lower_text,
                    'wage' in lower_href or 'wage' in lower_text,
                    'worker' in lower_href or 'worker' in lower_text,
                    '.pdf' in lower_href,
                    'gazette' in lower_href or 'gazette' in lower_text,
                ])
                
                if is_relevant:
                    links.append({
                        'url': full_url,
                        'text': text,
                        'is_pdf': '.pdf' in lower_href
                    })
            
            return links
            
        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {e}")
            return []
    
    def crawl_source(self, source):
        results = []
        
        logger.info(f"Crawling source: {source['name']}")
        
        page_result = self.fetch_page(source['url'])
        
        if not page_result['success']:
            logger.error(f"Failed to fetch {source['url']}: {page_result.get('error')}")
            return results
        
        if source['type'] == 'index':
            links = self.extract_links(page_result['content'], source['url'])
            logger.info(f"Found {len(links)} relevant links from {source['name']}")
            
            for link in links[:20]:
                if link['is_pdf']:
                    results.append({
                        'url': link['url'],
                        'title': link['text'],
                        'content': f"[PDF Document] {link['text']}",
                        'source': source['name'],
                        'is_pdf': True
                    })
                else:
                    sub_result = self.fetch_page(link['url'])
                    if sub_result['success']:
                        content = self.extract_content(sub_result['content'], link['url'])
                        if content and len(content) > 100:
                            results.append({
                                'url': link['url'],
                                'html': sub_result['content'],
                                'content': content,
                                'source': source['name'],
                                'is_pdf': False
                            })
        else:
            content = self.extract_content(page_result['content'], source['url'])
            if content and len(content) > 100:
                results.append({
                    'url': source['url'],
                    'html': page_result['content'],
                    'content': content,
                    'source': source['name'],
                    'is_pdf': False
                })
        
        return results
    
    def crawl_all(self):
        all_results = []
        
        for source in self.SOURCES:
            try:
                results = self.crawl_source(source)
                all_results.extend(results)
                logger.info(f"Collected {len(results)} items from {source['name']}")
            except Exception as e:
                logger.error(f"Error crawling {source['name']}: {e}")
        
        logger.info(f"Total items crawled: {len(all_results)}")
        return all_results
    
    def crawl_url(self, url):
        result = self.fetch_page(url)
        
        if not result['success']:
            return None
        
        content = self.extract_content(result['content'], url)
        
        return {
            'url': url,
            'html': result['content'],
            'content': content,
            'source': 'Manual',
            'is_pdf': url.lower().endswith('.pdf')
        }

web_crawler = WebCrawler()
