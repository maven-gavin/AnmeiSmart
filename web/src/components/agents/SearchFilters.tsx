import { memo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FilterState } from '@/hooks/useAgentFilters';

interface SearchFiltersProps {
  filters: FilterState;
  onFilterChange: (key: keyof FilterState, value: string) => void;
  onReset: () => void;
  onSearch: () => void;
}

export const SearchFilters = memo<SearchFiltersProps>(({ 
  filters, 
  onFilterChange, 
  onReset, 
  onSearch 
}) => {
  return (
    <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <span className="text-lg font-medium text-gray-800">组合查询:</span>
        
        <div>
          <Select 
            value={filters.environment} 
            onValueChange={(value) => onFilterChange('environment', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="所有环境" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有环境</SelectItem>
              <SelectItem value="dev">开发环境</SelectItem>
              <SelectItem value="test">测试环境</SelectItem>
              <SelectItem value="prod">生产环境</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Input
            value={filters.appName}
            onChange={(e) => onFilterChange('appName', e.target.value)}
            placeholder="搜索应用名称"
            className="w-full"
          />
        </div>
        
        <div className="flex justify-end space-x-2">
          <Button variant="outline" onClick={onReset}>
            重置
          </Button>
          <Button 
            className="bg-orange-500 hover:bg-orange-600" 
            onClick={onSearch}
          >
            查询
          </Button>
        </div>
      </div>
    </div>
  );
});

SearchFilters.displayName = 'SearchFilters';
