import { useRef, useState } from "react";
import { api } from "@/app/api";

export const useFileLogic = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (selectedFile: File) => {
    setIsLoading(true);
    if (!selectedFile.name.endsWith(".pdf")) {
      alert("PDF 파일만 업로드만 가능해요.");
      setIsLoading(false);
      return;
    }
    if (selectedFile.size > 50 * 1024 * 1024) {
      alert("파일 크기는 50MB 이하만 업로드 가능해요.");
      setIsLoading(false);
      return;
    }
    setFile(selectedFile);

    try {
      const result = await api.upload(selectedFile);
      console.log(result);
    } catch (error) {
      console.error(error);
    } 
      
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
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
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setIsLoading(false);
    setIsDragging(false);
  };

  return {
    file,
    isLoading,
    isDragging,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleFileSelect,
    fileInputRef,
    resetFile,
  };
};
