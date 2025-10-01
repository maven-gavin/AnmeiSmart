import { memo } from 'react';
import { SearchFilters } from './SearchFilters';
import { AgentGrid } from './AgentGrid';
import { Pagination } from './Pagination';
import { FilterState } from '@/hooks/useAgentFilters';
import { AgentConfig } from '@/service/agentConfigService';

interface AgentExploreProps {
  filters: FilterState;
  currentItems: AgentConfig[];
  currentPage: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  onFilterChange: (key: keyof FilterState, value: string) => void;
  onReset: () => void;
  onSearch: () => void;
  onStartChat: (config: AgentConfig) => void;
  onPageChange: (page: number) => void;
  onNext: () => void;
  onPrevious: () => void;
}

export const AgentExplore = memo<AgentExploreProps>(({
  filters,
  currentItems,
  currentPage,
  totalPages,
  hasNextPage,
  hasPreviousPage,
  onFilterChange,
  onReset,
  onSearch,
  onStartChat,
  onPageChange,
  onNext,
  onPrevious
}) => {
  return (
    <div className="container mx-auto px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Agent探索</h1>
        </div>
      </div>

      <SearchFilters
        filters={filters}
        onFilterChange={onFilterChange}
        onReset={onReset}
        onSearch={onSearch}
      />

      <AgentGrid
        configs={currentItems}
        onStartChat={onStartChat}
      />

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        hasNextPage={hasNextPage}
        hasPreviousPage={hasPreviousPage}
        onPageChange={onPageChange}
        onNext={onNext}
        onPrevious={onPrevious}
      />
    </div>
  );
});

AgentExplore.displayName = 'AgentExplore';
