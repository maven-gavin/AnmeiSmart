'use client';

import { useState, useEffect } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import { ContactSidebar } from './ContactSidebar';
import { ContactToolbar } from './ContactToolbar';
import { ContactList } from './ContactList';
import { AddFriendModal } from './AddFriendModal';
import { EditFriendModal } from './EditFriendModal';
import type { 
  Friendship, 
  ContactTag, 
  ContactGroup, 
  FriendListFilters 
} from '@/types/contacts';
import { getFriends, getContactTags, getContactGroups } from '@/service/contacts/api';
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
          // 跳转到聊天页面
          window.location.href = `/chat?friend=${friendId}`;
          break;
        case 'edit':
          const friendship = friends.find(f => f.friend?.id === friendId);
          if (friendship) {
            setEditingFriendship(friendship);
          }
          break;
        case 'remove':
          if (confirm('确定要删除这个好友吗？')) {
            // TODO: 实现删除逻辑
            toast.success('好友删除成功');
            loadFriends();
          }
          break;
        case 'toggle_star':
          // TODO: 实现星标切换逻辑
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
        
        <ContactList
          friends={friends}
          viewMode={viewMode}
          loading={loading}
          pagination={pagination}
          onPageChange={handlePageChange}
          onFriendAction={handleFriendAction}
        />
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



