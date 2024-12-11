import os
from pathlib import Path

import yaml
from src.arxiv_downloader import PaperDownloader
from src.arxiv_searcher import ArxivSearcher
from src.csv_creator import CSVCreator
from src.paper_summarizer import PaperSummarizer


class PaperCollector:
    def __init__(self, config_path="config.yaml"):
        """Initialize PaperCollector with configuration."""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.setup_directories()

    def setup_directories(self):
        """Create necessary directories and set up file paths."""
        # Get project name
        self.project_name = self.config["project"]["name"]

        # Set up directories
        base_dir = Path(self.config["paths"]["base_dir"])
        self.papers_dir = (
            base_dir / self.config["paths"]["papers_dir"] / self.project_name
        )

        # Create directories
        base_dir.mkdir(exist_ok=True)
        self.papers_dir.mkdir(parents=True, exist_ok=True)

        # Set up file paths with consistent naming
        self.papers_jsonl = base_dir / f"{self.project_name}_papers.jsonl"
        self.summaries_jsonl = base_dir / f"{self.project_name}_summaries.jsonl"
        self.output_csv = base_dir / f"{self.project_name}_results.csv"

    def run(self):
        """Execute the complete paper collection and analysis pipeline."""
        print(f"\nStarting paper collection for project: {self.project_name}")

        print("\n1. Searching and downloading paper metadata...")
        searcher = ArxivSearcher(self.config["search"], self.papers_jsonl)
        searcher.search_and_download()

        print("\n2. Downloading PDF files...")
        downloader = PaperDownloader(
            self.papers_jsonl,
            self.papers_dir,
            delay=self.config["settings"]["delay_between_requests"],
        )
        downloader.download_all()

        print("\n3. Generating paper summaries...")
        summarizer = PaperSummarizer(
            self.config["api"]["anthropic_key"],
            max_words=self.config["settings"]["max_words_for_summary"],
        )
        summarizer.process_papers(
            self.papers_dir, self.papers_jsonl, self.summaries_jsonl
        )

        print("\n4. Creating final CSV report...")
        creator = CSVCreator(self.papers_jsonl, self.summaries_jsonl, self.output_csv)
        creator.create()

        print(f"\nProcess complete! Results saved to:")
        print(f"- Papers: {self.papers_dir}")
        print(f"- Metadata: {self.papers_jsonl}")
        print(f"- Summaries: {self.summaries_jsonl}")
        print(f"- Final Report: {self.output_csv}")


def main():
    """Main entry point."""
    try:
        collector = PaperCollector()
        collector.run()
    except Exception as e:
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
