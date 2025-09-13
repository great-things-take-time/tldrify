"use client";

import { useFileLogic } from "@/hook/file/use-file-logic";
import FileUploader from "./_home/_components/file-uploader";
import FileRenderer from "./_home/_components/file-renderer";

export default function Home() {
  const {
    file,
    isLoading,
    handleDragOver,
    handleDragLeave,
    isDragging,
    handleDrop,
    handleFileSelect,
    fileInputRef,
    resetFile,
    uploadProgress,
    uploadStatus,
    error,
  } = useFileLogic();

  return (
    <div>
      {file && uploadStatus === 'completed' ? (
        <FileRenderer file={file} resetFile={resetFile} />
      ) : (
        <FileUploader
          isLoading={isLoading}
          isDragging={isDragging}
          uploadProgress={uploadProgress}
          uploadStatus={uploadStatus}
          error={error}
          handleDragOver={handleDragOver}
          handleDragLeave={handleDragLeave}
          handleDrop={handleDrop}
          fileInputRef={fileInputRef}
          handleFileSelect={handleFileSelect}
        />
      )}
    </div>
  );
}