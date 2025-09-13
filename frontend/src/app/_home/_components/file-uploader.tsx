import FileLoading from "./file-loading";
import { cn } from "@/util/shared";

interface FileUploaderProps {
  isLoading: boolean;
  isDragging: boolean;
  uploadProgress: number;
  uploadStatus: 'idle' | 'uploading' | 'completed' | 'error';
  error: string | null;
  handleDragOver: (e: React.DragEvent) => void;
  handleDragLeave: (e: React.DragEvent) => void;
  handleDrop: (e: React.DragEvent) => void;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  handleFileSelect: (selectedFile: File) => void;
}

export default function FileUploader({
  isLoading,
  isDragging,
  uploadProgress,
  uploadStatus,
  error,
  handleDragOver,
  handleDragLeave,
  handleDrop,
  fileInputRef,
  handleFileSelect,
}: FileUploaderProps) {
  return (
    <div className="bg-white rounded-2xl p-12 mb-8 shadow-xl text-center">
      {isLoading ? (
        <div className="space-y-4">
          <FileLoading />
          {uploadStatus === 'uploading' && (
            <div className="mt-6">
              <div className="mb-2 text-sm text-gray-600">
                업로드 중... {uploadProgress}%
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      ) : (
        <>
          <h2 className="mb-8 text-gray-900 text-2xl font-bold">
            PDF 문서를 업로드하세요
          </h2>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
              {error}
            </div>
          )}

          {uploadStatus === 'completed' && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-600">
              업로드가 완료되었습니다!
            </div>
          )}

          <div
            className={cn(
              "group border-4 border-dashed border-slate-300 rounded-xl p-12 cursor-pointer",
              "hover:border-indigo-500 hover:bg-indigo-50 transition duration-300",
              "hover:bg-gradient-to-br hover:from-[#eff6ff] hover:to-[#dbeafe] hover:translate-y-[-2px]",
              isDragging &&
                "border-indigo-500 bg-indigo-50 bg-gradient-to-br from-[#eff6ff] to-[#dbeafe] translate-y-[-2px]",
              error && "border-red-300",
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div
              className={cn(
                "text-5xl text-slate-400 mb-4 group-hover:scale-110 transition-all duration-300",
                isDragging && "scale-110",
              )}
            >
              📁
            </div>
            <div className="text-lg text-slate-500 mb-4">
              PDF 파일을 드래그하거나 클릭하여 선택하세요
            </div>
            <p className="text-slate-400 mb-4">최대 100MB, PDF 형식만 지원</p>
            <p className="text-xs text-slate-400 mb-4">
              10MB 이상 파일은 자동으로 청크 업로드가 적용됩니다
            </p>
            <div
              className={cn(
                "inline-block bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-6 py-3 rounded-full font-semibold shadow-md group-hover:shadow-lg transition cursor-pointer",
                isDragging && "shadow-lg",
              )}
            >
              파일 선택
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept="application/pdf"
                onChange={(e) => {
                  const selectedFile = e.target.files?.[0];
                  if (selectedFile) {
                    handleFileSelect(selectedFile);
                  }
                }}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}