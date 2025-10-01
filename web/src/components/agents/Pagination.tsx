import { memo } from 'react';
import { Button } from '@/components/ui/button';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  onPageChange: (page: number) => void;
  onNext: () => void;
  onPrevious: () => void;
}

export const Pagination = memo<PaginationProps>(({
  currentPage,
  totalPages,
  hasNextPage,
  hasPreviousPage,
  onPageChange,
  onNext,
  onPrevious
}) => {
  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="mt-6 flex justify-between items-center">
      <div className="flex space-x-2">
        <Button
          onClick={onPrevious}
          disabled={!hasPreviousPage}
          variant="outline"
          size="sm"
          className="px-3"
        >
          上一页
        </Button>
        
        {Array.from({ length: totalPages }, (_, i) => (
          <Button
            key={i}
            onClick={() => onPageChange(i + 1)}
            variant={currentPage === i + 1 ? "default" : "outline"}
            size="sm"
            className={`px-3 ${currentPage === i + 1 ? 'bg-orange-500 hover:bg-orange-600' : ''}`}
          >
            {i + 1}
          </Button>
        ))}
        
        <Button
          onClick={onNext}
          disabled={!hasNextPage}
          variant="outline"
          size="sm"
          className="px-3"
        >
          下一页
        </Button>
      </div>
    </div>
  );
});

Pagination.displayName = 'Pagination';
