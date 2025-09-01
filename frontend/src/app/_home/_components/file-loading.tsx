export default function FileLoading() {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="relative">
        <div className="w-16 h-16 border-4 border-indigo-200 border-t-indigo-500 rounded-full animate-spin"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl">📄</span>
        </div>
      </div>
      <p className="mt-6 text-lg text-gray-600 font-medium">
        PDF를 처리하고 있습니다...
      </p>
      <div className="mt-4 w-64 bg-gray-200 rounded-full h-2">
        <div className="w-[70%] bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full animate-pulse" />
      </div>
    </div>
  );
}
