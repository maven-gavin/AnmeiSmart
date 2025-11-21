import { apiClient } from './apiClient';
import { User, UserRole } from '@/types/auth';

export interface GetUsersParams {
  skip?: number;
  limit?: number;
  search?: string;
}

export interface UserListResponse {
  data: User[];
  total: number;
}

class UserService {
  private baseUrl = '/users';

  /**
   * 获取用户列表
   */
  async getUsers(params: GetUsersParams = {}): Promise<User[]> {
    const response = await apiClient.get<User[]>(`${this.baseUrl}`, { params });
    return response.data;
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
}

export const userService = new UserService();

