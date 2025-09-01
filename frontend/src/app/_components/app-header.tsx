"use client";

import { cn } from "@/util/shared";

export default function AppHeader({ className }: { className?: string }) {
  return (
    <header
      className={cn(
        "bg-white/90 backdrop-blur-lg border-b border-white/20 shadow-lg",
        className,
      )}
    >
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* 로고 및 타이틀 섹션 */}
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg">
              <span className="text-white text-2xl">📄</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                PDF Viewer
              </h1>
              <p className="text-sm text-gray-600">
                문서를 쉽고 빠르게 확인하세요
              </p>
            </div>
          </div>
          <button
            type="button"
            className="cursor-pointer px-4 py-2 text-gray-600 hover:text-indigo-600 rounded-xl font-medium transition-all duration-200 flex items-center space-x-2"
            onClick={() => {
              navigator.clipboard.writeText(window.location.href);
            }}
          >
            <span>🔗</span>
            <span>URL 공유</span>
          </button>
        </div>
      </div>
    </header>
  );
}
