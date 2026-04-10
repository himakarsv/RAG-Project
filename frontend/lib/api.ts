import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Types ──────────────────────────────────────────────

export interface Document {
  document_id: string;
  filename: string;
  file_type: string;
  size_mb: number;
  total_chunks: number;
  status: "processing" | "ready" | "failed";
  created_at: string;
}

export interface Source {
  source_number: number;
  document_id: string;
  filename: string;
  chunk_type: string;
  similarity_score: number;
  excerpt: string;
}

export interface QueryResponse {
  question: string;
  answer: string;
  sources: Source[];
  model: string;
  chunks_used: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: Date;
}

// ── API calls ──────────────────────────────────────────

export const uploadDocument = async (file: File): Promise<Document> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const listDocuments = async (): Promise<Document[]> => {
  const response = await api.get("/documents");
  return response.data;
};

export const deleteDocument = async (documentId: string): Promise<void> => {
  await api.delete(`/documents/${documentId}`);
};

export const queryDocuments = async (
  question: string,
  documentId?: string,
  topK: number = 5
): Promise<QueryResponse> => {
  const response = await api.post("/query", {
    question,
    document_id: documentId || null,
    top_k: topK,
  });
  return response.data;
};