/**
 * 前端文件服务
 * 处理文件上传、验证和管理
 */
import { tokenManager } from '@/service/tokenManager';
import { FileInfo } from '@/types/chat';

export class FileService {
  private static readonly MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
  private static readonly API_BASE = '/api/v1/files';

  /**
   * 验证文件
   */
  static validateFile(file: File): { valid: boolean; error?: string } {
    // 检查文件大小
    if (file.size > this.MAX_FILE_SIZE) {
      const sizeMB = Math.round(this.MAX_FILE_SIZE / (1024 * 1024));
      return {
        valid: false,
        error: `文件大小超出限制，最大允许 ${sizeMB}MB`
      };
    }

    // 检查文件名
    if (!file.name || file.name.trim() === '') {
      return {
        valid: false,
        error: '文件名不能为空'
      };
    }

    return { valid: true };
  }

  /**
   * 上传文件
   */
  async uploadFile(file: File, conversationId: string): Promise<FileInfo> {
    // 验证文件
    const validation = FileService.validateFile(file);
    if (!validation.valid) {
      throw new Error(validation.error);
    }

    // 获取认证token
    const token = await tokenManager.getValidToken();
    if (!token) {
      throw new Error('用户未登录');
    }

    // 构建FormData
    const formData = new FormData();
    formData.append('file', file);
    formData.append('conversation_id', conversationId);

    // 发送请求
    const response = await fetch(`${FileService.API_BASE}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `上传失败: ${response.status}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || '上传失败');
    }

    return result.file_info;
  }

  /**
   * 获取文件信息
   */
  async getFileInfo(objectName: string): Promise<FileInfo | null> {
    try {
      const token = await tokenManager.getValidToken();
      if (!token) {
        throw new Error('用户未登录');
      }

      const response = await fetch(`${FileService.API_BASE}/info/${encodeURIComponent(objectName)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 404) {
        return null;
      }

      if (!response.ok) {
        throw new Error(`获取文件信息失败: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('获取文件信息失败:', error);
      return null;
    }
  }

  /**
   * 删除文件
   */
  async deleteFile(objectName: string): Promise<boolean> {
    try {
      const token = await tokenManager.getValidToken();
      if (!token) {
        throw new Error('用户未登录');
      }

      const response = await fetch(`${FileService.API_BASE}/delete/${encodeURIComponent(objectName)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      return response.ok;
    } catch (error) {
      console.error('删除文件失败:', error);
      return false;
    }
  }

  /**
   * 获取文件预览URL
   */
  static getPreviewUrl(objectName: string): string {
    return `${FileService.API_BASE}/preview/${encodeURIComponent(objectName)}`;
  }

  /**
   * 获取文件下载URL
   */
  static getDownloadUrl(objectName: string): string {
    return `${FileService.API_BASE}/download/${encodeURIComponent(objectName)}`;
  }

  /**
   * 格式化文件大小
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 获取文件类型图标
   */
  static getFileIcon(fileType: string, mimeType: string): string {
    if (fileType === 'image') {
      return '🖼️';
    }
    if (fileType === 'audio') {
      return '🎵';
    }
    if (fileType === 'video') {
      return '🎬';
    }
    if (fileType === 'document') {
      if (mimeType.includes('pdf')) {
        return '📄';
      }
      if (mimeType.includes('word')) {
        return '📝';
      }
      if (mimeType.includes('excel') || mimeType.includes('sheet')) {
        return '📊';
      }
      if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) {
        return '📽️';
      }
      return '📄';
    }
    if (fileType === 'archive') {
      return '📦';
    }
    return '📎';
  }
} 