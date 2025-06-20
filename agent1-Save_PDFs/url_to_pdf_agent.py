#!/usr/bin/env python3
"""
URL to PDF Agent
Reads URLs from text files and creates PDFs of each web page.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Optional
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pdfkit


class URLToPDFAgent:
    def __init__(self, output_dir: str = "pdf_output", headless: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.headless = headless
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('url_to_pdf_agent.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def read_urls_from_file(self, file_path: str) -> List[str]:
        """Read URLs from a text file, one URL per line."""
        urls = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if line.startswith('http://') or line.startswith('https://'):
                            urls.append(line)
                        else:
                            self.logger.warning(f"Invalid URL at line {line_num}: {line}")
            self.logger.info(f"Read {len(urls)} URLs from {file_path}")
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
        return urls

    def sanitize_filename(self, url: str) -> str:
        """Create a safe filename from URL."""
        filename = url.replace('https://', '').replace('http://', '')
        filename = filename.replace('/', '_').replace('?', '_').replace('&', '_')
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        return filename[:100] + '.pdf'

    def create_pdf_with_wkhtmltopdf(self, url: str, output_path: str) -> bool:
        """Create PDF using wkhtmltopdf."""
        try:
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,
                'javascript-delay': 2000,
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore'
            }
            
            pdfkit.from_url(url, output_path, options=options)
            self.logger.info(f"PDF created successfully: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error creating PDF with wkhtmltopdf for {url}: {e}")
            return False

    def create_pdf_with_selenium(self, url: str, output_path: str) -> bool:
        """Create PDF using Selenium (fallback method)."""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Print to PDF using Chrome's print functionality
                print_options = {
                    'landscape': False,
                    'displayHeaderFooter': False,
                    'printBackground': True,
                    'preferCSSPageSize': True,
                }
                
                pdf_data = driver.execute_cdp_cmd("Page.printToPDF", print_options)
                
                with open(output_path, 'wb') as f:
                    f.write(base64.b64decode(pdf_data['data']))
                
                self.logger.info(f"PDF created successfully with Selenium: {output_path}")
                return True
                
            finally:
                driver.quit()
                
        except Exception as e:
            self.logger.error(f"Error creating PDF with Selenium for {url}: {e}")
            return False

    def process_url(self, url: str) -> bool:
        """Process a single URL and create PDF."""
        filename = self.sanitize_filename(url)
        output_path = self.output_dir / filename
        
        self.logger.info(f"Processing URL: {url}")
        
        # Try wkhtmltopdf first, fallback to Selenium
        if self.create_pdf_with_wkhtmltopdf(url, str(output_path)):
            return True
        else:
            self.logger.info(f"Falling back to Selenium for {url}")
            return self.create_pdf_with_selenium(url, str(output_path))

    def process_file(self, file_path: str) -> None:
        """Process all URLs in a text file."""
        urls = self.read_urls_from_file(file_path)
        
        if not urls:
            self.logger.warning(f"No valid URLs found in {file_path}")
            return
        
        success_count = 0
        for url in urls:
            if self.process_url(url):
                success_count += 1
        
        self.logger.info(f"Processed {success_count}/{len(urls)} URLs successfully from {file_path}")

    def process_directory(self, directory_path: str) -> None:
        """Process all .txt files in a directory."""
        directory = Path(directory_path)
        txt_files = list(directory.glob("*.txt"))
        
        if not txt_files:
            self.logger.warning(f"No .txt files found in {directory_path}")
            return
        
        for txt_file in txt_files:
            self.logger.info(f"Processing file: {txt_file}")
            self.process_file(str(txt_file))


def main():
    parser = argparse.ArgumentParser(description="Convert URLs from text files to PDFs")
    parser.add_argument("input", help="Input file or directory containing .txt files with URLs")
    parser.add_argument("-o", "--output", default="pdf_output", help="Output directory for PDFs")
    parser.add_argument("--no-headless", action="store_true", help="Run browser in non-headless mode")
    
    args = parser.parse_args()
    
    agent = URLToPDFAgent(output_dir=args.output, headless=not args.no_headless)
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        agent.process_file(str(input_path))
    elif input_path.is_dir():
        agent.process_directory(str(input_path))
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        sys.exit(1)


if __name__ == "__main__":
    main()