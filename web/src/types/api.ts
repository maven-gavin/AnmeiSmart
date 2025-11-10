export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
  timestamp: string;
}

export const isApiSuccess = <T>(response: ApiResponse<T>): boolean => response.code === 0;

