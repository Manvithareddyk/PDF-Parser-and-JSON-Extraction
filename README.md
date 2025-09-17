# PDF Parser with Structured JSON Extraction
A comprehensive Python program that parses PDF files and extracts their content into well-structured JSON format. The program preserves the hierarchical organization of documents while identifying different content types including paragraphs, tables, and charts.

## Features

- **Multi-content Type Extraction**: Handles paragraphs, tables, and charts/images
- **Hierarchical Structure**: Maintains page-level organization and section/subsection relationships  
- **Clean Text Processing**: Extracts readable, well-formatted text content
- **Table Detection**: Automatically identifies and extracts tabular data
- **Modular Design**: Well-structured, documented, and maintainable codebase
- **Robust Error Handling**: Handles various PDF formats and edge cases

## Requirements

- Python 3.7 or higher
- Required Python packages (see installation section)

## Installation

### 1. Clone or Download the Code

Save the `pdf_parser.py` file to your local machine.

### 2. Install Dependencies

Install the required Python packages using pip:

```bash
pip install pdfplumber pandas pillow pytesseract
```

#### Detailed Package Information:

- **pdfplumber**: Main PDF parsing and text extraction
- **pandas**: Data manipulation for table processing  
- **pillow (PIL)**: Image processing capabilities
- **pytesseract**: OCR for text extraction from images (optional for advanced features)

### 3. Additional Setup for OCR (Optional)

If you plan to use advanced chart/image text extraction, install Tesseract OCR:

**Windows:**
- Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Add Tesseract to your system PATH

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

## Usage

### Command Line Interface

The program provides a command-line interface for easy usage:

```bash
python pdf_parser.py input_file.pdf -o output_file.json
```

#### Arguments:

- `input_file.pdf`: Path to the PDF file you want to parse (required)
- `-o, --output`: Path for the output JSON file (optional, defaults to `extracted_content.json`)

### Examples

**Basic usage:**
```bash
python pdf_parser.py document.pdf
```

**Specify output file:**
```bash
python pdf_parser.py document.pdf -o structured_content.json
```

**Full path example:**
```bash
python pdf_parser.py /path/to/your/document.pdf -o /path/to/output/result.json
```

### Programmatic Usage

You can also use the parser programmatically in your Python code:

```python
from pdf_parser import PDFParser

# Initialize the parser
parser = PDFParser('your_document.pdf')

# Extract content
data = parser.extract_content()

# Save to JSON
parser.save_to_json('output.json')

# Or work with the data directly
print(f"Extracted {len(data['pages'])} pages")
```

## Output Format

The program generates a JSON file with the following structure:

```json
{
  "pages": [
    {
      "page_number": 1,
      "content": [
        {
          "type": "paragraph",
          "section": "Introduction", 
          "sub_section": "Background",
          "text": "Extracted paragraph content..."
        },
        {
          "type": "table",
          "section": "Data Analysis",
          "description": null,
          "table_data": [
            ["Header 1", "Header 2", "Header 3"],
            ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
            ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"]
          ]
        },
        {
          "type": "chart", 
          "section": "Results",
          "description": "Chart showing performance metrics",
          "table_data": [
            ["X Label", "Y Label"],
            ["2022", "100"],
            ["2023", "150"]
          ]
        }
      ]
    }
  ]
}
```

### Content Types

- **paragraph**: Regular text content with section/subsection context
- **table**: Structured tabular data with headers and rows  
- **chart**: Visual elements like graphs, charts, or diagrams

## Troubleshooting

### Common Issues

1. **ImportError for required packages**
   - Solution: Install all dependencies using `pip install pdfplumber pandas pillow pytesseract`

2. **File not found error**
   - Solution: Ensure the PDF file path is correct and the file exists

3. **Empty or incomplete extraction**
   - Solution: Check if the PDF is text-based (not scanned images). For scanned PDFs, OCR capabilities are limited in this version.

4. **Memory issues with large PDFs**
   - Solution: Process large documents in smaller chunks or increase available memory

### Performance Tips

- **Large files**: The program processes page by page, so memory usage scales with page complexity rather than total file size
- **Complex layouts**: Documents with complex formatting may require manual review of extracted sections
- **Scanned documents**: Best results are achieved with text-based PDFs rather than scanned images

## Limitations

- **Chart data extraction**: Current implementation provides basic chart detection. Advanced chart data extraction would require additional image processing capabilities.
- **Complex layouts**: Very complex document layouts may not be perfectly preserved
- **Scanned PDFs**: Limited support for image-based PDFs (would require enhanced OCR integration)

## Future Enhancements

- Enhanced chart/image data extraction using computer vision
- Better section detection algorithms
- Support for more complex document structures
- Integration with cloud OCR services for better accuracy
- Batch processing capabilities

## Support

If you encounter issues:

1. Check that all dependencies are properly installed
2. Verify your Python version is 3.7 or higher  
3. Ensure the input PDF file is accessible and not corrupted
4. Review the console output for specific error messages

For advanced customization, examine the `PDFParser` class methods to modify extraction logic for your specific use case.
