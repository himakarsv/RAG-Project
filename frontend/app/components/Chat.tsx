"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, FileText, ChevronDown, ChevronUp } from "lucide-react";
import toast from "react-hot-toast";
import { Document, Message, Source, queryDocuments } from "@/lib/api";

interface ChatProps {
  selectedDocument: Document | null;
}

function SourceCard({ source }: { source: Source }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div
        className="flex items-center gap-2 px-3 py-2 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
        <span className="text-xs text-gray-600 flex-1">
          Source {source.source_number} — {source.filename}
        </span>
        <span className="text-[10px] text-gray-400 bg-white border border-gray-200 px-1.5 py-0.5 rounded-full">
          {(source.similarity_score * 100).toFixed(0)}% match
        </span>
        {expanded ? (
          <ChevronUp size={12} className="text-gray-400" />
        ) : (
          <ChevronDown size={12} className="text-gray-400" />
        )}
      </div>
      {expanded && (
        <div className="px-3 py-2 text-xs text-gray-600 leading-relaxed border-t border-gray-200 bg-white">
          {source.excerpt}
        </div>
      )}
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className={`
          w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0
          ${isUser ? "bg-green-100 text-green-800" : "bg-purple-100 text-purple-800"}
        `}
      >
        {isUser ? "U" : "AI"}
      </div>

      {/* Content */}
      <div className={`max-w-[75%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-2`}>
        <div
          className={`
            px-4 py-2.5 rounded-2xl text-sm leading-relaxed
            ${isUser
              ? "bg-purple-100 text-purple-900 rounded-tr-sm"
              : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm"
            }
          `}
        >
          {message.content}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="w-full flex flex-col gap-1.5">
            <p className="text-[10px] text-gray-400 uppercase tracking-wide">
              Sources used
            </p>
            {message.sources.map((source) => (
              <SourceCard key={source.source_number} source={source} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat({ selectedDocument }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [searchScope, setSearchScope] = useState<"document" | "all">("document");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Reset chat when document changes
  useEffect(() => {
    setMessages([]);
    setInput("");
  }, [selectedDocument?.document_id]);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;

    // Determine which document to query
    const docId =
      searchScope === "document" && selectedDocument
        ? selectedDocument.document_id
        : undefined;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await queryDocuments(question, docId, 5);

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error: any) {
      toast.error("Failed to get answer. Please try again.");
      // Remove the user message if query failed
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full min-w-0">

      {/* Header */}
      <div className="px-5 py-3.5 border-b border-gray-200 flex items-center gap-3 bg-white">
        <div className="w-8 h-8 rounded-lg bg-orange-50 flex items-center justify-center flex-shrink-0">
          <FileText size={15} className="text-orange-700" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {selectedDocument ? selectedDocument.filename : "All documents"}
          </p>
          <p className="text-xs text-gray-400">
            {selectedDocument
              ? `${selectedDocument.total_chunks} chunks · ${selectedDocument.file_type.replace(".", "").toUpperCase()}`
              : `Searching across all uploaded documents`
            }
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-4">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center py-16">
            <div className="w-12 h-12 rounded-2xl bg-purple-50 flex items-center justify-center mb-4">
              <span className="text-2xl">✦</span>
            </div>
            <p className="text-sm font-medium text-gray-700 mb-1">
              {selectedDocument
                ? `Ask anything about ${selectedDocument.filename}`
                : "Ask anything across your documents"
              }
            </p>
            <p className="text-xs text-gray-400 max-w-xs">
              The AI will search through the document chunks and answer using only what's in your files
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}

        {/* Loading indicator */}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-purple-100 flex items-center justify-center text-xs font-medium text-purple-800 flex-shrink-0">
              AI
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3">
              <Loader2 size={14} className="animate-spin text-gray-400" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Scope toggle + Input */}
      <div className="border-t border-gray-200 bg-white">

        {/* Search scope toggle */}
        <div className="flex items-center gap-2 px-4 pt-3 pb-1">
          <span className="text-xs text-gray-400">Search in:</span>
          <button
            onClick={() => setSearchScope("document")}
            className={`text-xs px-3 py-1 rounded-full border transition-colors ${
              searchScope === "document"
                ? "bg-purple-50 border-purple-200 text-purple-700"
                : "border-gray-200 text-gray-500 hover:bg-gray-50"
            }`}
          >
            {selectedDocument ? "This document" : "Select a document"}
          </button>
          <button
            onClick={() => setSearchScope("all")}
            className={`text-xs px-3 py-1 rounded-full border transition-colors ${
              searchScope === "all"
                ? "bg-purple-50 border-purple-200 text-purple-700"
                : "border-gray-200 text-gray-500 hover:bg-gray-50"
            }`}
          >
            All documents
          </button>
        </div>

        {/* Text input */}
        <div className="flex items-end gap-2 px-4 py-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              selectedDocument
                ? `Ask about ${selectedDocument.filename}...`
                : "Ask a question across all documents..."
            }
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm text-gray-800 bg-gray-50 outline-none focus:border-gray-300 focus:bg-white transition-colors placeholder:text-gray-400"
            style={{ maxHeight: 120 }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="w-9 h-9 rounded-xl bg-gray-900 text-white flex items-center justify-center flex-shrink-0 disabled:opacity-30 hover:bg-gray-700 transition-colors"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}