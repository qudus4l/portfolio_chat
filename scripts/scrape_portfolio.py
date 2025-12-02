#!/usr/bin/env python3
"""
Comprehensive Portfolio Website Scraper

This script scrapes ALL content from Qudus's portfolio website including:
- Main page sections (Home, About, Projects, Skills, Work Experience, Contact)
- Individual project detail pages  
- Individual work experience detail pages
- All text content, project descriptions, skills, etc.
"""

from typing import List, Dict, Set, Optional
import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import time
import logging
from langchain_core.documents import Document
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PortfolioScraper:
    """Comprehensive scraper for Qudus's portfolio website."""
    
    def __init__(self, base_url: str = "http://www.qudus4l.tech"):
        """Initialize the portfolio scraper.
        
        Args:
            base_url: Base URL of the portfolio website
        """
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def scrape_all_content(self) -> List[Document]:
        """Scrape all content from the portfolio website.
        
        Returns:
            List of Document objects containing all scraped content
        """
        logger.info("Starting comprehensive portfolio scraping...")
        documents = []
        
        try:
            # 1. Scrape main page with all sections
            main_docs = self._scrape_main_page()
            documents.extend(main_docs)
            logger.info(f"Scraped {len(main_docs)} sections from main page")
            
            # 2. Discover and scrape all project detail pages
            project_urls = self._discover_project_urls()
            for url in project_urls:
                if url not in self.visited_urls:
                    project_docs = self._scrape_project_page(url)
                    documents.extend(project_docs)
                    self.visited_urls.add(url)
                    time.sleep(0.5)  # Be respectful
            
            logger.info(f"Scraped {len(project_urls)} project detail pages")
            
            # 3. Discover and scrape all work experience detail pages  
            work_urls = self._discover_work_urls()
            for url in work_urls:
                if url not in self.visited_urls:
                    work_docs = self._scrape_work_page(url)
                    documents.extend(work_docs)
                    self.visited_urls.add(url)
                    time.sleep(0.5)  # Be respectful
                    
            logger.info(f"Scraped {len(work_urls)} work experience detail pages")
            
            # 4. Extract GitHub project information
            github_projects = self._extract_github_projects()
            documents.extend(github_projects)
            logger.info(f"Extracted {len(github_projects)} GitHub project references")
            
            logger.info(f"Total documents scraped: {len(documents)}")
            return documents
            
        except Exception as e:
            logger.error(f"Error during portfolio scraping: {str(e)}")
            return documents
    
    def _scrape_main_page(self) -> List[Document]:
        """Scrape all sections from the main portfolio page.
        
        Returns:
            List of Document objects for each main page section
        """
        documents = []
        
        try:
            response = self._get_page(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract each major section separately for better context
            sections_to_scrape = [
                {'id': 'hero', 'name': 'Hero/Introduction'},
                {'id': 'about', 'name': 'About'},
                {'id': 'projects', 'name': 'Projects Overview'},
                {'id': 'work-experience', 'name': 'Work Experience'},
                {'id': 'skills', 'name': 'Skills'},
                {'id': 'contact', 'name': 'Contact'}
            ]
            
            for section_info in sections_to_scrape:
                section_doc = self._extract_section_content(soup, section_info)
                if section_doc:
                    documents.append(section_doc)
            
            # Also extract any additional content not in specific sections
            general_content = self._extract_general_content(soup)
            if general_content:
                documents.append(general_content)
                
        except Exception as e:
            logger.error(f"Error scraping main page: {str(e)}")
            
        return documents
    
    def _extract_section_content(self, soup: BeautifulSoup, section_info: Dict) -> Optional[Document]:
        """Extract content from a specific section of the main page.
        
        Args:
            soup: BeautifulSoup object of the main page
            section_info: Dictionary with section id and name
            
        Returns:
            Document object with section content or None
        """
        section_id = section_info['id']
        section_name = section_info['name']
        
        # Try different selectors to find the section
        section = (soup.find('section', {'id': section_id}) or 
                  soup.find('div', {'id': section_id}) or
                  soup.find('section', class_=section_id) or
                  soup.find('div', class_=section_id))
        
        if not section:
            # For hero section, try finding it by class
            if section_id == 'hero':
                section = soup.find('section', class_='hero')
                
        if section:
            # Clean and extract text content
            content = self._clean_text_content(section.get_text())
            
            # Also extract any structured data (lists, headings, etc.)
            structured_content = self._extract_structured_content(section)
            
            full_content = f"=== {section_name} Section ===\n\n{content}"
            if structured_content:
                full_content += f"\n\nStructured Information:\n{structured_content}"
            
            return Document(
                page_content=full_content,
                metadata={
                    "source": "portfolio_main_page",
                    "section": section_id,
                    "section_name": section_name,
                    "url": self.base_url
                }
            )
        
        return None
    
    def _extract_structured_content(self, section: Tag) -> str:
        """Extract structured content like lists, headings, etc.
        
        Args:
            section: BeautifulSoup Tag object
            
        Returns:
            Formatted structured content
        """
        structured = []
        
        # Extract headings
        for heading in section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = heading.name[1]  # Get number from h1, h2, etc.
            text = self._clean_text_content(heading.get_text())
            if text:
                structured.append(f"{'#' * int(level)} {text}")
        
        # Extract lists
        for ul in section.find_all('ul'):
            structured.append("List:")
            for li in ul.find_all('li'):
                text = self._clean_text_content(li.get_text())
                if text:
                    structured.append(f"  • {text}")
        
        # Extract any data attributes or special content
        for elem in section.find_all(attrs={"data-skill": True}):
            skill = elem.get('data-skill')
            if skill:
                structured.append(f"Skill: {skill}")
                
        return "\n".join(structured)
    
    def _extract_general_content(self, soup: BeautifulSoup) -> Optional[Document]:
        """Extract any additional general content from the page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Document with general content or None
        """
        # Get page title and meta description
        title = soup.find('title')
        title_text = title.get_text() if title else ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        desc_text = meta_desc.get('content') if meta_desc else ""
        
        # Extract any additional text content not in main sections
        body_text = soup.find('body')
        if body_text:
            all_text = self._clean_text_content(body_text.get_text())
            
            content = f"=== Portfolio Website General Information ===\n\n"
            content += f"Title: {title_text}\n"
            if desc_text:
                content += f"Description: {desc_text}\n"
            content += f"\nFull page context for reference:\n{all_text[:2000]}..."  # Limit to avoid duplication
            
            return Document(
                page_content=content,
                metadata={
                    "source": "portfolio_general",
                    "url": self.base_url,
                    "type": "general_context"
                }
            )
        
        return None
    
    def _extract_github_projects(self) -> List[Document]:
        """Extract GitHub project information from the portfolio.
        
        Returns:
            List of Document objects with GitHub project info
        """
        documents = []
        
        try:
            response = self._get_page(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all GitHub links in the projects section
            projects_section = soup.find('section', {'id': 'projects'})
            if projects_section:
                github_links = []
                for a in projects_section.find_all('a', href=True):
                    href = a['href']
                    if 'github.com' in href and 'qudus4l' in href:
                        github_links.append(href)
                
                # Create a document with all GitHub project references
                if github_links:
                    content = "=== GitHub Projects Referenced in Portfolio ===\n\n"
                    content += "Projects showcased in the portfolio with GitHub repositories:\n\n"
                    
                    for link in github_links:
                        # Extract project name from URL
                        project_name = link.split('/')[-1].replace('.git', '').replace('-', ' ').title()
                        content += f"• {project_name}: {link}\n"
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "source": "portfolio_github_projects",
                            "type": "project_references",
                            "url": self.base_url
                        }
                    ))
                    
        except Exception as e:
            logger.error(f"Error extracting GitHub projects: {str(e)}")
            
        return documents
    
    def _discover_project_urls(self) -> List[str]:
        """Discover all project detail page URLs.
        
        Returns:
            List of project detail page URLs
        """
        project_urls = []
        
        try:
            response = self._get_page(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links to project detail pages
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'project-details/' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in project_urls:
                        project_urls.append(full_url)
                        
        except Exception as e:
            logger.error(f"Error discovering project URLs: {str(e)}")
        
        # If no URLs found via scraping, use known project URLs
        if not project_urls:
            logger.info("No project URLs found via scraping, using known project URLs")
            known_projects = [
                "thesispen-ai.html",
                "darth.html", 
                "brainifi.html",
                "ai-therapist.html",
                "neural-style-transfer.html",
                "mnist.html",
                "fake-news.html",
                "flower-classifier.html",
                "dog-breed-classifier.html"
            ]
            
            for project in known_projects:
                full_url = f"{self.base_url}/project-details/{project}"
                project_urls.append(full_url)
        
        logger.info(f"Discovered {len(project_urls)} project URLs")
        return project_urls
    
    def _discover_work_urls(self) -> List[str]:
        """Discover all work experience detail page URLs.
        
        Returns:
            List of work experience detail page URLs
        """
        work_urls = []
        
        try:
            response = self._get_page(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links to work detail pages
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'work-details/' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in work_urls:
                        work_urls.append(full_url)
                        
        except Exception as e:
            logger.error(f"Error discovering work URLs: {str(e)}")
        
        # If no URLs found via scraping, use known work URLs
        if not work_urls:
            logger.info("No work URLs found via scraping, using known work URLs")
            known_work = [
                "auntypelz-ai.html",
                "auto-agentic-ai.html",
                "customer-success-chatbot.html",
                "arabic-ocr.html",
                "med-llm.html"
            ]
            
            for work in known_work:
                full_url = f"{self.base_url}/work-details/{work}"
                work_urls.append(full_url)
        
        logger.info(f"Discovered {len(work_urls)} work URLs")        
        return work_urls
    
    def _scrape_project_page(self, url: str) -> List[Document]:
        """Scrape a project detail page.
        
        Args:
            url: URL of the project detail page
            
        Returns:
            List of Document objects with project information
        """
        documents = []
        
        try:
            response = self._get_page(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract project name from URL or title
            project_name = self._extract_page_name(url, soup)
            
            # Get all text content
            content = self._clean_text_content(soup.get_text())
            
            # Extract structured information
            structured_info = self._extract_project_details(soup)
            
            full_content = f"=== Project: {project_name} ===\n\n{content}"
            if structured_info:
                full_content += f"\n\nProject Details:\n{structured_info}"
            
            documents.append(Document(
                page_content=full_content,
                metadata={
                    "source": "portfolio_project",
                    "project_name": project_name,
                    "url": url,
                    "type": "project_detail"
                }
            ))
            
        except Exception as e:
            logger.error(f"Error scraping project page {url}: {str(e)}")
            
        return documents
    
    def _scrape_work_page(self, url: str) -> List[Document]:
        """Scrape a work experience detail page.
        
        Args:
            url: URL of the work experience detail page
            
        Returns:
            List of Document objects with work experience information
        """
        documents = []
        
        try:
            response = self._get_page(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract work experience name from URL or title
            work_name = self._extract_page_name(url, soup)
            
            # Get all text content
            content = self._clean_text_content(soup.get_text())
            
            # Extract structured information
            structured_info = self._extract_work_details(soup)
            
            full_content = f"=== Work Experience: {work_name} ===\n\n{content}"
            if structured_info:
                full_content += f"\n\nWork Details:\n{structured_info}"
            
            documents.append(Document(
                page_content=full_content,
                metadata={
                    "source": "portfolio_work",
                    "work_name": work_name,
                    "url": url,
                    "type": "work_detail"
                }
            ))
            
        except Exception as e:
            logger.error(f"Error scraping work page {url}: {str(e)}")
            
        return documents
    
    def _extract_project_details(self, soup: BeautifulSoup) -> str:
        """Extract structured project details.
        
        Args:
            soup: BeautifulSoup object of project page
            
        Returns:
            Formatted project details
        """
        details = []
        
        # Look for common project detail elements
        for elem in soup.find_all(['div', 'section', 'span'], class_=re.compile(r'(tech|skill|tool|language|framework)', re.I)):
            text = self._clean_text_content(elem.get_text())
            if text:
                details.append(f"Technology/Tool: {text}")
        
        # Extract any lists
        for ul in soup.find_all('ul'):
            details.append("Features/Details:")
            for li in ul.find_all('li'):
                text = self._clean_text_content(li.get_text())
                if text:
                    details.append(f"  • {text}")
        
        return "\n".join(details)
    
    def _extract_work_details(self, soup: BeautifulSoup) -> str:
        """Extract structured work experience details.
        
        Args:
            soup: BeautifulSoup object of work page
            
        Returns:
            Formatted work details
        """
        details = []
        
        # Look for common work detail elements
        for elem in soup.find_all(['div', 'section', 'span'], class_=re.compile(r'(role|position|company|duration|responsibility)', re.I)):
            text = self._clean_text_content(elem.get_text())
            if text:
                details.append(f"Work Info: {text}")
        
        # Extract any achievement lists
        for ul in soup.find_all('ul'):
            details.append("Responsibilities/Achievements:")
            for li in ul.find_all('li'):
                text = self._clean_text_content(li.get_text())
                if text:
                    details.append(f"  • {text}")
        
        return "\n".join(details)
    
    def _extract_page_name(self, url: str, soup: BeautifulSoup) -> str:
        """Extract page name from URL or page title.
        
        Args:
            url: Page URL
            soup: BeautifulSoup object of the page
            
        Returns:
            Clean page name
        """
        # Try to get from title tag
        title = soup.find('title')
        if title:
            title_text = self._clean_text_content(title.get_text())
            if title_text and title_text != "Qudus Abolade":
                return title_text
        
        # Extract from URL
        path = urlparse(url).path
        name = path.split('/')[-1].replace('.html', '').replace('-', ' ').title()
        return name or "Unknown Page"
    
    def _clean_text_content(self, text: str) -> str:
        """Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common navigation/footer text that's not useful
        noise_patterns = [
            r'Skip to main content',
            r'Toggle navigation',
            r'Copyright.*',
            r'All rights reserved.*',
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _get_page(self, url: str) -> requests.Response:
        """Get a web page with error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            Response object
            
        Raises:
            Exception: If page cannot be fetched
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise


def scrape_portfolio_website(base_url: str = "http://www.qudus4l.tech") -> List[Document]:
    """Main function to scrape the entire portfolio website.
    
    Args:
        base_url: Base URL of the portfolio website
        
    Returns:
        List of Document objects containing all scraped content
    """
    scraper = PortfolioScraper(base_url)
    return scraper.scrape_all_content()


if __name__ == "__main__":
    # Test the scraper
    documents = scrape_portfolio_website()
    print(f"\nScraping completed! Total documents: {len(documents)}")
    
    for doc in documents[:3]:  # Show first 3 for testing
        print(f"\n--- {doc.metadata.get('source', 'Unknown')} ---")
        print(f"Content preview: {doc.page_content[:200]}...")
