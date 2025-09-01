import { useEffect, useRef, useState } from "react";

interface PageCanvas {
  pageNumber: number;
  canvas: HTMLCanvasElement;
}

export default function usePdfLoad(file: File) {
  const [isLoading, setIsLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(0);
  const [renderedPages, setRenderedPages] = useState<PageCanvas[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  const loadAndRenderPDF = async () => {
    try {
      setIsLoading(true);

      const arrayBuffer = await file.arrayBuffer();
      const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer })
        .promise;

      setTotalPages(pdf.numPages);

      // 모든 페이지를 순차적으로 렌더링
      const pages: PageCanvas[] = [];

      for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        const page = await pdf.getPage(pageNum);
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");

        // 컨텍스트가 null인 경우 건너뛰기
        if (!context) {
          continue;
        }

        // 뷰포트 설정 (스케일 1.5로 고해상도)
        const viewport = page.getViewport({ scale: 1.5 });
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        // 페이지 렌더링
        const renderContext = {
          canvasContext: context,
          viewport: viewport,
        };

        await page.render(renderContext).promise;

        pages.push({
          pageNumber: pageNum,
          canvas: canvas,
        });

        // 실시간으로 렌더링된 페이지 업데이트
        setRenderedPages([...pages]);
      }

      setIsLoading(false);
    } catch {
      alert("PDF 파일을 렌더링하는 중 오류가 발생했습니다.");
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // PDF.js 라이브러리 로드
    const script = document.createElement("script");
    script.src =
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
    script.onload = () => {
      if (window.pdfjsLib) {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc =
          "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
        loadAndRenderPDF();
      }
    };
    document.head.appendChild(script);

    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, [file]);

  return {
    isLoading,
    totalPages,
    renderedPages,
    containerRef,
  };
}
