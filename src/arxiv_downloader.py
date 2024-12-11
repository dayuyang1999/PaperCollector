import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import PyPDF2
import requests
from tqdm import tqdm

class PaperDownloader:
    def __init__(self, papers_jsonl: str, output_dir: str, delay: int = 1):
        """Initialize PaperDownloader."""
        self.papers_jsonl = papers_jsonl
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_arxiv_id(self, pdf_url: str) -> str:
        """Extract arXiv ID from PDF URL."""
        parsed_url = urlparse(pdf_url)
        path = parsed_url.path
        match = re.search(r"\d{4}\.\d{5}(?:v\d+)?", path)
        if match:
            return match.group(0)
        raise ValueError(f"Could not extract arXiv ID from URL: {pdf_url}")

    def download_pdf(self, url: str, timeout: int = 30) -> bytes:
        """Download PDF from URL."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.content

    def download_all(self):
        """Download all papers from the JSONL file."""
        with open(self.papers_jsonl, "r", encoding="utf-8") as f:
            papers = [json.loads(line) for line in f]

        for paper in tqdm(papers, desc="Downloading PDFs"):
            try:
                pdf_url = paper["pdf_url"]
                arxiv_id = self.extract_arxiv_id(pdf_url)
                output_path = self.output_dir / f"{arxiv_id}.pdf"

                if output_path.exists():
                    continue

                pdf_content = self.download_pdf(pdf_url)
                with open(output_path, "wb") as f:
                    f.write(pdf_content)

                time.sleep(self.delay)

            except Exception as e:
                print(f"Error downloading {pdf_url}: {str(e)}")
                continue
