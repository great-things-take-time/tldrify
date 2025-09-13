const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

export interface UploadProgress {
  percentage: number;
  completedChunks: number;
  totalChunks: number;
  uploadId: string;
}

export interface UploadResponse {
  success: boolean;
  documentId?: number;
  jobId?: string;
  filename?: string;
  size?: number;
  message: string;
  complete?: boolean;
  progress?: UploadProgress;
}

export interface DocumentResponse {
  id: number;
  filename: string;
  file_size: number;
  status: string;
  title?: string;
  page_count?: number;
  created_at: string;
  processing_completed_at?: string;
}

class ApiClient {
  private wsConnections: Map<string, WebSocket> = new Map();

  // Normal upload (for small files)
  async upload(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  }

  // Chunked upload (for large files)
  async uploadChunked(
    file: File,
    chunkSize: number = 1048576, // 1MB default
    onProgress?: (progress: UploadProgress) => void
  ): Promise<UploadResponse> {
    const uploadId = this.generateUploadId();
    const totalChunks = Math.ceil(file.size / chunkSize);
    let lastResponse: UploadResponse | null = null;

    for (let i = 0; i < totalChunks; i++) {
      const start = i * chunkSize;
      const end = Math.min(start + chunkSize, file.size);
      const chunk = file.slice(start, end);

      const formData = new FormData();
      formData.append("upload_id", uploadId);
      formData.append("chunk_index", i.toString());
      formData.append("total_chunks", totalChunks.toString());
      formData.append("filename", file.name);
      formData.append("chunk", chunk);

      const response = await fetch(`${API_BASE_URL}/api/upload/chunk`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Chunk ${i + 1} upload failed`);
      }

      lastResponse = await response.json();

      // Report progress
      if (onProgress && lastResponse.progress) {
        onProgress(lastResponse.progress);
      }
    }

    return lastResponse!;
  }

  // WebSocket connection for real-time progress
  connectProgressWebSocket(
    uploadId: string,
    onProgress: (progress: UploadProgress) => void,
    onComplete?: () => void,
    onError?: (error: Error) => void
  ): WebSocket {
    const ws = new WebSocket(`${WS_BASE_URL}/api/ws/upload/${uploadId}`);

    ws.onopen = () => {
      console.log(`WebSocket connected for upload ${uploadId}`);
      this.wsConnections.set(uploadId, ws);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'progress' && data.data) {
          onProgress(data.data);
        } else if (data.type === 'complete') {
          if (onComplete) onComplete();
          this.disconnectProgressWebSocket(uploadId);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(new Error('WebSocket connection error'));
    };

    ws.onclose = () => {
      console.log(`WebSocket disconnected for upload ${uploadId}`);
      this.wsConnections.delete(uploadId);
    };

    return ws;
  }

  // Disconnect WebSocket
  disconnectProgressWebSocket(uploadId: string) {
    const ws = this.wsConnections.get(uploadId);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close();
      this.wsConnections.delete(uploadId);
    }
  }

  // Get upload progress (polling alternative to WebSocket)
  async getUploadProgress(uploadId: string): Promise<UploadProgress> {
    const response = await fetch(`${API_BASE_URL}/api/upload/progress/${uploadId}`);

    if (!response.ok) {
      throw new Error('Failed to get upload progress');
    }

    const data = await response.json();
    return data.progress;
  }

  // Document management endpoints
  async getDocuments(
    status?: string,
    skip: number = 0,
    limit: number = 20
  ): Promise<DocumentResponse[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    if (status) {
      params.append('status', status);
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/documents?${params}`);

    if (!response.ok) {
      throw new Error('Failed to fetch documents');
    }

    return response.json();
  }

  async getDocument(documentId: number): Promise<DocumentResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}`);

    if (!response.ok) {
      throw new Error('Document not found');
    }

    return response.json();
  }

  async deleteDocument(documentId: number): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete document');
    }

    return response.json();
  }

  async getDocumentStatus(documentId: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}/status`);

    if (!response.ok) {
      throw new Error('Failed to get document status');
    }

    return response.json();
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/health`);

    if (!response.ok) {
      throw new Error('Health check failed');
    }

    return response.json();
  }

  // Helper to generate unique upload ID
  private generateUploadId(): string {
    return `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

export const api = new ApiClient();