import { memo } from 'react';

export const LoadingSpinner = memo(() => {
  return (
    <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
    </div>
  );
});

LoadingSpinner.displayName = 'LoadingSpinner';
