# Video to PDF Converter

Extract pages from screen-captured ebook videos and convert to PDF.

Created using Claude Sonnet 4.5 Thinking

## Supported Video Formats

The tool supports most common video formats including:
- **WebM** (VP8/VP9 codecs) - commonly used for screen recordings
- **MP4** (H.264/H.265)
- **AVI**
- **MOV** (QuickTime)
- **MKV** (Matroska)
- **FLV** (Flash Video)

Any format supported by OpenCV/ffmpeg will work.

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

3. (Optional) Install Tesseract OCR for searchable PDFs:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
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
- `--ocr`: Add searchable OCR text layer to PDF (requires tesseract-ocr to be installed)
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

# Create searchable PDF with OCR
python video_to_pdf.py --input ebook.mp4 --output mybook.pdf --ocr

# All features combined
python video_to_pdf.py --input ebook.webm --output mybook.pdf --split-pages --filter-blank --keep-images

# Disable auto-grayscale (keep all pages as color)
python video_to_pdf.py --input ebook.webm --output mybook.pdf --no-auto-grayscale
```

## Features

### Automatic Grayscale Optimization
The tool automatically detects pages without color and saves them as grayscale PNGs, reducing file size by ~50% for those pages. This is enabled by default and works transparently.

### OCR Text Layer (Optional)
When using `--ocr`, the tool adds an invisible, searchable text layer to the PDF using Tesseract OCR. This allows you to:
- Search for text within the PDF
- Copy/paste text from the PDF
- Use accessibility features

Note: OCR processing will significantly increase processing time (a few seconds per page).
