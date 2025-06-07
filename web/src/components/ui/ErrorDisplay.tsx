interface ErrorDisplayProps {
  error: string;
  showRedirectMessage?: boolean;
  redirectMessage?: string;
}

export function ErrorDisplay({ 
  error, 
  showRedirectMessage = true,
  redirectMessage = "正在重定向..." 
}: ErrorDisplayProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mb-4 rounded-full bg-red-100 p-3 mx-auto w-fit">
          <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <div className="text-red-500 text-lg mb-2">{error}</div>
        {showRedirectMessage && (
          <div className="text-gray-500 text-sm">{redirectMessage}</div>
        )}
      </div>
    </div>
  );
} 