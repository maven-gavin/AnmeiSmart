'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, ChevronLeft, ChevronRight, User } from 'lucide-react';
import digitalHumanService from '@/service/digitalHumanService';
import { DigitalHuman } from '@/types/digital-human';
import { cn } from '@/lib/utils';
import { AvatarCircle } from '@/components/ui/AvatarCircle';

interface DigitalHumanToolbarProps {
  selectedId?: string;
  onSelect: (digitalHuman: DigitalHuman) => void;
  onLoaded?: (items: DigitalHuman[]) => void;
}

export function DigitalHumanToolbar({ 
  selectedId, 
  onSelect,
  onLoaded 
}: DigitalHumanToolbarProps) {
  const [digitalHumans, setDigitalHumans] = useState<DigitalHuman[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setIsLoading(true);
        const data = await digitalHumanService.getDigitalHumans();
        // 过滤活跃的数字人
        const activeItems = data.filter(item => item.status === 'active');
        setDigitalHumans(activeItems);
        if (onLoaded) {
          onLoaded(activeItems);
        }
      } catch (error) {
        console.error('Failed to load digital humans', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchItems();
  }, [onLoaded]);

  const filteredItems = digitalHumans.filter(item => 
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const checkScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
      setShowLeftArrow(scrollLeft > 0);
      setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 1);
    }
  };

  useEffect(() => {
    checkScroll();
    window.addEventListener('resize', checkScroll);
    return () => window.removeEventListener('resize', checkScroll);
  }, [filteredItems]);

  const scroll = (direction: 'left' | 'right') => {
    if (scrollContainerRef.current) {
      const scrollAmount = 240;
      scrollContainerRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  return (
    <div className="flex flex-1 items-center mx-6 overflow-hidden h-12 bg-gray-50/50 rounded-xl border border-gray-100 p-1">
      {/* Search Component */}
      <div className="relative flex items-center w-56 flex-shrink-0 border-r border-gray-200 pr-3 mr-3 ml-1">
        <Search className="absolute left-2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="搜索数字人..."
          className="h-9 w-full rounded-lg bg-transparent pl-9 pr-2 text-sm outline-none placeholder:text-gray-400 focus:bg-white focus:ring-1 focus:ring-orange-100 transition-all"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Scrollable Container */}
      <div className="relative flex flex-1 items-center overflow-hidden group h-full">
        {/* Left Arrow */}
        {showLeftArrow && (
          <button 
            onClick={() => scroll('left')}
            className="absolute left-0 z-10 flex h-full items-center justify-center bg-gradient-to-r from-gray-50 to-transparent px-2 text-gray-500 hover:text-orange-500 transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
        )}

        {/* Digital Human List */}
        <div 
          ref={scrollContainerRef}
          onScroll={checkScroll}
          className="flex items-center space-x-3 overflow-x-auto scrollbar-hide px-2 w-full h-full py-0.5"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {filteredItems.map(item => (
            <button
              key={item.id}
              onClick={() => onSelect(item)}
              className={cn(
                "flex items-center space-x-2 whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium transition-all group/item",
                selectedId === item.id
                  ? "bg-orange-100 text-orange-700 shadow-sm"
                  : "text-gray-600 hover:bg-white hover:shadow-sm hover:text-gray-900"
              )}
            >
              <AvatarCircle
                name={item.name}
                avatar={item.avatar}
                sizeClassName="w-6 h-6"
                className={cn(
                  "border transition-transform",
                  selectedId === item.id ? "border-orange-200 scale-110" : "border-gray-200 group-hover/item:scale-110"
                )}
              />
              <span>{item.name}</span>
            </button>
          ))}
          {filteredItems.length === 0 && !isLoading && (
            <div className="flex items-center text-xs text-gray-400 px-2 space-x-1">
              <User className="h-3 w-3" />
              <span>未找到匹配的数字人</span>
            </div>
          )}
        </div>

        {/* Right Arrow */}
        {showRightArrow && (
          <button 
            onClick={() => scroll('right')}
            className="absolute right-0 z-10 flex h-full items-center justify-center bg-gradient-to-l from-gray-50 to-transparent px-2 text-gray-500 hover:text-orange-500 transition-colors"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
}

