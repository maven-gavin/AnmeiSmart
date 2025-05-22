'use client';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  className?: string;
  fullScreen?: boolean;
}

export default function LoadingSpinner({ 
  size = 'medium', 
  className = '', 
  fullScreen = true 
}: LoadingSpinnerProps) {
  const sizeClasses = {
    small: 'h-6 w-6 border-2',
    medium: 'h-12 w-12 border-4',
    large: 'h-16 w-16 border-4'
  };

  const spinnerClasses = `${sizeClasses[size]} animate-spin rounded-full border-orange-500 border-t-transparent ${className}`;

  if (fullScreen) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className={spinnerClasses}></div>
      </div>
    );
  }

  return <div className={spinnerClasses}></div>;
} 