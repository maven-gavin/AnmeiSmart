import { apiClient } from './apiClient';
import { User, UserRole } from '@/types/auth';

export interface GetUsersParams {
  skip?: number;
  limit?: number;
  search?: string;
}

export interface UserListResponse {
  users: User[];
  total: number;
  skip: number;
  limit: number;
}

class UserService {
  private baseUrl = '/users';

  /**
   * 获取用户列表
   * @returns 返回用户数组和总数
   */
  async getUsers(params: GetUsersParams = {}): Promise<{ users: User[]; total: number }> {
    const response = await apiClient.get<UserListResponse>(`${this.baseUrl}`, { params });
    // 后端返回的是 UserListResponse 格式：{ users: User[], total: number, skip: number, limit: number }
    // apiClient 已经提取了 data 字段，所以 response.data 就是 UserListResponse
    return {
      users: response.data?.users || [],
      total: response.data?.total || 0
    };
  }

  /**
   * 获取用户详情
   */
  async getUser(userId: string): Promise<User> {
    const response = await apiClient.get<User>(`${this.baseUrl}/${userId}`);
    return response.data;
  }

  /**
   * 创建用户
   */
  async createUser(user: Partial<User>): Promise<User> {
    const response = await apiClient.post<User>(`${this.baseUrl}`, user);
    return response.data;
  }

  /**
   * 更新用户
   */
  async updateUser(userId: string, user: Partial<User>): Promise<User> {
    const response = await apiClient.put<User>(`${this.baseUrl}/${userId}`, user);
    return response.data;
  }

  /**
   * 获取当前用户
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>(`${this.baseUrl}/me`);
    return response.data;
  }

  /**
   * 更新当前用户
   */
  async updateCurrentUser(user: Partial<User>): Promise<User> {
    const response = await apiClient.put<User>(`${this.baseUrl}/me`, user);
    return response.data;
  }

  /**
   * 删除用户
   */
  async deleteUser(userId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${userId}`);
  }
}

export const userService = new UserService();

