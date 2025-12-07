# Skill Tree Generator - Usage Guide

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Set your xAI API key for enhanced skill extraction:
```bash
export XAI_API_KEY="your_api_key_here"
```

## Usage

Run the script with your resume PDF:

```bash
python skill_tree_generator.py
```

Or specify a different PDF path:

```bash
python skill_tree_generator.py path/to/resume.pdf
```

## Output

The script generates two files:

1. **skill_tree.json** - Structured JSON data of the skill tree
2. **skill_tree.html** - Interactive web visualization (open in your browser)

## Features

- **PDF Text Extraction**: Extracts text from PDF resumes using pdfplumber (with PyPDF2 fallback)
- **AI-Powered Analysis**: Uses xAI API to intelligently extract and categorize skills
- **Fallback Mode**: Works without API key using keyword matching
- **Interactive Visualization**: Beautiful, interactive skill tree with zoom, expand/collapse features
- **Hierarchical Structure**: Organizes skills into categories (Technical, Soft Skills, Domains, Certifications)

## Visualization Controls

- **Zoom In/Out**: Adjust the view scale
- **Reset**: Return to default view
- **Expand All**: Show all skill nodes
- **Collapse All**: Collapse to top-level categories
- **Click Nodes**: Expand/collapse individual branches

