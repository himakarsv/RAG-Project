import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from unstructured.partition.auto import partition
from unstructured.documents.elements import Table, Image, Title, NarrativeText
import os
import pytesseract
from app.core.config import settings


os.environ["PATH"] += os.pathsep + settings.POPPLER_PATH
os.environ["PATH"] += os.pathsep + str(Path(settings.TESSERACT_PATH).parent)
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH




def extract_with_unstructured(file_path: Path) -> dict:
    """
    Universal parser using Unstructured.io.
    Handles PDF, DOCX, XLSX, images, txt, md and more automatically.
    """
    elements = partition(filename=str(file_path),poppler_path=settings.POPPLER_PATH)

    result = {
        "raw_text": "",
        "tables": [],
        "images": [],
        "titles": [],
        "pages": [],
        "total_elements": len(elements)
    }

    raw_chunks = []

    for element in elements:
        text = str(element).strip()
        if not text:
            continue

        if isinstance(element, Title):
            result["titles"].append(text)
            raw_chunks.append(f"[HEADING] {text}")

        elif isinstance(element, Table):
            result["tables"].append({
                "content": text,
                "metadata": element.metadata.to_dict() if element.metadata else {}
            })
            raw_chunks.append(f"[TABLE]\n{text}")

        elif isinstance(element, Image):
            result["images"].append({
                "content": text,
                "metadata": element.metadata.to_dict() if element.metadata else {}
            })
            raw_chunks.append(f"[IMAGE] {text}")

        elif isinstance(element, NarrativeText):
            raw_chunks.append(text)

        else:
            raw_chunks.append(text)

    result["raw_text"] = "\n\n".join(raw_chunks)
    return result


def extract_text_from_pdf(file_path: Path) -> dict:
    """
    PDF-specific parser — combines Unstructured + pdfplumber for best results.
    Unstructured handles text and structure, pdfplumber adds precise table extraction.
    """

    # Step 1 — Unstructured handles the main extraction
    result = extract_with_unstructured(file_path)

    # Step 2 — pdfplumber for precise table extraction from PDFs
    try:
        with pdfplumber.open(str(file_path)) as pdf:
            result["total_pages"] = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                result["pages"].append({
                    "page_number": page_num + 1,
                    "text": page_text.strip()
                })

                tables = page.extract_tables()
                for table in tables:
                    if table:
                        # Convert table rows to readable markdown format
                        markdown_table = table_to_markdown(table)
                        result["tables"].append({
                            "page_number": page_num + 1,
                            "data": table,
                            "markdown": markdown_table
                        })
    except Exception as e:
        result["pdf_error"] = str(e)

    return result


def table_to_markdown(table: list) -> str:
    """
    Convert a pdfplumber table (list of rows) into a markdown table string.
    This is important because LLMs understand markdown tables much better
    than raw nested lists.
    """
    if not table or not table[0]:
        return ""

    # Clean None values
    cleaned = []
    for row in table:
        cleaned.append([str(cell) if cell is not None else "" for cell in row])

    # First row is the header
    header = cleaned[0]
    separator = ["---"] * len(header)
    rows = cleaned[1:]

    lines = []
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(separator) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def extract_text_from_file(file_path: Path, file_extension: str) -> dict:
    """
    Main router — detects file type and sends to the right parser.
    """
    file_extension = file_extension.lower()

    try:
        if file_extension == ".pdf":
            return extract_text_from_pdf(file_path)

        elif file_extension in [".docx", ".xlsx", ".xls", ".csv",
                                 ".txt", ".md", ".png", ".jpg",
                                 ".jpeg", ".webp"]:
            # Unstructured handles all of these automatically
            return extract_with_unstructured(file_path)

        else:
            return {
                "raw_text": "",
                "error": f"Unsupported file type: {file_extension}"
            }

    except Exception as e:
        return {
            "raw_text": "",
            "error": f"Parsing failed: {str(e)}"
        }