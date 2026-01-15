/**
 * 通讯录相关的TypeScript类型定义
 */

// 枚举类型
export type FriendshipStatus = 'pending' | 'accepted' | 'blocked' | 'deleted';
export type TagCategory = 'work' | 'personal' | 'business' | 'custom';
export type GroupType = 'personal' | 'work' | 'project' | 'temporary';
export type GroupMemberRole = 'member' | 'admin' | 'owner';
export type InteractionType = 'chat_started' | 'message_sent' | 'call_made' | 'meeting_scheduled' | 'profile_viewed' | 'tag_added' | 'group_added';

// 基础接口
export interface ContactTag {
  id: string;
  user_id: string;
  name: string;
  color: string;
  icon?: string;
  description?: string;
  category: TagCategory;
  is_system_tag: boolean;
  display_order: number;
  is_visible: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface Friendship {
  id: string;
  user_id: string;
  friend_id: string;
  status: FriendshipStatus;
  nickname?: string;
  remark?: string;
  source?: string;
  is_starred: boolean;
  is_muted: boolean;
  is_pinned: boolean;
  is_blocked: boolean;
  requested_at: string;
  accepted_at?: string;
  last_interaction_at?: string;
  interaction_count: number;
  created_at: string;
  updated_at: string;
  
  // 关联数据
  friend?: {
    id: string;
    username: string;
    avatar?: string;
    roles: string[];
  };
  tags: ContactTag[];
}

export interface ContactGroup {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  avatar?: string;
  group_type: GroupType;
  color_theme: string;
  display_order: number;
  is_collapsed: boolean;
  max_members?: number;
  is_private: boolean;
  member_count: number;
  created_at: string;
  updated_at: string;
  
  // 可选的成员信息
  members?: GroupMember[];
}

export interface GroupMember {
  id: string;
  group_id: string;
  friendship_id: string;
  role: GroupMemberRole;
  joined_at: string;
  invited_by?: string;
  
  // 关联的好友信息
  friendship?: Friendship;
}

export interface ContactPrivacySetting {
  id: string;
  user_id: string;
  allow_search_by_phone: boolean;
  allow_search_by_email: boolean;
  allow_search_by_username: boolean;
  auto_accept_from_contacts: boolean;
  require_verification_message: boolean;
  show_online_status: boolean;
  show_last_seen: boolean;
  show_profile_to_friends: boolean;
  created_at: string;
  updated_at: string;
}

export interface InteractionRecord {
  id: string;
  friendship_id: string;
  interaction_type: InteractionType;
  related_object_type?: string;
  related_object_id?: string;
  interaction_data?: any;
  occurred_at: string;
  created_at: string;
}

// 请求类型
export interface FriendRequestCreate {
  friend_id: string;
  verification_message?: string;
  source?: string;
}

export interface FriendRequestAction {
  action: 'accept' | 'reject';
  message?: string;
}

export interface UpdateFriendshipRequest {
  nickname?: string;
  remark?: string;
  is_starred?: boolean;
  is_muted?: boolean;
  is_pinned?: boolean;
}

export interface UserSearchRequest {
  query: string;
  search_type?: 'all' | 'phone' | 'email' | 'username';
  limit?: number;
}

export interface UserSearchResult {
  id: string;
  username: string;
  avatar?: string;
  roles: string[];
  is_friend: boolean;
  friendship_status?: FriendshipStatus;
}

export interface FriendRequest {
  id: string;
  user_id: string;
  friend_id: string;
  status: FriendshipStatus;
  verification_message?: string;
  source?: string;
  requested_at: string;
  
