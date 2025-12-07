/**
 * 通讯录API客户端
 */
import { apiClient } from '../apiClient';
import type {
  // 基础类型
  Friendship,
  ContactTag,
  ContactGroup,
  FriendRequest,
  ContactPrivacySetting,
  ContactAnalytics,
  FriendshipStatus,
  
  // 请求类型
  FriendRequestCreate,
  FriendRequestAction,
  UpdateFriendshipRequest,
  UserSearchRequest,
  ContactTagCreate,
  ContactTagUpdate,
  CreateContactGroupRequest,
  UpdateContactGroupRequest,
  UpdateFriendTagsRequest,
  UpdateGroupMembersRequest,
  UpdatePrivacySettingsRequest,
  BatchFriendOperations,
  CreateGroupChatRequest,
  
  // 响应类型
  UserSearchResult,
  TagSuggestion,
  BatchOperationResponse,
  PaginatedFriends,
  PaginatedFriendRequests,
  PaginatedGroupMembers,
  FriendListFilters
} from '@/types/contacts';

// ============================================================================
// 好友管理相关API
// ============================================================================

/**
 * 获取好友列表
 */
export async function getFriends(filters: FriendListFilters & {
  page?: number;
  size?: number;
} = {}): Promise<PaginatedFriends> {
  const params = new URLSearchParams();
  
  // 添加筛选参数
  if (filters.view) params.append('view', filters.view);
  if (filters.tags?.length) {
    filters.tags.forEach(tag => params.append('tags', tag));
  }
  if (filters.groups?.length) {
    filters.groups.forEach(group => params.append('groups', group));
  }
  if (filters.search) params.append('search', filters.search);
  if (filters.status) params.append('status', filters.status);
  if (filters.sort_by) params.append('sort_by', filters.sort_by);
  if (filters.sort_order) params.append('sort_order', filters.sort_order);
  if (filters.page) params.append('page', filters.page.toString());
  if (filters.size) params.append('size', filters.size.toString());
  
  const response = await apiClient.get(`/contacts/friends?${params.toString()}`);
  return response.data;
}

/**
 * 搜索用户
 */
export async function searchUsers(searchRequest: UserSearchRequest): Promise<UserSearchResult[]> {
  // 后端返回 ApiResponse<List[UserSearchResult>]，其中：
  // - name 字段需要映射到前端的 username
  // - is_friend / friendship_status 表示当前用户与该用户之间是否已经存在任何好友关系以及其状态
  const response = await apiClient.post<any[]>('/contacts/friends/search', searchRequest);
  const items = response.data || [];
  
  return items.map((item) => {
    const friendshipStatus = (item.friendship_status || undefined) as FriendshipStatus | undefined;
    // 只要存在任何好友关系（包括 pending/accepted 等），就认为已经有关联关系，不再展示“添加”按钮
    const hasRelationship = Boolean(friendshipStatus) || Boolean(item.is_friend);

    return {
      id: item.id,
      username: item.name || item.username || '未知用户', // 映射 name 到 username
      avatar: item.avatar,
      roles: [], // 后端未返回 roles，给默认空数组
      is_friend: hasRelationship,
      friendship_status: friendshipStatus,
      // 保留可能的额外字段
      email: item.email,
      phone: item.phone,
      mutual_friends_count: item.mutual_friends_count ?? 0
    } as UserSearchResult;
  });
}

/**
 * 发送好友请求
 */
export async function sendFriendRequest(request: FriendRequestCreate): Promise<FriendRequest> {
  const response = await apiClient.post('/contacts/friends/request', request);
  return response.data;
}

/**
 * 获取好友请求列表
 */
export async function getFriendRequests(
  type: 'sent' | 'received' = 'received',
  status?: FriendshipStatus,
  page: number = 1,
  size: number = 20
): Promise<PaginatedFriendRequests> {
  const params = new URLSearchParams({
    type,
    page: page.toString(),
    size: size.toString()
  });
  
  if (status) params.append('status', status);
  
  const response = await apiClient.get(`/contacts/friends/requests?${params.toString()}`);
  return response.data;
}

/**
 * 处理好友请求
 */
export async function handleFriendRequest(requestId: string, action: FriendRequestAction): Promise<void> {
  await apiClient.put(`/contacts/friends/requests/${requestId}`, action);
}

/**
 * 更新好友关系
 */
export async function updateFriendship(friendshipId: string, updateData: UpdateFriendshipRequest): Promise<Friendship> {
  const response = await apiClient.put(`/contacts/friends/${friendshipId}`, updateData);
  return response.data;
}

/**
 * 删除好友关系
 */
export async function deleteFriendship(friendshipId: string): Promise<void> {
  await apiClient.delete(`/contacts/friends/${friendshipId}`);
}

/**
 * 批量好友操作
 */
export async function batchFriendOperations(operations: BatchFriendOperations): Promise<BatchOperationResponse> {
  const response = await apiClient.post('/contacts/friends/batch', operations);
  return response.data;
}

