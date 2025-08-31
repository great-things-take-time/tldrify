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
  } = useFileLogic();

  return (
    <div>
      {file ? (
        <FileRenderer file={file} resetFile={resetFile} />
      ) : (
        <FileUploader
          isLoading={isLoading}
          isDragging={isDragging}
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
