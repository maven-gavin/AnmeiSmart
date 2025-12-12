'use client';

import * as React from 'react';
import { Check, ChevronsUpDown, Search, User as UserIcon } from 'lucide-react';
import { cn } from '@/service/utils';
import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

export interface UserOption {
  id: string;
  username: string;
  email: string;
}

interface UserComboboxProps {
  value?: string;
  onValueChange: (value: string) => void;
  users: UserOption[];
  onSearch?: (searchText: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyText?: string;
  className?: string;
}

export function UserCombobox({
  value,
  onValueChange,
  users,
  onSearch,
  isLoading = false,
  disabled = false,
  placeholder = '选择用户...',
  searchPlaceholder = '搜索用户名或邮箱...',
  emptyText = '未找到用户',
  className,
}: UserComboboxProps) {
  const [open, setOpen] = React.useState(false);
  const [searchValue, setSearchValue] = React.useState('');

  const selectedUser = users.find((user) => user.id === value);

  const handleSearch = React.useCallback(
    (search: string) => {
      setSearchValue(search);
      if (onSearch && search.length > 0) {
        // 延迟搜索以避免过于频繁的API调用
        const timeoutId = setTimeout(() => {
          onSearch(search);
        }, 300);
        return () => clearTimeout(timeoutId);
      }
    },
    [onSearch]
  );

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled || isLoading}
          className={cn('w-full justify-between', className)}
        >
          {selectedUser ? (
            <div className="flex items-center gap-2 overflow-hidden">
              <UserIcon className="h-4 w-4 shrink-0 text-muted-foreground" />
              <span className="truncate">{selectedUser.username}</span>
              <span className="text-xs text-muted-foreground truncate">
                ({selectedUser.email})
              </span>
            </div>
          ) : (
            <span className="text-muted-foreground">{placeholder}</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full min-w-[400px] p-0" align="start">
        <Command shouldFilter={false}>
          <div className="flex items-center border-b px-3">
            <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
            <CommandInput
              placeholder={searchPlaceholder}
              value={searchValue}
              onValueChange={handleSearch}
              className="flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
          <CommandList>
            {isLoading ? (
              <div className="py-6 text-center text-sm text-muted-foreground">
                <div className="flex items-center justify-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500" />
                  <span>搜索中...</span>
                </div>
              </div>
            ) : (
              <>
                <CommandEmpty>
                  <div className="py-6 text-center">
                    <div className="text-sm text-muted-foreground mb-2">{emptyText}</div>
                    {searchValue && onSearch && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onSearch(searchValue)}
                        className="mt-2"
                      >
                        <Search className="mr-2 h-4 w-4" />
                        搜索 &ldquo;{searchValue}&rdquo;
                      </Button>
                    )}
                  </div>
                </CommandEmpty>
                <CommandGroup>
                  {users.map((user) => (
                    <CommandItem
                      key={user.id}
                      value={user.id}
                      onSelect={(currentValue) => {
                        onValueChange(currentValue === value ? '' : currentValue);
                        setOpen(false);
                      }}
                      className="cursor-pointer"
                    >
                      <Check
                        className={cn(
                          'mr-2 h-4 w-4',
                          value === user.id ? 'opacity-100' : 'opacity-0'
                        )}
                      />
                      <UserIcon className="mr-2 h-4 w-4 text-muted-foreground" />
                      <div className="flex flex-col overflow-hidden">
                        <span className="font-medium truncate">{user.username}</span>
                        <span className="text-xs text-muted-foreground truncate">
                          {user.email}
                        </span>
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

