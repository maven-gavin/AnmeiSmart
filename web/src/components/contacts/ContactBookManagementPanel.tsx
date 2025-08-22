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
import { useWebSocketByPage } from '@/hooks/useWebSocketByPage';
import { toast } from 'react-hot-toast';

interface ContactBookManagementPanelProps {
  // 可以添加额外的props
}

export function ContactBookManagementPanel({}: ContactBookManagementPanelProps) {
  const { user } = useAuthContext();
  
  // 状态管理
  const [selectedView, setSelectedView] = useState<'all' | 'starred' | 'recent' | string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'list' | 'card'>('list');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  // 数据状态
  const [friends, setFriends] = useState<Friendship[]>([]);
  const [tags, setTags] = useState<ContactTag[]>([]);
  const [groups, setGroups] = useState<ContactGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    size: 20,
    total: 0,
    pages: 0,
    hasNext: false,
    hasPrev: false
  });
  
  // 弹窗状态
  const [showAddFriendModal, setShowAddFriendModal] = useState(false);
  const [editingFriendship, setEditingFriendship] = useState<Friendship | null>(null);
  
  // WebSocket实时功能 - 使用现有框架
  const { isConnected, sendMessage } = useWebSocketByPage('contacts', {
    onMessage: (data) => {
      // 处理通讯录相关的WebSocket消息
      const { type, payload } = data;
      
      switch (type) {
        case 'friend_request_received':
          toast.success(`收到来自 ${payload.user?.username} 的好友请求`);
          if (selectedView === 'pending') {
            loadFriends();
          }
          break;
          
        case 'friend_request_accepted':
          toast.success(`${payload.friend?.username} 接受了您的好友请求`);
          loadFriends();
          break;
          
        case 'friend_online_status_changed':
          // 更新好友在线状态
          setFriends(prev => prev.map(f => 
            f.friend?.id === payload.friend_id 
              ? { ...f, friend: { ...f.friend!, isOnline: payload.is_online } }
              : f
          ));
          break;
          
        default:
          console.log('未知的通讯录WebSocket消息:', type);
      }
    }
  });
  
  // 加载数据
  useEffect(() => {
    loadInitialData();
  }, [user?.id]);
  
  // 当筛选条件变化时重新加载数据
  useEffect(() => {
    if (user?.id) {
      loadFriends();
    }
  }, [selectedView, searchQuery, selectedTags, selectedGroups, sortBy, sortOrder, pagination.page]);
  
  const loadInitialData = async () => {
    if (!user?.id) return;
    
    try {
      setLoading(true);
      
      // 并行加载基础数据
      const [tagsData, groupsData] = await Promise.all([
        getContactTags(),
        getContactGroups()
      ]);
      
      setTags(tagsData);
      setGroups(groupsData);
      
      // 加载好友列表
      await loadFriends();
      
    } catch (error) {
      console.error('加载初始数据失败:', error);
      toast.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };
  
  const loadFriends = async () => {
    if (!user?.id) return;
    
    try {
      const filters: FriendListFilters = {
        view: selectedView === 'all' ? undefined : selectedView,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
        groups: selectedGroups.length > 0 ? selectedGroups : undefined,
        search: searchQuery || undefined,
        sort_by: sortBy,
        sort_order: sortOrder
      };
      
      const result = await getFriends({
        ...filters,
        page: pagination.page,
        size: pagination.size
      });
      
      setFriends(result.items);
      setPagination({
        page: result.page,
        size: result.size,
        total: result.total,
        pages: result.pages,
        hasNext: result.has_next,
        hasPrev: result.has_prev
      });
      
    } catch (error) {
      console.error('加载好友列表失败:', error);
      toast.error('加载好友列表失败');
    }
  };
  
  // 事件处理函数
  const handleViewChange = (view: string) => {
    setSelectedView(view);
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一页
  };
  
  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一页
  };
  
  const handleTagsChange = (tagIds: string[]) => {
    setSelectedTags(tagIds);
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一页
  };
  
  const handleGroupsChange = (groupIds: string[]) => {
    setSelectedGroups(groupIds);
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一页
  };
  
  const handleSortChange = (field: string) => {
    if (field === sortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一页
  };
  
  const handlePageChange = (page: number) => {
    setPagination(prev => ({ ...prev, page }));
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
        case 'edit':
          const friendship = friends.find(f => f.friend?.id === friendId);
          if (friendship) {
            setEditingFriendship(friendship);
          }
          break;
        case 'remove':
          if (confirm('确定要删除这个好友吗？')) {
            const friendship = friends.find(f => f.friend?.id === friendId);
            if (friendship) {
              await deleteFriendship(friendship.id);
              toast.success('好友删除成功');
              loadFriends();
            }
          }
          break;
        case 'toggle_star':
          const targetFriendship = friends.find(f => f.friend?.id === friendId);
          if (targetFriendship) {
            await updateFriendship(targetFriendship.id, {
              is_starred: !targetFriendship.is_starred
            });
            toast.success(targetFriendship.is_starred ? '已取消星标' : '已设为星标');
            loadFriends();
          }
          break;
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
        friendsCount={pagination.total}
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
            pagination={pagination}
            onPageChange={handlePageChange}
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
    </div>
  );
}



