'use client';

import { useState, useEffect } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import { ContactSidebar } from './ContactSidebar';
import { ContactToolbar } from './ContactToolbar';
import { ContactList } from './ContactList';
import { AddFriendModal } from './AddFriendModal';
import { EditFriendModal } from './EditFriendModal';
import { FriendRequestList } from './FriendRequestList';
import { TagManagementPanel } from './TagManagement/TagManagementPanel';
import type { 
  Friendship, 
  ContactTag, 
  ContactGroup, 
  FriendListFilters 
} from '@/types/contacts';
import { getFriends, getContactTags, getContactGroups, deleteFriendship, updateFriendship } from '@/service/contacts/api';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { toast } from 'react-hot-toast';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { EnhancedPagination } from '@/components/ui/pagination';

interface ContactBookManagementPanelProps {
  // 可以添加额外的props
}

export function ContactBookManagementPanel({}: ContactBookManagementPanelProps) {
  const { user } = useAuthContext();
  
  // 状态管理
  const [selectedView, setSelectedView] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'list' | 'card'>('list');
  const [sortBy, setSortBy] = useState<'name' | 'recent' | 'added' | 'interaction'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  // 数据状态
  const [friends, setFriends] = useState<Friendship[]>([]);
  const [tags, setTags] = useState<ContactTag[]>([]);
  const [groups, setGroups] = useState<ContactGroup[]>([]);
  const [loading, setLoading] = useState(true);
  
  // 分页状态 - 使用与用户管理一致的方式
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(20);
  const [total, setTotal] = useState(0);
  
  // 弹窗状态
  const [showAddFriendModal, setShowAddFriendModal] = useState(false);
  const [editingFriendship, setEditingFriendship] = useState<Friendship | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deletingFriendship, setDeletingFriendship] = useState<Friendship | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  
  // WebSocket 实时功能 - 使用全局 WebSocket 上下文
  const websocketState = useWebSocket();
  
  // 处理 WebSocket 事件（统一使用 action/data 结构）
  useEffect(() => {
    if (!websocketState.lastMessage) return;

    const { action, data } = websocketState.lastMessage;
    if (!action) return;

    switch (action) {
      case 'friend_request_received':
        toast.success('收到新的好友请求');
        if (selectedView === 'pending') {
          loadFriends();
        }
        break;
        
      case 'friend_request_accepted':
        toast.success('您的好友请求已被接受');
        loadFriends();
        break;
        
      case 'friend_online_status_changed':
        // 更新好友在线状态，data 中包含 friend_id / is_online 等信息
        setFriends(prev => prev.map(f => 
          f.friend?.id === data.friend_id 
            ? { ...f, friend: { ...f.friend!, isOnline: data.is_online } }
            : f
        ));
        break;
        
      default:
        console.log('未知的通讯录 WebSocket 事件:', action, data);
    }
  }, [websocketState.lastMessage, selectedView]);
  
  // 加载数据
  useEffect(() => {
    loadInitialData();
  }, [user?.id]);
  
  // 当筛选条件或分页变化时重新加载数据
  useEffect(() => {
    if (user?.id) {
      loadFriends();
    }
  }, [selectedView, searchQuery, selectedTags, selectedGroups, sortBy, sortOrder, currentPage, itemsPerPage]);
  
  // 确保删除过程中对话框保持打开
  useEffect(() => {
    if (deleteLoading && !isDeleteDialogOpen) {
      setIsDeleteDialogOpen(true);
    }
  }, [deleteLoading, isDeleteDialogOpen]);
  
  // 修复：确保对话框关闭时清理 body 的 pointer-events 样式
  // Radix UI 有时在状态不同步时不会正确清理样式
  useEffect(() => {
    if (!isDeleteDialogOpen) {
      // 使用 requestAnimationFrame 确保在下一帧清理，此时 Radix UI 应该已经完成清理
      const frameId = requestAnimationFrame(() => {
        // 再次检查，确保在下一帧清理
        requestAnimationFrame(() => {
          if (document.body.style.pointerEvents === 'none') {
            document.body.style.removeProperty('pointer-events');
          }
          // 同时清理可能的 overflow 样式
          if (document.body.style.overflow === 'hidden') {
            document.body.style.removeProperty('overflow');
          }
        });
      });
      
      return () => cancelAnimationFrame(frameId);
    }
  }, [isDeleteDialogOpen]);
  
  const loadInitialData = async () => {
    if (!user?.id) return;
    
    try {
      // 并行加载基础数据
      const [tagsData, groupsData] = await Promise.all([
        getContactTags(),
        getContactGroups()
      ]);
      
      setTags(tagsData);
      setGroups(groupsData);
      
      // 加载好友列表（loadFriends 自己管理 loading 状态）
      await loadFriends();
      
    } catch (error) {
      console.error('加载初始数据失败:', error);
      toast.error('加载数据失败');
      setLoading(false);
    }
  };
  
  const loadFriends = async () => {
    if (!user?.id) return;
    
    try {
      setLoading(true);
      const validViews: Array<'all' | 'starred' | 'recent' | 'pending' | 'blocked'> = ['all', 'starred', 'recent', 'pending', 'blocked'];
      const filters: FriendListFilters = {
        view: (selectedView === 'all' || !validViews.includes(selectedView as any)) 
          ? undefined 
          : (selectedView as 'starred' | 'recent' | 'pending' | 'blocked'),
        tags: selectedTags.length > 0 ? selectedTags : undefined,
        groups: selectedGroups.length > 0 ? selectedGroups : undefined,
        search: searchQuery || undefined,
        sort_by: sortBy,
        sort_order: sortOrder
      };
      
      const result = await getFriends({
        ...filters,
        page: currentPage,
        size: itemsPerPage
      });
      
      setFriends(result.items);
      setTotal(result.total);
      
    } catch (error) {
      console.error('加载好友列表失败:', error);
      toast.error('加载好友列表失败');
    } finally {
      setLoading(false);
    }
  };
  
  // 事件处理函数
  const handleViewChange = (view: string) => {
    setSelectedView(view);
    setCurrentPage(1); // 重置到第一页
  };
  
  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1); // 重置到第一页
  };
  
  const handleTagsChange = (tagIds: string[]) => {
    setSelectedTags(tagIds);
    setCurrentPage(1); // 重置到第一页
  };
  
  const handleGroupsChange = (groupIds: string[]) => {
    setSelectedGroups(groupIds);
    setCurrentPage(1); // 重置到第一页
  };
  
  const handleSortChange = (field: 'name' | 'recent' | 'added' | 'interaction') => {
    if (field === sortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
    setCurrentPage(1); // 重置到第一页
  };
  
  const handleFriendAction = async (action: string, friendId: string) => {
    try {
      switch (action) {
        case 'chat':
          // 获取或创建与好友的会话，然后跳转
          try {
            const { startConversationWithFriend } = await import('@/service/contacts/chatIntegration');
            const conversation = await startConversationWithFriend(friendId);
            
            // 跳转到聊天页面，指定会话ID
            window.location.href = `/chat?conversation=${conversation.id}`;
          } catch (error) {
            console.error('发起对话失败:', error);
            toast.error('发起对话失败，请重试');
          }
          break;
        case 'edit': {
          const friendship = friends.find(f => f.friend?.id === friendId);
          if (friendship) {
            setEditingFriendship(friendship);
          }
          break;
        }
        case 'remove': {
          const friendship = friends.find(f => f.friend?.id === friendId);
          if (friendship) {
            setDeletingFriendship(friendship);
            setIsDeleteDialogOpen(true);
          }
          break;
        }
        case 'toggle_star': {
          const targetFriendship = friends.find(f => f.friend?.id === friendId);
          if (targetFriendship) {
            await updateFriendship(targetFriendship.id, {
              is_starred: !targetFriendship.is_starred
            });
            toast.success(targetFriendship.is_starred ? '已取消星标' : '已设为星标');
            loadFriends();
          }
          break;
        }
        case 'toggle_pin': {
          const targetFriendship = friends.find(f => f.friend?.id === friendId);
          if (targetFriendship) {
            await updateFriendship(targetFriendship.id, {
              is_pinned: !targetFriendship.is_pinned
            });
            toast.success(targetFriendship.is_pinned ? '已取消置顶' : '已置顶显示');
            loadFriends();
          }
          break;
        }
        case 'toggle_mute': {
          const targetFriendship = friends.find(f => f.friend?.id === friendId);
          if (targetFriendship) {
            await updateFriendship(targetFriendship.id, {
              is_muted: !targetFriendship.is_muted
            });
            toast.success(targetFriendship.is_muted ? '已取消免打扰' : '已设为免打扰');
            loadFriends();
          }
          break;
        }
        default:
          console.warn('未知操作:', action);
      }
    } catch (error) {
      console.error('操作失败:', error);
      toast.error('操作失败');
    }
  };
  
  const handleAddFriendSuccess = () => {
    setShowAddFriendModal(false);
    loadFriends();
    toast.success('好友添加成功');
  };
  
  const handleEditFriendSuccess = () => {
    setEditingFriendship(null);
    loadFriends();
    toast.success('好友信息更新成功');
  };
  
  const handleConfirmDelete = async () => {
    if (!deletingFriendship) return;
    
    setDeleteLoading(true);
    try {
      await deleteFriendship(deletingFriendship.id);
      toast.success('好友删除成功');
      setIsDeleteDialogOpen(false);
      setDeletingFriendship(null);
      
      // 如果当前页删除后没有数据了，且不是第一页，则跳转到上一页
      if (friends.length === 1 && currentPage > 1) {
        setCurrentPage(currentPage - 1);
      } else {
        loadFriends();
      }
    } catch (error) {
      console.error('删除好友失败:', error);
      toast.error('删除失败，请重试');
    } finally {
      setDeleteLoading(false);
    }
  };
  
  if (!user) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-gray-500">请先登录</p>
      </div>
    );
  }
  
  return (
    <div className="flex h-full bg-gray-50">
      {/* 左侧导航栏 */}
      <ContactSidebar
        selectedView={selectedView}
        onViewChange={handleViewChange}
        tags={tags}
        groups={groups}
        friendsCount={total}
        loading={loading}
      />
      
      {/* 主内容区 */}
      <div className="flex-1 flex flex-col">
        <ContactToolbar
          searchQuery={searchQuery}
          onSearchChange={handleSearchChange}
          selectedTags={selectedTags}
          onTagsChange={handleTagsChange}
          selectedGroups={selectedGroups}
          onGroupsChange={handleGroupsChange}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSortChange={handleSortChange}
          onAddFriend={() => setShowAddFriendModal(true)}
          tags={tags}
          groups={groups}
        />
        
        {/* 根据选择的视图显示不同内容 */}
        {selectedView === 'pending' ? (
          <div className="flex-1 overflow-auto p-4">
            <FriendRequestList onRequestHandled={loadFriends} />
          </div>
        ) : selectedView === 'tag_management' ? (
          <div className="flex-1 overflow-auto p-4">
            <TagManagementPanel />
          </div>
        ) : selectedView === 'privacy' ? (
          <div className="flex-1 overflow-auto p-4">
            <div className="bg-white rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">隐私设置</h2>
              <p className="text-gray-500">隐私设置功能开发中...</p>
            </div>
          </div>
        ) : selectedView === 'analytics' ? (
          <div className="flex-1 overflow-auto p-4">
            <div className="bg-white rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">使用统计</h2>
              <p className="text-gray-500">统计功能开发中...</p>
            </div>
          </div>
        ) : (
          <ContactList
            friends={friends}
            viewMode={viewMode}
            loading={loading}
            total={total}
            currentPage={currentPage}
            itemsPerPage={itemsPerPage}
            onPageChange={setCurrentPage}
            onItemsPerPageChange={(newLimit) => {
              setItemsPerPage(newLimit);
              setCurrentPage(1);
            }}
            onFriendAction={handleFriendAction}
          />
        )}
      </div>
      
      {/* 弹窗组件 */}
      {showAddFriendModal && (
        <AddFriendModal
          onClose={() => setShowAddFriendModal(false)}
          onSuccess={handleAddFriendSuccess}
        />
      )}
      
      {editingFriendship && (
        <EditFriendModal
          friendship={editingFriendship}
          onClose={() => setEditingFriendship(null)}
          onSuccess={handleEditFriendSuccess}
          tags={tags}
        />
      )}
      
      {/* 删除确认对话框 */}
      <AlertDialog
        open={isDeleteDialogOpen}
        onOpenChange={(open) => {
          if (open) {
            setIsDeleteDialogOpen(true);
          } else {
            // 如果正在删除，不允许关闭
            if (deleteLoading) return;
            setIsDeleteDialogOpen(false);
            setDeletingFriendship(null);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除好友</AlertDialogTitle>
            <AlertDialogDescription>
              删除后无法恢复，确定要删除好友
              <span className="font-semibold text-gray-900">
                {deletingFriendship?.nickname || deletingFriendship?.friend?.username}
              </span>
              吗？
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel 
              onClick={() => {
                if (deleteLoading) return;
                setIsDeleteDialogOpen(false);
                setDeletingFriendship(null);
              }}
              disabled={deleteLoading}
            >
              取消
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-red-600 hover:bg-red-700"
              disabled={deleteLoading}
            >
              {deleteLoading ? '删除中...' : '确认删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}



