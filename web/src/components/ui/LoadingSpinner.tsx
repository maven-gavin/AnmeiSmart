'use client';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
}

export default function LoadingSpinner({ size = 'medium' }: LoadingSpinnerProps) {
  const sizeClasses = {
    small: 'h-6 w-6 border-2',
    medium: 'h-12 w-12 border-4',
    large: 'h-16 w-16 border-4'
  };

  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className={`${sizeClasses[size]} animate-spin rounded-full border-orange-500 border-t-transparent`}></div>
    </div>
  );
} 