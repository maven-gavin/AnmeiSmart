import { useState, useMemo, useCallback } from 'react';

export function usePagination<T>(items: T[], itemsPerPage: number = 5) {
  const [currentPage, setCurrentPage] = useState(1);

  const paginatedData = useMemo(() => {
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    const currentItems = items.slice(indexOfFirstItem, indexOfLastItem);
    const totalPages = Math.ceil(items.length / itemsPerPage);

    return {
      currentItems,
      totalPages,
      currentPage,
      hasNextPage: currentPage < totalPages,
      hasPreviousPage: currentPage > 1
    };
  }, [items, currentPage, itemsPerPage]);

  const goToPage = useCallback((pageNumber: number) => {
    setCurrentPage(pageNumber);
  }, []);

  const nextPage = useCallback(() => {
    if (paginatedData.hasNextPage) {
      setCurrentPage(prev => prev + 1);
    }
  }, [paginatedData.hasNextPage]);

  const previousPage = useCallback(() => {
    if (paginatedData.hasPreviousPage) {
      setCurrentPage(prev => prev - 1);
    }
  }, [paginatedData.hasPreviousPage]);

  const resetPage = useCallback(() => {
    setCurrentPage(1);
  }, []);

  return {
    ...paginatedData,
    goToPage,
    nextPage,
    previousPage,
    resetPage
  };
}
