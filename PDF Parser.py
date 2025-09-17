import json
import re
import sys
from typing import Dict, List, Any, Optional, Tuple
import argparse
from pathlib import Path

try:
    import pdfplumber
    import pandas as pd
    from PIL import Image
    import pytesseract
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install required dependencies using: pip install pdfplumber pandas pillow pytesseract")
    sys.exit(1)


class PDFParser:
    """
    A comprehensive PDF parser that extracts content into structured JSON format.
    Handles paragraphs, tables, and charts while maintaining hierarchical organization.
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize the PDF parser with the path to the PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file to be parsed
        """
        self.pdf_path = pdf_path
        self.extracted_data = {"pages": []}
        
    def extract_content(self) -> Dict[str, Any]:
        """
        Main method to extract content from PDF and return structured JSON.
        
        Returns:
            Dict[str, Any]: Structured JSON containing all extracted content
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_content = self._process_page(page, page_num)
                    self.extracted_data["pages"].append(page_content)
            
            return self.extracted_data
            
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return {"pages": [], "error": str(e)}
    
    def _process_page(self, page, page_num: int) -> Dict[str, Any]:
        """
        Process a single page and extract all content types.
        
        Args:
            page: pdfplumber page object
            page_num (int): Page number
            
        Returns:
            Dict[str, Any]: Page content structure
        """
        page_data = {
            "page_number": page_num,
            "content": []
        }
        
        # Extract text content and identify sections
        text_content = self._extract_text_content(page)
        
        # Extract tables
        tables = self._extract_tables(page)
        
        # Extract images/charts
        charts = self._extract_charts(page, page_num)
        
        # Combine all content in reading order
        all_content = []
        all_content.extend(text_content)
        all_content.extend(tables)
        all_content.extend(charts)
        
        # Sort by vertical position to maintain reading order
        all_content.sort(key=lambda x: x.get('position', 0), reverse=True)
        
        # Clean up position data (not needed in final output)
        for item in all_content:
            item.pop('position', None)
            
        page_data["content"] = all_content
        return page_data
    
    def _extract_text_content(self, page) -> List[Dict[str, Any]]:
        """
        Extract and structure text content, identifying sections and paragraphs.
        
        Args:
            page: pdfplumber page object
            
        Returns:
            List[Dict[str, Any]]: List of structured text content
        """
        text_blocks = []
        
        try:
            # Extract text with position information
            words = page.extract_words()
            
            if not words:
                return text_blocks
            
            # Group words into lines and then paragraphs
            lines = self._group_words_into_lines(words)
            paragraphs = self._group_lines_into_paragraphs(lines)
            
            current_section = None
            current_subsection = None
            
            for para in paragraphs:
                text = para['text'].strip()
                if not text:
                    continue
                
                # Identify section headers (heuristics based on formatting)
                section_info = self._identify_section(para, text)
                
                if section_info['is_section']:
                    current_section = section_info['section']
                    current_subsection = None
                elif section_info['is_subsection']:
                    current_subsection = section_info['subsection']
                else:
                    # Regular paragraph
                    text_blocks.append({
                        "type": "paragraph",
                        "section": current_section,
                        "sub_section": current_subsection,
                        "text": text,
                        "position": para['top']
                    })
                    
        except Exception as e:
            print(f"Error extracting text content: {e}")
            
        return text_blocks
    
    def _group_words_into_lines(self, words: List[Dict]) -> List[Dict]:
        """Group words into lines based on vertical position."""
        if not words:
            return []
            
        # Sort words by vertical position, then horizontal
        words.sort(key=lambda w: (-w['top'], w['x0']))
        
        lines = []
        current_line = []
        current_top = None
        tolerance = 2  # pixels
        
        for word in words:
            if current_top is None or abs(word['top'] - current_top) <= tolerance:
                current_line.append(word)
                current_top = word['top']
            else:
                if current_line:
                    lines.append({
                        'text': ' '.join(w['text'] for w in current_line),
                        'top': current_top,
                        'x0': min(w['x0'] for w in current_line),
                        'size': current_line[0].get('size', 12)
                    })
                current_line = [word]
                current_top = word['top']
        
        if current_line:
            lines.append({
                'text': ' '.join(w['text'] for w in current_line),
                'top': current_top,
                'x0': min(w['x0'] for w in current_line),
                'size': current_line[0].get('size', 12)
            })
        
        return lines
    
    def _group_lines_into_paragraphs(self, lines: List[Dict]) -> List[Dict]:
        """Group lines into paragraphs based on spacing and indentation."""
        if not lines:
            return []
            
        paragraphs = []
        current_paragraph = []
        
        for i, line in enumerate(lines):
            if not current_paragraph:
                current_paragraph = [line]
                continue
                
            # Check if this line should start a new paragraph
            prev_line = lines[i-1]
            vertical_gap = prev_line['top'] - line['top']
            
            # New paragraph if significant vertical gap or different indentation
            if vertical_gap > 15 or abs(line['x0'] - prev_line['x0']) > 10:
                # Finish current paragraph
                paragraphs.append({
                    'text': '\n'.join(l['text'] for l in current_paragraph),
                    'top': current_paragraph[0]['top'],
                    'size': current_paragraph[0].get('size', 12)
                })
                current_paragraph = [line]
            else:
                current_paragraph.append(line)
        
        if current_paragraph:
            paragraphs.append({
                'text': '\n'.join(l['text'] for l in current_paragraph),
                'top': current_paragraph[0]['top'],
                'size': current_paragraph[0].get('size', 12)
            })
        
        return paragraphs
    
    def _identify_section(self, para: Dict, text: str) -> Dict[str, Any]:
        """
        Identify if text is a section header, subsection, or regular content.
        
        Args:
            para: Paragraph dictionary with formatting info
            text: Text content
            
        Returns:
            Dict with section identification results
        """
        result = {
            'is_section': False,
            'is_subsection': False,
            'section': None,
            'subsection': None
        }
        
        # Heuristics for section identification
        font_size = para.get('size', 12)
        is_short = len(text) < 100
        is_title_case = text.istitle() or text.isupper()
        has_numbers = bool(re.match(r'^\d+\.?\s', text))
        
        # Main section (larger font, short, title case)
        if font_size > 14 and is_short and (is_title_case or has_numbers):
            result['is_section'] = True
            result['section'] = text
        # Subsection (medium font, short, some formatting)
        elif font_size > 12 and is_short and (is_title_case or has_numbers or text.endswith(':')):
            result['is_subsection'] = True
            result['subsection'] = text
        
        return result
    
    def _extract_tables(self, page) -> List[Dict[str, Any]]:
        """
        Extract tables from the page.
        
        Args:
            page: pdfplumber page object
            
        Returns:
            List[Dict[str, Any]]: List of structured table data
        """
        tables_data = []
        
        try:
            tables = page.extract_tables()
            
            for i, table in enumerate(tables):
                if table and len(table) > 0:
                    # Clean the table data
                    cleaned_table = []
                    for row in table:
                        cleaned_row = [cell.strip() if cell else "" for cell in row]
                        if any(cell for cell in cleaned_row):  # Skip empty rows
                            cleaned_table.append(cleaned_row)
                    
                    if cleaned_table:
                        # Try to determine the section this table belongs to
                        table_bbox = self._get_table_bbox(page, i)
                        
                        tables_data.append({
                            "type": "table",
                            "section": self._find_nearest_section(page, table_bbox),
                            "description": None,
                            "table_data": cleaned_table,
                            "position": table_bbox['top'] if table_bbox else 0
                        })
                        
        except Exception as e:
            print(f"Error extracting tables: {e}")
            
        return tables_data
    
    def _get_table_bbox(self, page, table_index: int) -> Optional[Dict]:
        """Get bounding box of a table."""
        try:
            # This is a simplified approach - in practice, you might need more sophisticated methods
            tables = page.extract_tables()
            if table_index < len(tables):
                # Estimate position based on page content
                return {"top": 500 - (table_index * 100)}  # Rough estimation
        except:
            pass
        return None
    
    def _extract_charts(self, page, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract charts and images from the page.
        
        Args:
            page: pdfplumber page object
            page_num: Page number
            
        Returns:
            List[Dict[str, Any]]: List of structured chart/image data
        """
        charts_data = []
        
        try:
            # Extract images from the page
            if hasattr(page, 'images') and page.images:
                for i, image in enumerate(page.images):
                    try:
                        # Get image position
                        position = image.get('top', 0)
                        
                        # Try to extract any text associated with the image (caption, labels)
                        description = self._extract_image_description(page, image)
                        
                        # For actual chart data extraction, you would need more sophisticated
                        # image processing and OCR. This is a simplified version.
                        chart_data = self._extract_chart_data_simple(page, image)
                        
                        charts_data.append({
                            "type": "chart",
                            "section": self._find_nearest_section(page, image),
                            "description": description,
                            "table_data": chart_data,
                            "position": position
                        })
                        
                    except Exception as e:
                        print(f"Error processing image {i}: {e}")
                        
        except Exception as e:
            print(f"Error extracting charts: {e}")
            
        return charts_data
    
    def _extract_image_description(self, page, image) -> Optional[str]:
        """Extract description/caption for an image."""
        # This is a simplified implementation
        # In practice, you'd look for text near the image
        return "Chart or diagram extracted from PDF"
    
    def _extract_chart_data_simple(self, page, image) -> List[List[str]]:
        """
        Simple chart data extraction (placeholder implementation).
        In a real scenario, you'd use OCR and image processing.
        """
        # This is a placeholder - real implementation would require
        # sophisticated image processing and OCR
        return [
            ["Label", "Value"],
            ["Sample", "Data"]
        ]
    
    def _find_nearest_section(self, page, bbox) -> Optional[str]:
        """Find the nearest section header to a given bounding box."""
        # Simplified implementation - in practice, you'd analyze text positions
        # relative to the bbox to find the most relevant section
        return None
    
    def save_to_json(self, output_path: str) -> None:
        """
        Save the extracted data to a JSON file.
        
        Args:
            output_path (str): Path where the JSON file should be saved
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved extracted data to {output_path}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")


def main():
    """Main function to run the PDF parser."""
    parser = argparse.ArgumentParser(description='Extract structured content from PDF to JSON')
    parser.add_argument('input_pdf', help='Path to input PDF file')
    parser.add_argument('-o', '--output', help='Output JSON file path', 
                       default='extracted_content.json')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_pdf).exists():
        print(f"Error: Input file '{args.input_pdf}' does not exist.")
        sys.exit(1)
    
    # Initialize parser and extract content
    pdf_parser = PDFParser(args.input_pdf)
    print(f"Processing PDF: {args.input_pdf}")
    
    extracted_data = pdf_parser.extract_content()
    
    if "error" in extracted_data:
        print(f"Failed to process PDF: {extracted_data['error']}")
        sys.exit(1)
    
    # Save to JSON
    pdf_parser.save_to_json(args.output)
    
    # Print summary
    total_pages = len(extracted_data['pages'])
    total_content_items = sum(len(page['content']) for page in extracted_data['pages'])
    
    print(f"\nExtraction Summary:")
    print(f"  Pages processed: {total_pages}")
    print(f"  Total content items: {total_content_items}")
    
    # Content type breakdown
    content_types = {}
    for page in extracted_data['pages']:
        for item in page['content']:
            content_type = item['type']
            content_types[content_type] = content_types.get(content_type, 0) + 1
    
    for content_type, count in content_types.items():
        print(f"  {content_type.capitalize()}s: {count}")


if __name__ == "__main__":
    main()