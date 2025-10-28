#!/usr/bin/env python3
"""
Video to PDF Converter
Extract pages from screen-captured ebook videos and convert to PDF.
"""

import argparse
import os
import sys
from pathlib import Path
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import img2pdf
from PIL import Image


class VideoPageExtractor:
    """Extract individual pages from a video of someone flipping through a book."""
    
    def __init__(self, video_path, threshold=0.85, output_dir="pages", split_pages=False, filter_blank=False, blank_threshold=500):
        """
        Initialize the extractor.
        
        Args:
            video_path: Path to input video file
            threshold: Similarity threshold (0-1). Higher = less sensitive to changes
            output_dir: Directory to save extracted page images
            split_pages: Whether to split double-page spreads
            filter_blank: Whether to filter out mostly blank pages (e.g., loading spinners)
            blank_threshold: Variance threshold for blank detection (lower = more blank)
        """
        self.video_path = video_path
        self.threshold = threshold
        self.output_dir = Path(output_dir)
        self.split_pages = split_pages
        self.filter_blank = filter_blank
        self.blank_threshold = blank_threshold
        self.page_count = 0
        self.skipped_blank = 0
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def compare_frames(self, frame1, frame2):
        """
        Compare two frames to detect if a page change occurred.
        
        Args:
            frame1: First frame (numpy array)
            frame2: Second frame (numpy array)
            
        Returns:
            float: Similarity score (0-1, where 1 is identical)
        """
        # Convert to grayscale for comparison
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Resize for faster comparison
        height, width = gray1.shape
        resize_height = min(height, 480)
        resize_width = min(width, 640)
        
        gray1_resized = cv2.resize(gray1, (resize_width, resize_height))
        gray2_resized = cv2.resize(gray2, (resize_width, resize_height))
        
        # Calculate structural similarity
        score, _ = ssim(gray1_resized, gray2_resized, full=True)
        
        return score
    
    def is_blank_page(self, frame):
        """
        Detect if a frame is mostly blank (e.g., loading spinner on white background).
        
        Args:
            frame: Frame to check (numpy array)
            
        Returns:
            bool: True if the page appears to be blank/minimal content
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate Laplacian variance (measures image sharpness/content)
        # Blank pages with just a spinner will have very low variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        return laplacian_var < self.blank_threshold
    
    def split_image(self, image_path, page_num):
        """
        Split a double-page spread into two separate images.
        
        Args:
            image_path: Path to the image to split
            page_num: Page number for naming
            
        Returns:
            list: Paths to the split images
        """
        img = Image.open(image_path)
        width, height = img.size
        
        # Split at the middle
        mid = width // 2
        
        # Left page
        left = img.crop((0, 0, mid, height))
        left_path = self.output_dir / f"page_{page_num:04d}_left.png"
        left.save(left_path, "PNG")
        
        # Right page
        right = img.crop((mid, 0, width, height))
        right_path = self.output_dir / f"page_{page_num:04d}_right.png"
        right.save(right_path, "PNG")
        
        # Remove original
        os.remove(image_path)
        
        return [left_path, right_path]
    
    def save_page(self, frame):
        """
        Save a frame as a page image.
        
        Args:
            frame: Frame to save (numpy array)
            
        Returns:
            str or list or None: Path(s) to saved image(s), or None if filtered
        """
        # Check if page is blank (if filtering enabled)
        if self.filter_blank and self.is_blank_page(frame):
            self.skipped_blank += 1
            print(f"  Skipped blank/loading page")
            return None
        
        self.page_count += 1
        
        if self.split_pages:
            # Save temporary full image
            temp_path = self.output_dir / f"page_{self.page_count:04d}_temp.png"
            cv2.imwrite(str(temp_path), frame)
            
            # Split and return paths
            paths = self.split_image(temp_path, self.page_count)
            print(f"  Saved as {paths[0].name} and {paths[1].name}")
            return paths
        else:
            # Save single image
            path = self.output_dir / f"page_{self.page_count:04d}.png"
            cv2.imwrite(str(path), frame)
            print(f"  Saved as {path.name}")
            return str(path)
    
    def extract_pages(self):
        """
        Extract pages from the video.
        
        Returns:
            list: Paths to all extracted page images
        """
        print(f"Opening video: {self.video_path}")
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {self.video_path}")
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"Video info: {total_frames} frames @ {fps:.2f} fps")
        print(f"Detection threshold: {self.threshold}")
        print(f"Split pages: {self.split_pages}")
        print(f"Filter blank pages: {self.filter_blank}")
        if self.filter_blank:
            print(f"Blank threshold: {self.blank_threshold}")
        print("\nExtracting pages...")
        
        prev_frame = None
        frame_count = 0
        page_images = []
        
        # Read first frame
        ret, frame = cap.read()
        if ret:
            print(f"\nPage {self.page_count + 1} detected (first frame)")
            result = self.save_page(frame)
            if result is not None:
                if isinstance(result, list):
                    page_images.extend(result)
                else:
                    page_images.append(result)
            prev_frame = frame
            frame_count += 1
        
        # Process remaining frames
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Show progress
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)", end='\r')
            
            # Compare with previous frame
            similarity = self.compare_frames(prev_frame, frame)
            
            # If similarity is below threshold, we have a new page
            if similarity < self.threshold:
                print(f"\nPage {self.page_count + 1} detected (frame {frame_count}, similarity: {similarity:.3f})")
                result = self.save_page(frame)
                if result is not None:
                    if isinstance(result, list):
                        page_images.extend(result)
                    else:
                        page_images.append(result)
                prev_frame = frame
        
        cap.release()
        print(f"\n\nExtraction complete! Found {self.page_count} page change(s)")
        if self.filter_blank and self.skipped_blank > 0:
            print(f"Skipped {self.skipped_blank} blank/loading page(s)")
        print(f"Total images: {len(page_images)}")
        
        return sorted(page_images)
    
    def create_pdf(self, page_images, output_pdf):
        """
        Create a PDF from extracted page images.
        
        Args:
            page_images: List of image paths
            output_pdf: Output PDF path
        """
        print(f"\nCreating PDF: {output_pdf}")
        
        # Convert images to PDF
        with open(output_pdf, "wb") as f:
            f.write(img2pdf.convert(page_images))
        
        print(f"PDF created successfully!")
        print(f"Output: {output_pdf}")
        
        # Get file size
        size_mb = os.path.getsize(output_pdf) / (1024 * 1024)
        print(f"File size: {size_mb:.2f} MB")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract pages from a video of an ebook and create a PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input video.mp4 --output book.pdf
  %(prog)s --input video.mp4 --output book.pdf --split-pages --threshold 0.90
  %(prog)s --input video.mp4 --output book.pdf --keep-images
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input video file path"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output PDF file path"
    )
    
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.85,
        help="Page change detection threshold (0-1, default: 0.85). Higher = less sensitive"
    )
    
    parser.add_argument(
        "--split-pages",
        action="store_true",
        help="Split double-page spreads into separate images"
    )
    
    parser.add_argument(
        "--filter-blank",
        action="store_true",
        help="Filter out mostly blank pages (e.g., loading spinners)"
    )
    
    parser.add_argument(
        "--blank-threshold",
        type=float,
        default=500,
        help="Variance threshold for blank page detection (default: 500, lower = stricter)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="pages",
        help="Directory for intermediate PNG files (default: pages)"
    )
    
    parser.add_argument(
        "--keep-images",
        action="store_true",
        help="Keep PNG files after PDF creation"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    # Validate threshold
    if not 0 <= args.threshold <= 1:
        print(f"Error: Threshold must be between 0 and 1", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Extract pages
        extractor = VideoPageExtractor(
            args.input,
            threshold=args.threshold,
            output_dir=args.output_dir,
            split_pages=args.split_pages,
            filter_blank=args.filter_blank,
            blank_threshold=args.blank_threshold
        )
        
        page_images = extractor.extract_pages()
        
        if not page_images:
            print("Error: No pages were extracted!", file=sys.stderr)
            sys.exit(1)
        
        # Create PDF
        extractor.create_pdf(page_images, args.output)
        
        # Cleanup if requested
        if not args.keep_images:
            print(f"\nCleaning up temporary images...")
            for img_path in page_images:
                os.remove(img_path)
            # Remove directory if empty
            try:
                Path(args.output_dir).rmdir()
                print(f"Removed directory: {args.output_dir}")
            except OSError:
                print(f"Directory not empty, keeping: {args.output_dir}")
        else:
            print(f"\nPage images kept in: {args.output_dir}")
        
        print("\n✓ Done!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
