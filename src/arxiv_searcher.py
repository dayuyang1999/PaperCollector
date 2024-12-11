import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Union

import arxiv
from tqdm import tqdm

class ArxivSearcher:
    def __init__(self, search_config: Dict, output_path: str):
        """Initialize ArxivSearcher with search configuration."""
        self.config = search_config
        self.output_path = output_path
        self.client = arxiv.Client(page_size=100, delay_seconds=3, num_retries=5)

    def build_query(self) -> str:
        """Build arXiv query string from config."""
        query_parts = []

        # Add title search
        if self.config.get('title_keywords'):
            title_query = self._build_field_query(self.config['title_keywords'], 'ti')
            query_parts.append(f"({title_query})")

        # Add abstract search
        if self.config.get('abstract_keywords'):
            abstract_query = self._build_field_query(self.config['abstract_keywords'], 'abs')
            query_parts.append(f"({abstract_query})")

        # Combine queries
        search_query = " AND ".join(query_parts)

        # Add categories
        if self.config.get('categories'):
            category_query = self._build_category_query(self.config['categories'])
            search_query = f"{category_query} AND ({search_query})"

        # Add date range
        if self.config.get('date_range'):
            start_date = datetime.strptime(self.config['date_range']['start'], "%Y-%m-%d")
            search_query += f" AND submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO "

            if self.config['date_range'].get('end'):
                end_date = datetime.strptime(self.config['date_range']['end'], "%Y-%m-%d")
                search_query += f"{end_date.strftime('%Y%m%d')}2359]"
            else:
                search_query += "999999999999]"

        return search_query

    def _build_field_query(self, keywords: List[Union[str, List[str]]], field: str) -> str:
        """Build query string for a specific field."""
        query_parts = []
        for item in keywords:
            if isinstance(item, list):
                or_terms = [f'{field}:"{term}"' if " " in term else f"{field}:{term}"
                           for term in item]
                query_parts.append(f"({' OR '.join(or_terms)})")
            else:
                query_parts.append(f'{field}:"{item}"' if " " in item else f"{field}:{item}")
        return " AND ".join(query_parts)

    def _build_category_query(self, categories: List[str]) -> str:
        """Build query string for categories."""
        if len(categories) == 1:
            return f"cat:{categories[0]}"
        return f"cat:({' OR '.join(categories)})"

    def search_and_download(self):
        """Execute search and save results."""
        query = self.build_query()
        print(f"Using query: {query}")

        search = arxiv.Search(
            query=query,
            max_results=self.config.get('max_results', 100),
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        # Load existing papers to avoid duplicates
        existing_papers = set()
        try:
            with open(self.output_path, "r") as f:
                for line in f:
                    paper_data = json.loads(line)
                    existing_papers.add(paper_data["id"])
        except FileNotFoundError:
            pass

        # Process results
        with open(self.output_path, "a") as f:
            for result in tqdm(self.client.results(search), desc="Downloading metadata"):
                if result.entry_id in existing_papers:
                    continue

                try:
                    paper_data = {
                        "id": result.entry_id,
                        "title": result.title,
                        "abstract": result.summary,
                        "authors": [author.name for author in result.authors],
                        "categories": result.categories,
                        "published": result.published.isoformat(),
                        "updated": result.updated.isoformat(),
                        "pdf_url": result.pdf_url,
                        "primary_category": result.primary_category,
                    }
                    f.write(json.dumps(paper_data) + "\n")
                    f.flush()
                    time.sleep(1)

                except Exception as e:
                    print(f"Error processing paper {result.entry_id}: {str(e)}")
                    continue
