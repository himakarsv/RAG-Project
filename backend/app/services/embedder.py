from openai import OpenAI
from app.core.config import settings
from typing import List

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# OpenAI's best embedding model
# outputs 1536-dimensional vectors
EMBEDDING_MODEL = "text-embedding-ada-002"


def get_embedding(text: str) -> List[float]:
    """
    Convert a single piece of text into a 1536-dimensional vector.
    This is what makes semantic search possible — similar texts
    produce similar vectors.
    """
    # Clean the text — remove excessive whitespace
    text = text.replace("\n", " ").strip()

    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )

    return response.data[0].embedding


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Embed multiple texts in one API call — much cheaper and
    faster than calling get_embedding() one at a time.
    OpenAI allows up to 2048 texts per batch call.
    """
    # Clean all texts
    cleaned = [t.replace("\n", " ").strip() for t in texts]

    response = client.embeddings.create(
        input=cleaned,
        model=EMBEDDING_MODEL
    )

    # Sort by index to make sure order is preserved
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]