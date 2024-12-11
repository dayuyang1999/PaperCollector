# src/csv_creator.py
import csv
import datetime
import json
from pathlib import Path


class CSVCreator:
    def __init__(self, papers_jsonl: str, summaries_jsonl: str, output_csv: str):
        """Initialize CSVCreator."""
        self.papers_jsonl = papers_jsonl
        self.summaries_jsonl = summaries_jsonl
        self.output_csv = output_csv

    def load_papers_metadata(self) -> dict:
        """Load papers metadata from arxiv JSONL file."""
        papers_dict = {}
        try:
            with open(self.papers_jsonl, "r", encoding="utf-8") as f:
                for line in f:
                    paper = json.loads(line)
                    arxiv_id = paper["pdf_url"].split("/")[-1].replace(".pdf", "")
                    published_date = datetime.datetime.fromisoformat(
                        paper["published"].replace("Z", "+00:00")
                    )

                    papers_dict[arxiv_id] = {
                        "title": paper["title"],
                        "abstract": paper["abstract"],
                        "arxiv": paper["id"],
                        "release_date": published_date.strftime("%Y-%m"),
                    }
            print(f"Loaded metadata for {len(papers_dict)} papers")
        except Exception as e:
            print(f"Error loading papers metadata: {str(e)}")
        return papers_dict

    def load_summaries(self) -> dict:
        """Load paper summaries from summaries JSONL file."""
        summaries_dict = {}
        try:
            with open(self.summaries_jsonl, "r", encoding="utf-8") as f:
                for line in f:
                    summary = json.loads(line)
                    arxiv_id = summary["url"].split("/")[-1].replace(".pdf", "")

                    summaries_dict[arxiv_id] = {
                        "keywords": summary["keywords"],
                        "overall_summary": summary["overall_summary"],
                        "structure": summary["structure"],
                        "methodology": summary["methodology"],
                        "example": summary["example"],
                    }
            print(f"Loaded summaries for {len(summaries_dict)} papers")
        except Exception as e:
            print(f"Error loading summaries: {str(e)}")
        return summaries_dict

    def create(self):
        """Create CSV file with combined information."""
        print("Loading papers metadata and summaries...")
        papers_dict = self.load_papers_metadata()
        summaries_dict = self.load_summaries()

        if not papers_dict or not summaries_dict:
            print("No data to process. Check if input files exist and are not empty.")
            return

        fieldnames = [
            "title",
            "keywords",
            "release_date",
            "overall_summary",
            "structure",
            "methodology",
            "example",
            "abstract",
            "arxiv",
        ]

        print(f"Creating CSV file at {self.output_csv}...")
        rows_written = 0
        with open(self.output_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for arxiv_id in papers_dict:
                if arxiv_id in summaries_dict:
                    try:
                        paper_meta = papers_dict[arxiv_id]
                        paper_summary = summaries_dict[arxiv_id]

                        # Process keywords if they're in list format
                        keywords = paper_summary["keywords"]
                        if isinstance(keywords, list):
                            keywords = ", ".join(keywords)

                        # Create row
                        row = {
                            "title": paper_meta["title"],
                            "keywords": keywords,
                            "release_date": paper_meta["release_date"],
                            "overall_summary": paper_summary["overall_summary"],
                            "structure": paper_summary["structure"],
                            "methodology": paper_summary["methodology"],
                            "example": paper_summary["example"],
                            "abstract": paper_meta["abstract"],
                            "arxiv": paper_meta["arxiv"],
                        }

                        writer.writerow(row)
                        rows_written += 1
                    except Exception as e:
                        print(f"Error processing row for {arxiv_id}: {str(e)}")
                        continue

        print(f"CSV creation complete. Wrote {rows_written} rows to {self.output_csv}")