  // 关联用户信息
  user?: {
    id: string;
    username: string;
    avatar?: string;
  };
  friend?: {
    id: string;
    username: string;
    avatar?: string;
  };
}

export interface ContactTagCreate {
  name: string;
  color?: string;
  icon?: string;
  description?: string;
  category?: TagCategory;
  display_order?: number;
  is_visible?: boolean;
}

export interface ContactTagUpdate {
  name?: string;
  color?: string;
  icon?: string;
  description?: string;
  category?: TagCategory;
  display_order?: number;
  is_visible?: boolean;
}

export interface CreateContactGroupRequest {
  name: string;
  description?: string;
  avatar?: string;
  group_type?: GroupType;
  color_theme?: string;
  display_order?: number;
  is_collapsed?: boolean;
  max_members?: number;
  is_private?: boolean;
}

export interface UpdateContactGroupRequest {
  name?: string;
  description?: string;
  avatar?: string;
  group_type?: GroupType;
  color_theme?: string;
  display_order?: number;
  is_collapsed?: boolean;
  max_members?: number;
  is_private?: boolean;
}

export interface UpdateFriendTagsRequest {
  tag_ids: string[];
}

export interface UpdateGroupMembersRequest {
  add_friendship_ids: string[];
  remove_friendship_ids: string[];
}

export interface UpdatePrivacySettingsRequest {
  allow_search_by_phone?: boolean;
  allow_search_by_email?: boolean;
  allow_search_by_username?: boolean;
  auto_accept_from_contacts?: boolean;
  require_verification_message?: boolean;
  show_online_status?: boolean;
  show_last_seen?: boolean;
  show_profile_to_friends?: boolean;
}

export interface TagSuggestion {
  tag_id?: string;
  name: string;
  color: string;
  reason: string;
  confidence: number;
}

export interface BatchFriendOperations {
  friendship_ids: string[];
  operation: 'add_tags' | 'remove_tags' | 'move_to_group' | 'remove_from_group' | 'star' | 'unstar' | 'mute' | 'unmute';
  operation_data?: any;
}

export interface BatchOperationResponse {
  success_count: number;
  failure_count: number;
  errors: string[];
}

export interface ContactAnalytics {
  total_friends: number;
  active_friends: number;
  total_tags: number;
  total_groups: number;
  interactions_this_week: number;
  top_tags: Array<{
    name: string;
    usage_count: number;
    color: string;
  }>;
  recent_activities: Array<{
    type: string;
    description: string;
    occurred_at: string;
  }>;
}

export interface CreateGroupChatRequest {
  title?: string;
  include_all_members?: boolean;
  member_ids?: string[];
  initial_message?: string;
}

// 分页响应类型
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export type PaginatedFriends = PaginatedResponse<Friendship>;
export type PaginatedFriendRequests = PaginatedResponse<FriendRequest>;
export type PaginatedGroupMembers = PaginatedResponse<GroupMember>;

// 筛选和排序选项
export interface FriendListFilters {
  view?: 'all' | 'starred' | 'recent' | 'blocked' | 'pending';
  tags?: string[];
  groups?: string[];
  search?: string;
  status?: FriendshipStatus;
  sort_by?: 'name' | 'recent' | 'added' | 'interaction';
  sort_order?: 'asc' | 'desc';
}

// 系统预设标签配置
export interface SystemTagConfig {
  [category: string]: {
    name: string;
    tags: Array<{
      name: string;
      color: string;
      icon: string;
    }>;
  };
}

// 常量定义
export const SYSTEM_TAG_CATEGORIES: SystemTagConfig = {
  business: {
    name: "商务关系",
    tags: [
      { name: "客户", color: "#F59E0B", icon: "user-heart" },
      { name: "潜在客户", color: "#F97316", icon: "user-plus" },
      { name: "VIP客户", color: "#DC2626", icon: "star" },
      { name: "供应商", color: "#7C3AED", icon: "truck" },
      { name: "合作伙伴", color: "#10B981", icon: "handshake" }
    ]
  },
  work: {
    name: "工作关系",
    tags: [
      { name: "同事", color: "#3B82F6", icon: "users" },
      { name: "上级", color: "#8B5CF6", icon: "crown" },
      { name: "下属", color: "#06B6D4", icon: "user-check" },
      { name: "HR", color: "#EC4899", icon: "clipboard-list" }
    ]
  },
  personal: {
    name: "个人关系",
    tags: [
      { name: "朋友", color: "#8B5CF6", icon: "user-heart" },
      { name: "家人", color: "#EC4899", icon: "home" },
      { name: "同学", color: "#06B6D4", icon: "graduation-cap" }
    ]
  }
};