// ============================================================================
// 标签管理相关API
// ============================================================================

/**
 * 获取联系人标签
 */
export async function getContactTags(
  category?: TagCategory,
  includeSystem: boolean = true
): Promise<ContactTag[]> {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  params.append('include_system', includeSystem.toString());
  
  const response = await apiClient.get(`/contacts/tags?${params.toString()}`);
  return response.data;
}

/**
 * 创建联系人标签
 */
export async function createContactTag(tagData: ContactTagCreate): Promise<ContactTag> {
  const response = await apiClient.post('/contacts/tags', tagData);
  return response.data;
}

/**
 * 更新联系人标签
 */
export async function updateContactTag(tagId: string, updateData: ContactTagUpdate): Promise<ContactTag> {
  const response = await apiClient.put(`/contacts/tags/${tagId}`, updateData);
  return response.data;
}

/**
 * 删除联系人标签
 */
export async function deleteContactTag(tagId: string): Promise<void> {
  await apiClient.delete(`/contacts/tags/${tagId}`);
}

/**
 * 更新好友标签
 */
export async function updateFriendTags(friendshipId: string, tagUpdate: UpdateFriendTagsRequest): Promise<void> {
  await apiClient.put(`/contacts/friends/${friendshipId}/tags`, tagUpdate);
}

/**
 * 获取指定标签的好友列表
 */
export async function getFriendsByTag(
  tagId: string,
  page: number = 1,
  size: number = 20
): Promise<PaginatedFriends> {
  const params = new URLSearchParams({
    page: page.toString(),
    size: size.toString()
  });
  
  const response = await apiClient.get(`/contacts/tags/${tagId}/friends?${params.toString()}`);
  return response.data;
}

/**
 * 获取智能标签推荐
 */
export async function getTagSuggestions(friendshipId?: string): Promise<TagSuggestion[]> {
  const params = new URLSearchParams();
  if (friendshipId) params.append('friendship_id', friendshipId);
  
  const response = await apiClient.get(`/contacts/tags/suggestions?${params.toString()}`);
  return response.data;
}

// ============================================================================
// 分组管理相关API
// ============================================================================

/**
 * 获取联系人分组
 */
export async function getContactGroups(includeMembers: boolean = false): Promise<ContactGroup[]> {
  const params = new URLSearchParams({
    include_members: includeMembers.toString()
  });
  
  const response = await apiClient.get(`/contacts/groups?${params.toString()}`);
  return response.data;
}

/**
 * 创建联系人分组
 */
export async function createContactGroup(groupData: CreateContactGroupRequest): Promise<ContactGroup> {
  const response = await apiClient.post('/contacts/groups', groupData);
  return response.data;
}

/**
 * 更新联系人分组
 */
export async function updateContactGroup(groupId: string, updateData: UpdateContactGroupRequest): Promise<ContactGroup> {
  const response = await apiClient.put(`/contacts/groups/${groupId}`, updateData);
  return response.data;
}

/**
 * 删除联系人分组
 */
export async function deleteContactGroup(groupId: string): Promise<void> {
  await apiClient.delete(`/contacts/groups/${groupId}`);
}

/**
 * 获取分组成员
 */
export async function getGroupMembers(
  groupId: string,
  page: number = 1,
  size: number = 50
): Promise<PaginatedGroupMembers> {
  const params = new URLSearchParams({
    page: page.toString(),
    size: size.toString()
  });
  
  const response = await apiClient.get(`/contacts/groups/${groupId}/members?${params.toString()}`);
  return response.data;
}

/**
 * 更新分组成员
 */
export async function updateGroupMembers(groupId: string, memberUpdate: UpdateGroupMembersRequest): Promise<void> {
  await apiClient.put(`/contacts/groups/${groupId}/members`, memberUpdate);
}

/**
 * 基于分组创建群聊
 */
export async function createGroupChat(groupId: string, chatConfig: CreateGroupChatRequest): Promise<any> {
  const response = await apiClient.post(`/contacts/groups/${groupId}/chat`, chatConfig);
  return response.data;
}

// ============================================================================
// 隐私设置相关API
// ============================================================================

/**
 * 获取联系人隐私设置
 */
export async function getContactPrivacySettings(): Promise<ContactPrivacySetting> {
  const response = await apiClient.get('/contacts/privacy');
  return response.data;
}

/**
 * 更新联系人隐私设置
 */
export async function updateContactPrivacySettings(settings: UpdatePrivacySettingsRequest): Promise<ContactPrivacySetting> {
  const response = await apiClient.put('/contacts/privacy', settings);
  return response.data;
}

// ============================================================================
// 统计分析相关API
// ============================================================================

/**
 * 获取联系人使用统计
 */
export async function getContactAnalytics(period: 'week' | 'month' | 'quarter' | 'year' = 'month'): Promise<ContactAnalytics> {
  const params = new URLSearchParams({ period });
  
  const response = await apiClient.get(`/contacts/analytics?${params.toString()}`);
  return response.data;
}



