'use client';

import { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Permission } from '@/types/auth';

interface PermissionTransferProps {
  availablePermissions: Permission[];
  assignedPermissions: Permission[];
  onAssign: (permissionIds: string[]) => Promise<void>;
  onUnassign: (permissionIds: string[]) => Promise<void>;
  loading?: boolean;
}

export default function PermissionTransfer({
  availablePermissions,
  assignedPermissions,
  onAssign,
  onUnassign,
  loading = false,
}: PermissionTransferProps) {
  // 左侧：未绑定的权限
  const [leftSearchText, setLeftSearchText] = useState('');
  const [leftSelectedIds, setLeftSelectedIds] = useState<string[]>([]);
  
  // 右侧：已绑定的权限
  const [rightSearchText, setRightSearchText] = useState('');
  const [rightSelectedIds, setRightSelectedIds] = useState<string[]>([]);

  // 计算未绑定的权限（所有权限中排除已绑定的）
  const unassignedPermissions = useMemo(() => {
    const assignedIds = new Set(assignedPermissions.map(p => p.id));
    return availablePermissions.filter(p => !assignedIds.has(p.id));
  }, [availablePermissions, assignedPermissions]);

  // 左侧过滤后的权限
  const filteredLeftPermissions = useMemo(() => {
    if (!leftSearchText.trim()) return unassignedPermissions;
    const searchLower = leftSearchText.toLowerCase();
    return unassignedPermissions.filter(p =>
      p.name.toLowerCase().includes(searchLower) ||
      (p.displayName && p.displayName.toLowerCase().includes(searchLower)) ||
      p.code.toLowerCase().includes(searchLower) ||
      (p.description && p.description.toLowerCase().includes(searchLower))
    );
  }, [unassignedPermissions, leftSearchText]);

  // 右侧过滤后的权限
  const filteredRightPermissions = useMemo(() => {
    if (!rightSearchText.trim()) return assignedPermissions;
    const searchLower = rightSearchText.toLowerCase();
    return assignedPermissions.filter(p =>
      p.name.toLowerCase().includes(searchLower) ||
      (p.displayName && p.displayName.toLowerCase().includes(searchLower)) ||
      p.code.toLowerCase().includes(searchLower) ||
      (p.description && p.description.toLowerCase().includes(searchLower))
    );
  }, [assignedPermissions, rightSearchText]);

  // 左侧全选/取消全选
  const leftAllSelected = filteredLeftPermissions.length > 0 && 
    filteredLeftPermissions.every(p => leftSelectedIds.includes(p.id));
  const leftSomeSelected = filteredLeftPermissions.some(p => leftSelectedIds.includes(p.id));

  // 右侧全选/取消全选
  const rightAllSelected = filteredRightPermissions.length > 0 && 
    filteredRightPermissions.every(p => rightSelectedIds.includes(p.id));
  const rightSomeSelected = filteredRightPermissions.some(p => rightSelectedIds.includes(p.id));

  const handleLeftSelectAll = (checked: boolean) => {
    if (checked) {
      setLeftSelectedIds(filteredLeftPermissions.map(p => p.id));
    } else {
      setLeftSelectedIds([]);
    }
  };

  const handleRightSelectAll = (checked: boolean) => {
    if (checked) {
      setRightSelectedIds(filteredRightPermissions.map(p => p.id));
    } else {
      setRightSelectedIds([]);
    }
  };

  const handleLeftItemToggle = (permissionId: string, checked: boolean) => {
    if (checked) {
      setLeftSelectedIds([...leftSelectedIds, permissionId]);
    } else {
      setLeftSelectedIds(leftSelectedIds.filter(id => id !== permissionId));
    }
  };

  const handleRightItemToggle = (permissionId: string, checked: boolean) => {
    if (checked) {
      setRightSelectedIds([...rightSelectedIds, permissionId]);
    } else {
      setRightSelectedIds(rightSelectedIds.filter(id => id !== permissionId));
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

  // 当权限列表变化时，清除已选中但已不存在的ID
  useEffect(() => {
    const leftIds = new Set(filteredLeftPermissions.map(p => p.id));
    setLeftSelectedIds(prev => prev.filter(id => leftIds.has(id)));
  }, [filteredLeftPermissions]);

  useEffect(() => {
    const rightIds = new Set(filteredRightPermissions.map(p => p.id));
    setRightSelectedIds(prev => prev.filter(id => rightIds.has(id)));
  }, [filteredRightPermissions]);

  return (
    <div className="flex gap-4 h-[600px]">
      {/* 左侧：未绑定的权限 */}
      <div className="flex-1 flex flex-col border rounded-lg">
        <div className="p-4 border-b bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <Label className="text-sm font-medium">未绑定的权限</Label>
            <span className="text-xs text-gray-500">
              {filteredLeftPermissions.length} / {unassignedPermissions.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Input
              placeholder="搜索权限..."
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
          {filteredLeftPermissions.length === 0 ? (
            <div className="flex items-center justify-center h-full text-sm text-gray-500">
              {leftSearchText ? '未找到匹配的权限' : '暂无未绑定的权限'}
            </div>
          ) : (
            <div className="space-y-1">
              {filteredLeftPermissions.map((permission) => (
                <div
                  key={permission.id}
                  className={`flex items-start gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer ${
                    leftSelectedIds.includes(permission.id) ? 'bg-orange-50' : ''
                  }`}
                  onClick={() => handleLeftItemToggle(permission.id, !leftSelectedIds.includes(permission.id))}
                >
                  <Checkbox
                    id={`left-${permission.id}`}
                    checked={leftSelectedIds.includes(permission.id)}
                    onCheckedChange={(checked) => handleLeftItemToggle(permission.id, checked as boolean)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <Label htmlFor={`left-${permission.id}`} className="flex-1 cursor-pointer">
                    <div className="font-medium text-sm">{permission.displayName || permission.name}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {permission.code}
                    </div>
                    {permission.description && (
                      <div className="text-xs text-gray-400 mt-0.5 line-clamp-1">
                        {permission.description}
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

      {/* 右侧：已绑定的权限 */}
      <div className="flex-1 flex flex-col border rounded-lg">
        <div className="p-4 border-b bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <Label className="text-sm font-medium">已绑定的权限</Label>
            <span className="text-xs text-gray-500">
              {filteredRightPermissions.length} / {assignedPermissions.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Input
              placeholder="搜索权限..."
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
          {filteredRightPermissions.length === 0 ? (
            <div className="flex items-center justify-center h-full text-sm text-gray-500">
              {rightSearchText ? '未找到匹配的权限' : '暂无已绑定的权限'}
            </div>
          ) : (
            <div className="space-y-1">
              {filteredRightPermissions.map((permission) => (
                <div
                  key={permission.id}
                  className={`flex items-start gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer ${
                    rightSelectedIds.includes(permission.id) ? 'bg-red-50' : ''
                  }`}
                  onClick={() => handleRightItemToggle(permission.id, !rightSelectedIds.includes(permission.id))}
                >
                  <Checkbox
                    id={`right-${permission.id}`}
                    checked={rightSelectedIds.includes(permission.id)}
                    onCheckedChange={(checked) => handleRightItemToggle(permission.id, checked as boolean)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <Label htmlFor={`right-${permission.id}`} className="flex-1 cursor-pointer">
                    <div className="font-medium text-sm">{permission.displayName || permission.name}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {permission.code}
                    </div>
                    {permission.description && (
                      <div className="text-xs text-gray-400 mt-0.5 line-clamp-1">
                        {permission.description}
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

