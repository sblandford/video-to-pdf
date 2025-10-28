# Video to PDF Converter

Extract pages from screen-captured ebook videos and convert to PDF.

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: The `.vscode/settings.json` file is configured to automatically use the venv Python interpreter when you open this folder in Windsurf/VS Code. New terminals will automatically activate the venv.

### Manual Activation (if needed)
```bash
source venv/bin/activate
```

## Usage

```bash
python video_to_pdf.py --input video.mp4 --output book.pdf
```

### Options

- `--input`: Input video file (required)
- `--output`: Output PDF filename (required)
- `--threshold`: Page change detection sensitivity (0-1, default: 0.85)
- `--split-pages`: Split double-page spreads into separate images
- `--filter-blank`: Filter out mostly blank pages (e.g., loading spinners)
- `--blank-threshold`: Variance threshold for blank detection (default: 500, lower = stricter)
- `--no-auto-grayscale`: Disable automatic grayscale conversion for colorless pages (enabled by default)
- `--color-threshold`: Threshold for color detection (default: 10, lower = stricter)
- `--output-dir`: Directory for intermediate PNG files (default: ./pages)
- `--keep-images`: Keep PNG files after PDF creation

## Examples

```bash
# Basic usage
python video_to_pdf.py --input ebook.mp4 --output mybook.pdf

# With page splitting and custom threshold
python video_to_pdf.py --input ebook.mp4 --output mybook.pdf --split-pages --threshold 0.90

# Filter out loading spinners and blank pages
python video_to_pdf.py --input ebook.mp4 --output mybook.pdf --filter-blank

# All features combined
python video_to_pdf.py --input ebook.webm --output mybook.pdf --split-pages --filter-blank --keep-images

# Disable auto-grayscale (keep all pages as color)
python video_to_pdf.py --input ebook.webm --output mybook.pdf --no-auto-grayscale
```

## Features

### Automatic Grayscale Optimization
The tool automatically detects pages without color and saves them as grayscale PNGs, reducing file size by ~50% for those pages. This is enabled by default and works transparently.
