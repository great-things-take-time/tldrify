import usePdfLoad from "@/hook/file/use-pdf-load";

export default function FileRenderer({
  file,
  resetFile,
}: {
  file: File;
  resetFile: () => void;
}) {
  const { isLoading, totalPages, renderedPages, containerRef } =
    usePdfLoad(file);

  return (
    <div className="bg-white rounded-3xl p-8 shadow-2xl border border-gray-100">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
            <span className="text-white text-lg">📄</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-800">{file.name}</h3>
            <p className="text-sm text-gray-500">
              {totalPages > 0 ? `${totalPages}페이지` : "PDF 파일"}
            </p>
          </div>
        </div>

        <button
          onClick={resetFile}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-medium transition-colors duration-200 flex items-center space-x-2 cursor-pointer"
        >
          <span>↻</span>
          <span>다시 선택하기</span>
        </button>
      </div>

      {/* PDF 뷰어 컨테이너 */}
      <div
        ref={containerRef}
        className="max-h-[75vh] border-2 border-gray-200 rounded-2xl overflow-hidden shadow-lg bg-gradient-to-b from-gray-50 to-gray-100"
      >
        {/* 스크롤 가능한 PDF 페이지들 */}
        <div className="overflow-y-auto p-6 space-y-8 max-h-[75vh]">
          {renderedPages.length === 0 && isLoading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="w-12 h-12 border-3 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-4"></div>
              <p className="text-gray-600 font-medium">PDF 로딩 중...</p>
            </div>
          ) : (
            renderedPages.map((pageData) => (
              <div
                key={pageData.pageNumber}
                className="flex flex-col items-center"
              >
                {/* 페이지 번호 */}
                <div className="mb-4 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-500 text-white text-sm font-medium rounded-full shadow-md">
                  Page {pageData.pageNumber}
                </div>

                {/* 렌더링된 캔버스 */}
                <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-200 hover:shadow-xl transition-shadow duration-300">
                  <canvas
                    ref={(canvasElement) => {
                      if (canvasElement && pageData.canvas) {
                        const ctx = canvasElement.getContext("2d");
                        if (ctx) {
                          canvasElement.width = pageData.canvas.width;
                          canvasElement.height = pageData.canvas.height;
                          ctx.drawImage(pageData.canvas, 0, 0);
                        }
                      }
                    }}
                    className="max-w-full rounded-lg border border-gray-100 max-h-[900px]"
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
