'use client';

import { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Resource } from '@/service/resourceService';

interface ResourceTransferProps {
  availableResources: Resource[];
  assignedResources: Resource[];
  onAssign: (resourceIds: string[]) => Promise<void>;
  onUnassign: (resourceIds: string[]) => Promise<void>;
  loading?: boolean;
}

export default function ResourceTransfer({
  availableResources,
  assignedResources,
  onAssign,
  onUnassign,
  loading = false,
}: ResourceTransferProps) {
  // 左侧：未绑定的资源
  const [leftSearchText, setLeftSearchText] = useState('');
  const [leftSelectedIds, setLeftSelectedIds] = useState<string[]>([]);
  
  // 右侧：已绑定的资源
  const [rightSearchText, setRightSearchText] = useState('');
  const [rightSelectedIds, setRightSelectedIds] = useState<string[]>([]);

  // 计算未绑定的资源（所有资源中排除已绑定的）
  const unassignedResources = useMemo(() => {
    const assignedIds = new Set(assignedResources.map(r => r.id));
    return availableResources.filter(r => !assignedIds.has(r.id));
  }, [availableResources, assignedResources]);

  // 左侧过滤后的资源
  const filteredLeftResources = useMemo(() => {
    if (!leftSearchText.trim()) return unassignedResources;
    const searchLower = leftSearchText.toLowerCase();
    return unassignedResources.filter(r =>
      r.name.toLowerCase().includes(searchLower) ||
      (r.displayName && r.displayName.toLowerCase().includes(searchLower)) ||
      r.resourcePath.toLowerCase().includes(searchLower) ||
      (r.description && r.description.toLowerCase().includes(searchLower))
    );
  }, [unassignedResources, leftSearchText]);

  // 右侧过滤后的资源
  const filteredRightResources = useMemo(() => {
    if (!rightSearchText.trim()) return assignedResources;
    const searchLower = rightSearchText.toLowerCase();
    return assignedResources.filter(r =>
      r.name.toLowerCase().includes(searchLower) ||
      (r.displayName && r.displayName.toLowerCase().includes(searchLower)) ||
      r.resourcePath.toLowerCase().includes(searchLower) ||
      (r.description && r.description.toLowerCase().includes(searchLower))
    );
  }, [assignedResources, rightSearchText]);

  // 左侧全选/取消全选
  const leftAllSelected = filteredLeftResources.length > 0 && 
    filteredLeftResources.every(r => leftSelectedIds.includes(r.id));
  const leftSomeSelected = filteredLeftResources.some(r => leftSelectedIds.includes(r.id));

  // 右侧全选/取消全选
  const rightAllSelected = filteredRightResources.length > 0 && 
    filteredRightResources.every(r => rightSelectedIds.includes(r.id));
  const rightSomeSelected = filteredRightResources.some(r => rightSelectedIds.includes(r.id));

  const handleLeftSelectAll = (checked: boolean) => {
    if (checked) {
      setLeftSelectedIds(filteredLeftResources.map(r => r.id));
    } else {
      setLeftSelectedIds([]);
    }
  };

  const handleRightSelectAll = (checked: boolean) => {
    if (checked) {
      setRightSelectedIds(filteredRightResources.map(r => r.id));
    } else {
      setRightSelectedIds([]);
    }
  };

  const handleLeftItemToggle = (resourceId: string, checked: boolean) => {
    if (checked) {
      setLeftSelectedIds([...leftSelectedIds, resourceId]);
    } else {
      setLeftSelectedIds(leftSelectedIds.filter(id => id !== resourceId));
    }
  };

  const handleRightItemToggle = (resourceId: string, checked: boolean) => {
    if (checked) {
      setRightSelectedIds([...rightSelectedIds, resourceId]);
    } else {
      setRightSelectedIds(rightSelectedIds.filter(id => id !== resourceId));
    }
  };

  const handleAssign = async () => {
    if (leftSelectedIds.length === 0) return;
    await onAssign(leftSelectedIds);
    setLeftSelectedIds([]);
    setLeftSearchText('');
  };

  const handleUnassign = async () => {
    if (rightSelectedIds.length === 0) return;
    await onUnassign(rightSelectedIds);
    setRightSelectedIds([]);
    setRightSearchText('');
  };

  // 当资源列表变化时，清除已选中但已不存在的ID
  useEffect(() => {
    const leftIds = new Set(filteredLeftResources.map(r => r.id));
    setLeftSelectedIds(prev => prev.filter(id => leftIds.has(id)));
  }, [filteredLeftResources]);

  useEffect(() => {
    const rightIds = new Set(filteredRightResources.map(r => r.id));
    setRightSelectedIds(prev => prev.filter(id => rightIds.has(id)));
  }, [filteredRightResources]);

  return (
    <div className="flex gap-4 h-[600px]">
      {/* 左侧：未绑定的资源 */}
      <div className="flex-1 flex flex-col border rounded-lg">
        <div className="p-4 border-b bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <Label className="text-sm font-medium">未绑定的资源</Label>
            <span className="text-xs text-gray-500">
              {filteredLeftResources.length} / {unassignedResources.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Input
              placeholder="搜索资源..."
              value={leftSearchText}
              onChange={(e) => setLeftSearchText(e.target.value)}
              className="h-8 text-sm"
            />
            <div className="flex items-center gap-1">
              <Checkbox
                id="left-select-all"
                checked={leftAllSelected}
                onCheckedChange={handleLeftSelectAll}
                className={leftSomeSelected && !leftAllSelected ? 'data-[state=checked]:bg-orange-500' : ''}
              />
              <Label htmlFor="left-select-all" className="text-xs cursor-pointer">
                全选
              </Label>
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {filteredLeftResources.length === 0 ? (
            <div className="flex items-center justify-center h-full text-sm text-gray-500">
              {leftSearchText ? '未找到匹配的资源' : '暂无未绑定的资源'}
            </div>
          ) : (
            <div className="space-y-1">
              {filteredLeftResources.map((resource) => (
                <div
                  key={resource.id}
                  className={`flex items-start gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer ${
                    leftSelectedIds.includes(resource.id) ? 'bg-orange-50' : ''
                  }`}
                  onClick={() => handleLeftItemToggle(resource.id, !leftSelectedIds.includes(resource.id))}
                >
                  <Checkbox
                    id={`left-${resource.id}`}
                    checked={leftSelectedIds.includes(resource.id)}
                    onCheckedChange={(checked) => handleLeftItemToggle(resource.id, checked as boolean)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <Label htmlFor={`left-${resource.id}`} className="flex-1 cursor-pointer">
                    <div className="font-medium text-sm">{resource.displayName || resource.name}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {resource.resourcePath}
                      {resource.httpMethod && ` [${resource.httpMethod}]`}
                    </div>
                    {resource.description && (
                      <div className="text-xs text-gray-400 mt-0.5 line-clamp-1">
                        {resource.description}
                      </div>
                    )}
                  </Label>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="p-3 border-t bg-gray-50">
          <Button
            onClick={handleAssign}
            disabled={leftSelectedIds.length === 0 || loading}
            className="w-full bg-orange-500 hover:bg-orange-600"
            size="sm"
          >
            {loading ? '处理中...' : `确定应用 (${leftSelectedIds.length})`}
          </Button>
        </div>
      </div>

      {/* 中间：箭头 */}
      <div className="flex flex-col items-center justify-center gap-2 text-gray-400">
        <div className="text-xs">→</div>
        <div className="text-xs">←</div>
      </div>

      {/* 右侧：已绑定的资源 */}
      <div className="flex-1 flex flex-col border rounded-lg">
        <div className="p-4 border-b bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <Label className="text-sm font-medium">已绑定的资源</Label>
            <span className="text-xs text-gray-500">
              {filteredRightResources.length} / {assignedResources.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Input
              placeholder="搜索资源..."
              value={rightSearchText}
              onChange={(e) => setRightSearchText(e.target.value)}
              className="h-8 text-sm"
            />
            <div className="flex items-center gap-1">
              <Checkbox
                id="right-select-all"
                checked={rightAllSelected}
                onCheckedChange={handleRightSelectAll}
                className={rightSomeSelected && !rightAllSelected ? 'data-[state=checked]:bg-red-500' : ''}
              />
              <Label htmlFor="right-select-all" className="text-xs cursor-pointer">
                全选
              </Label>
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {filteredRightResources.length === 0 ? (
            <div className="flex items-center justify-center h-full text-sm text-gray-500">
              {rightSearchText ? '未找到匹配的资源' : '暂无已绑定的资源'}
            </div>
          ) : (
            <div className="space-y-1">
              {filteredRightResources.map((resource) => (
                <div
                  key={resource.id}
                  className={`flex items-start gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer ${
                    rightSelectedIds.includes(resource.id) ? 'bg-red-50' : ''
                  }`}
                  onClick={() => handleRightItemToggle(resource.id, !rightSelectedIds.includes(resource.id))}
                >
                  <Checkbox
                    id={`right-${resource.id}`}
                    checked={rightSelectedIds.includes(resource.id)}
                    onCheckedChange={(checked) => handleRightItemToggle(resource.id, checked as boolean)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <Label htmlFor={`right-${resource.id}`} className="flex-1 cursor-pointer">
                    <div className="font-medium text-sm">{resource.displayName || resource.name}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {resource.resourcePath}
                      {resource.httpMethod && ` [${resource.httpMethod}]`}
                    </div>
                    {resource.description && (
                      <div className="text-xs text-gray-400 mt-0.5 line-clamp-1">
                        {resource.description}
                      </div>
                    )}
                  </Label>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="p-3 border-t bg-gray-50">
          <Button
            onClick={handleUnassign}
            disabled={rightSelectedIds.length === 0 || loading}
            className="w-full bg-red-500 hover:bg-red-600"
            size="sm"
          >
            {loading ? '处理中...' : `确定删除 (${rightSelectedIds.length})`}
          </Button>
        </div>
      </div>
    </div>
  );
}

