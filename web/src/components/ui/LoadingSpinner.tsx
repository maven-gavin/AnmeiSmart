import { FC } from 'react';

interface LoadingSpinnerProps {
  className?: string;
  fullScreen?: boolean;
}

const LoadingSpinner: FC<LoadingSpinnerProps> = ({ className, fullScreen = true }) => {
  if (fullScreen) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className={`h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent ${className || ''}`} />
      </div>
    );
  }
  
  return (
    <div className={`animate-spin rounded-full border-4 border-primary border-t-transparent ${className || 'h-12 w-12'}`} />
  );
};

export default LoadingSpinner; 