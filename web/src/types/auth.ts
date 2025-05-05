export type UserRole = 'advisor' | 'doctor' | 'operator';

export interface AuthUser {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  avatar?: string;
  roles: UserRole[];
  currentRole?: UserRole;
}

export interface LoginCredentials {
  username: string; // 可以是邮箱或手机号
  password: string;
}

export interface LoginResponse {
  user: AuthUser;
  token: string;
}

export interface AuthState {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

export interface RoleOption {
  id: UserRole;
  name: string;
  path: string;
  icon?: string;
} 