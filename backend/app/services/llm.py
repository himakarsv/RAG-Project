from openai import OpenAI
from app.core.config import settings
from typing import List, Dict, Any

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def build_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Build the prompt that gets sent to the LLM.

    This is called prompt engineering — the way you structure
    the context and question directly affects answer quality.

    We:
    1. Tell the LLM exactly what its role is
    2. Give it the retrieved chunks as context
    3. Tell it to cite sources and admit when it doesn't know
    """

    # Format each chunk with its source info
    context_parts = []
    for i, chunk in enumerate(chunks):
        filename = chunk["metadata"].get("filename", "Unknown")
        chunk_type = chunk["chunk_type"].upper()
        heading = chunk["metadata"].get("heading", "")

        source_label = f"[Source {i+1} | {filename} | {chunk_type}"
        if heading:
            source_label += f" | Section: {heading}"
        source_label += "]"

        context_parts.append(f"{source_label}\n{chunk['content']}")

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are a helpful assistant that answers questions based strictly on the provided document context.

CONTEXT:
{context}

INSTRUCTIONS:
- Answer the question using ONLY the information in the context above
- If the context does not contain enough information to answer, say "I don't have enough information in the provided documents to answer this"
- When you use information from a source, mention which source it came from (e.g. "According to Source 1...")
- If the context contains tables, interpret them carefully
- Be concise and accurate

QUESTION:
{query}

ANSWER:"""

    return prompt


def generate_answer(
    query: str,
    chunks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Send the query + retrieved chunks to GPT and get an answer.
    Returns the answer text plus the sources that were used.
    """

    if not chunks:
        return {
            "answer": "No relevant documents found. Please upload documents first.",
            "sources": [],
            "model": "gpt-4o-mini"
        }

    prompt = build_prompt(query, chunks)

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # fast and cheap — upgrade to gpt-4o later if needed
        messages=[
            {
                "role": "system",
                "content": "You are a precise document assistant. Answer only from the provided context."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,  # low temperature = more factual, less creative
        max_tokens=1000
    )

    answer = response.choices[0].message.content

    # Format sources for the response
    sources = [
        {
            "source_number": i + 1,
            "document_id": chunk["document_id"],
            "filename": chunk["metadata"].get("filename", "Unknown"),
            "chunk_type": chunk["chunk_type"],
            "similarity_score": chunk["similarity"],
            "excerpt": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
        }
        for i, chunk in enumerate(chunks)
    ]

    return {
        "answer": answer,
        "sources": sources,
        "model": "gpt-4o-mini",
        "chunks_used": len(chunks)
    }