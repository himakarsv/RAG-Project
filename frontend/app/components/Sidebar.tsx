"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Trash2, FileText, Upload, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { Document, uploadDocument, deleteDocument } from "@/lib/api";

interface SidebarProps {
  documents: Document[];
  selectedDocument: Document | null;
  onSelectDocument: (doc: Document | null) => void;
  onDocumentsChange: () => void;
}

export default function Sidebar({
  documents,
  selectedDocument,
  onSelectDocument,
  onDocumentsChange,
}: SidebarProps) {
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      setUploading(true);

      try {
        toast.loading(`Uploading ${file.name}...`, { id: "upload" });
        await uploadDocument(file);
        toast.success(`${file.name} uploaded and processed!`, { id: "upload" });
        onDocumentsChange(); // refresh the list
      } catch (error: any) {
        const message =
          error.response?.data?.detail || "Upload failed. Please try again.";
        toast.error(message, { id: "upload" });
      } finally {
        setUploading(false);
      }
    },
    [onDocumentsChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "text/csv": [".csv"],
      "text/plain": [".txt"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
    },
  });

  const handleDelete = async (e: React.MouseEvent, doc: Document) => {
    e.stopPropagation(); // prevent selecting the document
    setDeletingId(doc.document_id);

    try {
      await deleteDocument(doc.document_id);
      toast.success(`${doc.filename} deleted.`);
      if (selectedDocument?.document_id === doc.document_id) {
        onSelectDocument(null); // deselect if deleted doc was selected
      }
      onDocumentsChange();
    } catch {
      toast.error("Failed to delete document.");
    } finally {
      setDeletingId(null);
    }
  };

  const getFileTypeBadgeStyle = (fileType: string) => {
    switch (fileType) {
      case ".pdf":
        return "bg-orange-50 text-orange-800 border border-orange-200";
      case ".docx":
        return "bg-blue-50 text-blue-800 border border-blue-200";
      case ".xlsx":
      case ".csv":
        return "bg-green-50 text-green-800 border border-green-200";
      default:
        return "bg-gray-100 text-gray-700 border border-gray-200";
    }
  };

  return (
    <div className="w-64 flex-shrink-0 border-r border-gray-200 flex flex-col bg-gray-50 h-full">

      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <p className="text-sm font-medium text-gray-800 mb-3">Your documents</p>

        {/* Upload dropzone */}
        <div
          {...getRootProps()}
          className={`
            border border-dashed rounded-lg p-3 text-center cursor-pointer transition-colors
            ${isDragActive
              ? "border-purple-400 bg-purple-50"
              : "border-gray-300 hover:border-gray-400 hover:bg-white"
            }
          `}
        >
          <input {...getInputProps()} />
          {uploading ? (
            <div className="flex items-center justify-center gap-2 text-gray-500">
              <Loader2 size={14} className="animate-spin" />
              <span className="text-xs">Processing...</span>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-2 text-gray-500">
              <Upload size={14} />
              <span className="text-xs">
                {isDragActive ? "Drop it here" : "Upload a file"}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto p-2">
        {documents.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <FileText size={24} className="mx-auto mb-2 opacity-40" />
            <p className="text-xs">No documents yet</p>
          </div>
        ) : (
          <>
            {/* All documents option */}
            <div
              onClick={() => onSelectDocument(null)}
              className={`
                flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer mb-1 transition-colors
                ${selectedDocument === null
                  ? "bg-white border border-gray-200 text-gray-900"
                  : "hover:bg-white text-gray-600"
                }
              `}
            >
              <div className="w-5 h-5 rounded bg-purple-100 flex items-center justify-center flex-shrink-0">
                <span style={{ fontSize: 10 }} className="text-purple-700">✦</span>
              </div>
              <span className="text-xs font-medium">All documents</span>
              <span className="ml-auto text-xs text-gray-400">{documents.length}</span>
            </div>

            {/* Individual documents */}
            {documents.map((doc) => (
              <div
                key={doc.document_id}
                onClick={() => onSelectDocument(doc)}
                className={`
                  group flex items-start gap-2 px-3 py-2 rounded-lg cursor-pointer mb-1 transition-colors
                  ${selectedDocument?.document_id === doc.document_id
                    ? "bg-white border border-gray-200"
                    : "hover:bg-white"
                  }
                `}
              >
                <FileText size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-800 truncate">
                    {doc.filename}
                  </p>
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${getFileTypeBadgeStyle(doc.file_type)}`}>
                      {doc.file_type.replace(".", "").toUpperCase()}
                    </span>
                    <span className="text-[10px] text-gray-400">
                      {doc.total_chunks} chunks
                    </span>
                  </div>
                </div>
                <button
                  onClick={(e) => handleDelete(e, doc)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:text-red-500 text-gray-400"
                >
                  {deletingId === doc.document_id ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Trash2 size={12} />
                  )}
                </button>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}