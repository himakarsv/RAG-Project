from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

# These are the core chunking settings
# chunk_size: max characters per chunk
# chunk_overlap: characters shared between consecutive chunks
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def chunk_text(
    text: str,
    metadata: Dict[str, Any] = {}
) -> List[Dict[str, Any]]:
    """
    Split plain text into overlapping chunks.
    Uses RecursiveCharacterTextSplitter which tries to split
    on paragraphs first, then sentences, then words.
    Never splits mid-word.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )

    chunks = splitter.split_text(text)

    return [
        {
            "content": chunk.strip(),
            "chunk_index": i,
            "chunk_type": "text",
            "metadata": metadata
        }
        for i, chunk in enumerate(chunks)
        if chunk.strip()  # skip empty chunks
    ]


def chunk_table(
    table_content: str,
    metadata: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    Tables are NEVER split — always kept as one chunk.
    Splitting mid-table destroys the meaning completely.
    """
    return {
        "content": table_content.strip(),
        "chunk_index": 0,
        "chunk_type": "table",
        "metadata": metadata
    }


def chunk_image(
    image_content: str,
    metadata: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    Each image description is its own chunk.
    """
    return {
        "content": image_content.strip(),
        "chunk_index": 0,
        "chunk_type": "image",
        "metadata": metadata
    }


def attach_heading_to_chunks(
    chunks: List[Dict[str, Any]],
    current_heading: str
) -> List[Dict[str, Any]]:
    """
    Prepend the nearest heading to every chunk.
    This gives the LLM section context even when
    only a small chunk is retrieved.

    Example:
        Without heading: "Leave must be applied 3 days in advance."
        With heading:    "[Section: Leave Policy] Leave must be applied 3 days in advance."
    """
    if not current_heading:
        return chunks

    for chunk in chunks:
        chunk["content"] = f"[Section: {current_heading}]\n{chunk['content']}"
        chunk["metadata"]["heading"] = current_heading

    return chunks


def chunk_document(
    extraction_result: dict,
    document_metadata: Dict[str, Any] = {}
) -> List[Dict[str, Any]]:
    """
    Main chunking function — takes the full extraction result
    from parser.py and produces a clean list of chunks ready
    for embedding.

    Handles text, tables and images with the right strategy for each.
    """
    all_chunks = []
    current_heading = ""

    # Split raw_text into lines and process each one
    raw_text = extraction_result.get("raw_text", "")
    if not raw_text:
        return []

    # Split on double newlines to get paragraphs/elements
    sections = raw_text.split("\n\n")

    text_buffer = []  # collect plain text sections before chunking

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Detect content type from the tags unstructured added
        if section.startswith("[HEADING]"):
            # Flush any buffered text before switching heading
            if text_buffer:
                combined = "\n\n".join(text_buffer)
                chunks = chunk_text(combined, metadata={**document_metadata})
                chunks = attach_heading_to_chunks(chunks, current_heading)
                all_chunks.extend(chunks)
                text_buffer = []

            # Update current heading (strip the tag)
            current_heading = section.replace("[HEADING]", "").strip()

        elif section.startswith("[TABLE]"):
            # Flush buffered text first
            if text_buffer:
                combined = "\n\n".join(text_buffer)
                chunks = chunk_text(combined, metadata={**document_metadata})
                chunks = attach_heading_to_chunks(chunks, current_heading)
                all_chunks.extend(chunks)
                text_buffer = []

            # Table is always one chunk
            table_content = section.replace("[TABLE]", "").strip()
            table_chunk = chunk_table(
                table_content,
                metadata={
                    **document_metadata,
                    "heading": current_heading
                }
            )
            all_chunks.append(table_chunk)

        elif section.startswith("[IMAGE]"):
            image_content = section.replace("[IMAGE]", "").strip()
            if image_content:
                image_chunk = chunk_image(
                    image_content,
                    metadata={
                        **document_metadata,
                        "heading": current_heading
                    }
                )
                all_chunks.append(image_chunk)

        else:
            # Plain text — buffer it up for batch chunking
            text_buffer.append(section)

    # Flush any remaining buffered text
    if text_buffer:
        combined = "\n\n".join(text_buffer)
        chunks = chunk_text(combined, metadata={**document_metadata})
        chunks = attach_heading_to_chunks(chunks, current_heading)
        all_chunks.extend(chunks)

    # Add global chunk index across the whole document
    for i, chunk in enumerate(all_chunks):
        chunk["document_chunk_index"] = i
        chunk["total_chunks"] = len(all_chunks)

    return all_chunks