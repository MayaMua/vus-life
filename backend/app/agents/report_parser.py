import os
import random
import io
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from pypdf import PdfReader, PdfWriter

from prompts.parse_prompts import REPORT_TO_MD_PROMPT, MD_TO_JSON_EXAMPLE, REPORT_TEMPLATE
from schema.items_of_interest import GeneticReport
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser


# Create Pydantic parser
parser = PydanticOutputParser(pydantic_object=GeneticReport)

def parse_page_selection(page_str: str) -> List[int]:
    """
    Parse page selection string to list of page numbers.
    
    Supports formats like:
    - "1, 2, 4" -> [1, 2, 4]
    - "1, 3-5" -> [1, 3, 4, 5]
    - "3-5" -> [3, 4, 5]
    
    Args:
        page_str: String containing page numbers and ranges
        
    Returns:
        List of page numbers
    """
    if not page_str or page_str.strip() == "":
        return None
    
    pages = []
    parts = page_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Handle range like "3-5"
            start, end = part.split('-')
            pages.extend(range(int(start), int(end) + 1))
        else:
            # Handle single page
            pages.append(int(part))
    
    return sorted(list(set(pages)))  # Remove duplicates and sort


def extract_pdf_pages(pdf_path: str, start_page: int = 1, end_page: Optional[int] = None) -> bytes:
    """
    Extract specific pages from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        start_page: Starting page number (1-indexed)
        end_page: Ending page number (1-indexed). If None, extract to the last page
        
    Returns:
        PDF data as bytes containing only the selected pages
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    total_pages = len(reader.pages)
    
    # Convert to 0-indexed
    start_idx = start_page - 1
    end_idx = total_pages if end_page is None else end_page
    
    # Validate page range
    if start_idx < 0 or start_idx >= total_pages:
        raise ValueError(f"Invalid start_page. PDF has {total_pages} pages.")
    
    if end_idx > total_pages:
        end_idx = total_pages
    
    # Add selected pages to writer
    for page_num in range(start_idx, end_idx):
        writer.add_page(reader.pages[page_num])
    
    # Write to bytes
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer.read()


def extract_pdf_pages_by_numbers(pdf_path: str, page_numbers: List[int]) -> bytes:
    """
    Extract specific pages from a PDF file by page numbers.
    
    Args:
        pdf_path: Path to the PDF file
        page_numbers: List of page numbers to extract (1-indexed)
        
    Returns:
        PDF data as bytes containing only the selected pages
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    total_pages = len(reader.pages)
    
    # Validate and add pages
    for page_num in page_numbers:
        if 1 <= page_num <= total_pages:
            writer.add_page(reader.pages[page_num - 1])  # Convert to 0-indexed
        else:
            raise ValueError(f"Invalid page number {page_num}. PDF has {total_pages} pages.")
    
    # Write to bytes
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer.read()


def analyze_medical_pdf(
    pdf_path: str, 
    model: str = "gemini-1.5-flash",
    api_key: str = None,
    page_numbers: Optional[List[int]] = None,
    start_page: int = 1, 
    end_page: Optional[int] = None
):
    """
    Analyze a medical PDF report and extract both Markdown and structured JSON data.
    
    Args:
        pdf_path: Path to the PDF file to analyze
        model: Gemini model name (default: "gemini-1.5-flash")
        api_key: Google API key for Gemini
        page_numbers: List of specific page numbers to extract (1-indexed). Takes precedence over start_page/end_page
        start_page: Starting page number to analyze (1-indexed, default: 1)
        end_page: Ending page number to analyze (1-indexed, default: None for all pages)
        
    Returns:
        Dictionary containing 'markdown' and 'data' keys, or 'raw_content' if parsing fails
    """
    # Initialize Gemini model with provided parameters
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY", "")
    
    llm = ChatGoogleGenerativeAI(
        model=model,
        temperature=0,
        google_api_key=api_key
    )
    
    # Build the final prompt
    custom_prompt = f"""
    {REPORT_TO_MD_PROMPT}
    
    ---
    
    {REPORT_TEMPLATE.format(
        report_text="Please extract the information from the attached PDF file.",
        example_output=MD_TO_JSON_EXAMPLE,
        format_instructions=parser.get_format_instructions()
    )}
    
    IMPORTANT: Your response must be divided into two sections:
    SECTION 1: [MARKDOWN_REPORT]
    (Place the Markdown formatted clinical report here)
    
    SECTION 2: [JSON_DATA]
    (Place the JSON output here, strictly following the schema)
    """

    # Extract specific pages if requested
    if page_numbers is not None and len(page_numbers) > 0:
        print(f"Extracting pages: {page_numbers}")
        pdf_data = extract_pdf_pages_by_numbers(pdf_path, page_numbers)
    elif start_page > 1 or end_page is not None:
        print(f"Extracting pages {start_page} to {end_page or 'end'}")
        pdf_data = extract_pdf_pages(pdf_path, start_page, end_page)
    else:
        # Read entire PDF file
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

    message = HumanMessage(
        content=[
            {"type": "text", "text": custom_prompt},
            {
                "type": "media",
                "mime_type": "application/pdf",
                "data": pdf_data,
            },
        ]
    )

    # Invoke the model
    response = llm.invoke([message])
    content = response.content

    # Post-processing: split Markdown and JSON
    try:
        md_part = content.split("SECTION 1: [MARKDOWN_REPORT]")[1].split("SECTION 2: [JSON_DATA]")[0].strip()
        json_part = content.split("SECTION 2: [JSON_DATA]")[1].strip()
        
        # Validate and parse JSON
        structured_data = parser.parse(json_part)
        
        return {
            "markdown": md_part,
            "data": structured_data.dict()
        }
    except Exception as e:
        print(f"Parsing failed: {e}")
        return {"raw_content": content}


def main():
    """
    Test function: randomly select a PDF from data/uploads and analyze it.
    """
    # Define the uploads directory
    uploads_dir = os.path.join(
        os.path.dirname(__file__), 
        "..", "..", "..", "data", "uploads"
    )
    
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in data/uploads directory")
        return
    
    # Randomly select a PDF
    selected_pdf = random.choice(pdf_files)
    pdf_path = os.path.join(uploads_dir, selected_pdf)
    
    print(f"Testing with randomly selected PDF: {selected_pdf}")
    print("=" * 80)
    
    # Analyze only the first 2 pages to save quota
    result = analyze_medical_pdf(pdf_path, start_page=1, end_page=2)
    
    # Display results
    if "markdown" in result:
        print("\n--- MARKDOWN OUTPUT ---")
        print(result["markdown"])
        print("\n" + "=" * 80)
        print("\n--- JSON OUTPUT ---")
        import json
        print(json.dumps(result["data"], indent=2))
    else:
        print("\n--- RAW CONTENT (Parsing Failed) ---")
        print(result.get("raw_content", "No content available"))


if __name__ == "__main__":
    main()