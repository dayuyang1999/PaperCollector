# Paper Collector

An automated tool for collecting, downloading, and analyzing research papers from arXiv. This tool searches for papers based on your criteria, downloads them, generates summaries using Claude API, and creates a comprehensive CSV report.

## Features

- Search arXiv papers using customizable criteria
- Automatically download PDF files
- Generate paper summaries using Claude API
- Create organized CSV reports with paper details and summaries

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/paper-collector.git
cd paper-collector
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Copy `config.yaml` and add your Anthropic API key:
```bash
cp config.yaml.example config.yaml
# Edit config.yaml and add your API key
```

## Configuration

Edit `config.yaml` to customize your search:

- `search`: Define search parameters (keywords, categories, date range)
- `api`: Add your Anthropic API key
- `paths`: Configure output directories
- `settings`: Adjust processing settings

## Usage

Simply run:
```bash
python main.py
```

The tool will:
1. Search arXiv for papers matching your criteria
2. Download PDFs
3. Generate summaries
4. Create a final CSV report

## Output

All output files are stored in the `data` directory:
- `papers.jsonl`: Raw paper metadata
- `papers/`: Downloaded PDF files
- `summaries.jsonl`: Paper summaries
- `results.csv`: Final report

## License

MIT License
