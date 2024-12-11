# src/paper_summarizer.py
import io
import json
import os
import re
import time
from pathlib import Path

import anthropic
import PyPDF2
from tqdm import tqdm


class PaperSummarizer:
    def __init__(self, api_key: str, max_words: int = 3000):
        """Initialize PaperSummarizer."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.max_words = max_words

    def extract_paper_content(self, pdf_path: str) -> str:
        """Extract content from PDF file."""
        try:
            with open(pdf_path, "rb") as file:
                # Create PDF reader object
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract text from all pages
                text = []
                for page in pdf_reader.pages:
                    text.append(page.extract_text())

                # Join all text and truncate to max words
                full_text = " ".join(text)
                words = full_text.split()
                truncated_text = " ".join(words[: self.max_words])

                return truncated_text
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            return ""

    def fix_json_string(self, text: str) -> str:
        """Clean and fix JSON string before parsing."""
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)

        json_match = re.search(r"\{[\s\S]*\}", text)
        if not json_match:
            raise ValueError("No JSON object found in response")

        json_str = json_match.group()
        cleaned_json = " ".join(
            line.strip() for line in json_str.split("\n") if line.strip()
        )
        cleaned_json = re.sub(r",\s*}", "}", cleaned_json)
        cleaned_json = re.sub(r'"\s*:\s*"', '": "', cleaned_json)

        return cleaned_json

    def get_summaries(self, paper_content: str) -> dict:
        """Get summaries using Claude API."""
        if not paper_content.strip():
            raise ValueError("Empty paper content")

        prompt = (
            """Analyze this research paper content and provide a summary in this exact JSON format:
        {
            "keywords": "List 5-7 specific keywords that capture the unique aspects of this paper (avoid generic terms like 'large language model', 'deep learning', etc.)",
            "overall_summary": "Provide a concise 2-3 sentence summary of the paper's main contribution and significance",
            "structure": "Outline the main sections and flow of the paper in a clear structure",
            "methodology": "Describe the key technical approaches, algorithms, or methods used in bullet points",
            "example": "Provide a concrete example of how the method works in practice, ideally using a specific case from the paper"
        }

        Do not include any text outside of this JSON structure. Ensure the JSON is properly formatted.
        Your summary should be:
        - Concise and specific
        - Focused on technical details
        - Written for senior researchers in AI/ML
        - Include specific examples when possible

        Paper content:"""
            + paper_content
        )

        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        cleaned_json = self.fix_json_string(response.content[0].text)
        summaries = json.loads(cleaned_json)

        required_keys = {
            "keywords",
            "overall_summary",
            "structure",
            "methodology",
            "example",
        }
        if not all(key in summaries for key in required_keys):
            missing_keys = required_keys - set(summaries.keys())
            raise ValueError(f"Missing required keys: {missing_keys}")

        return summaries

    def process_papers(self, papers_dir: str, papers_jsonl: str, output_jsonl: str):
        """Process all papers and create summary JSONL file."""
        # Load papers metadata
        papers_dict = {}
        with open(papers_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                paper = json.loads(line)
                arxiv_id = paper["pdf_url"].split("/")[-1].replace(".pdf", "")
                papers_dict[arxiv_id] = paper["pdf_url"]

        # Track processed files
        processed_files = set()
        if os.path.exists(output_jsonl):
            with open(output_jsonl, "r", encoding="utf-8") as f:
                for line in f:
                    paper = json.loads(line)
                    arxiv_id = paper["url"].split("/")[-1].replace(".pdf", "")
                    processed_files.add(arxiv_id)

        # Process papers
        papers_dir = Path(papers_dir)
        with open(output_jsonl, "a", encoding="utf-8") as out_f:
            for pdf_path in tqdm(
                list(papers_dir.glob("*.pdf")), desc="Generating summaries"
            ):
                arxiv_id = pdf_path.stem

                if arxiv_id in processed_files or arxiv_id not in papers_dict:
                    print(f"Skipping {arxiv_id} (already processed or not in metadata)")
                    continue

                try:
                    print(f"\nProcessing {arxiv_id}...")
                    paper_content = self.extract_paper_content(pdf_path)
                    if not paper_content:
                        print(f"No content extracted from {arxiv_id}")
                        continue

                    summaries = self.get_summaries(paper_content)

                    output = {"url": papers_dict[arxiv_id], **summaries}

                    json.dump(output, out_f, ensure_ascii=False)
                    out_f.write("\n")
                    out_f.flush()

                    processed_files.add(arxiv_id)
                    print(f"Successfully processed {arxiv_id}")
                    time.sleep(1)

                except Exception as e:
                    print(f"Error processing {arxiv_id}: {str(e)}")
                    continue
