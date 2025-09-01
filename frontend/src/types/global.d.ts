declare global {
  interface Window {
    pdfjsLib: {
      GlobalWorkerOptions: {
        workerSrc: string;
      };
      getDocument: (options: { data: ArrayBuffer }) => {
        promise: Promise<{
          numPages: number;
          getPage: (pageNumber: number) => Promise<{
            getViewport: (options: { scale: number }) => {
              height: number;
              width: number;
            };
            render: (context: {
              canvasContext: CanvasRenderingContext2D;
              viewport: { height: number; width: number };
            }) => { promise: Promise<void> };
          }>;
        }>;
      };
    };
  }
}

export {};
