import { useRef, useState } from "react";
import { api, UploadProgress, UploadResponse } from "@/app/api";

export interface FileUploadState {
  file: File | null;
  isLoading: boolean;
  isDragging: boolean;
  uploadProgress: number;
  uploadStatus: 'idle' | 'uploading' | 'completed' | 'error';
  uploadResponse: UploadResponse | null;
  error: string | null;
}

export const useFileLogic = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'completed' | 'error'>('idle');
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB as per backend config
  const CHUNK_THRESHOLD = 10 * 1024 * 1024; // Use chunked upload for files > 10MB

  const handleFileSelect = async (selectedFile: File) => {
    // Reset previous state
    setError(null);
    setUploadProgress(0);
    setUploadStatus('idle');
    setUploadResponse(null);

    // Validate file
    if (!selectedFile.name.endsWith(".pdf")) {
      setError("PDF 파일만 업로드 가능해요.");
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`파일 크기는 ${MAX_FILE_SIZE / (1024 * 1024)}MB 이하만 업로드 가능해요.`);
      return;
    }

    setFile(selectedFile);
    setIsLoading(true);
    setUploadStatus('uploading');

    try {
      let result: UploadResponse;

      if (selectedFile.size > CHUNK_THRESHOLD) {
        // Use chunked upload for large files
        console.log(`Using chunked upload for ${selectedFile.name} (${(selectedFile.size / (1024 * 1024)).toFixed(2)}MB)`);

        result = await api.uploadChunked(
          selectedFile,
          1048576, // 1MB chunks
          (progress: UploadProgress) => {
            setUploadProgress(progress.percentage);
            console.log(`Upload progress: ${progress.percentage}% (${progress.completedChunks}/${progress.totalChunks} chunks)`);
          }
        );
      } else {
        // Use normal upload for small files
        console.log(`Using normal upload for ${selectedFile.name} (${(selectedFile.size / (1024 * 1024)).toFixed(2)}MB)`);

        // Simulate progress for normal upload
        setUploadProgress(50);
        result = await api.upload(selectedFile);
        setUploadProgress(100);
      }

      console.log('Upload completed:', result);
      setUploadResponse(result);
      setUploadStatus('completed');

      // If document ID is returned, we can fetch status or connect to WebSocket for processing updates
      if (result.documentId) {
        console.log(`Document created with ID: ${result.documentId}`);
        // Optional: Connect to WebSocket for processing updates
        // connectToProcessingWebSocket(result.documentId);
      }

    } catch (error) {
      console.error('Upload error:', error);
      setError(error instanceof Error ? error.message : '업로드 중 오류가 발생했습니다.');
      setUploadStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  const connectToProcessingWebSocket = (documentId: number) => {
    // This could be implemented to track document processing status
    // For now, we'll just log it
    console.log(`Would connect to WebSocket for document ${documentId} processing updates`);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const resetFile = () => {
    setFile(null);
    setUploadProgress(0);
    setUploadStatus('idle');
    setUploadResponse(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setIsLoading(false);
    setIsDragging(false);

    // Disconnect WebSocket if connected
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  return {
    file,
    isLoading,
    isDragging,
    uploadProgress,
    uploadStatus,
    uploadResponse,
    error,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleFileSelect,
    fileInputRef,
    resetFile,
  };
};