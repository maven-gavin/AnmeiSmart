/**
 * 前端文件服务
 * 处理文件上传、验证和管理
 */
import { apiClient } from './apiClient';
import { FileInfo } from '@/types/chat';
import { FILE_CONFIG } from '@/config';

export class FileService {
  /**
   * 验证文件
   */
  static validateFile(file: File): { valid: boolean; error?: string } {
    // 检查文件大小
    if (file.size > FILE_CONFIG.MAX_FILE_SIZE) {
      const sizeMB = Math.round(FILE_CONFIG.MAX_FILE_SIZE / (1024 * 1024));
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

    // 构建FormData
    const formData = new FormData();
    formData.append('file', file);
    formData.append('conversation_id', conversationId);

    // 使用统一的apiClient发送请求
    const response = await apiClient.upload<{ success: boolean; message: string; file_info: FileInfo }>(
      FILE_CONFIG.API_ENDPOINTS.upload, 
      formData
    );

    if (!response.data?.success) {
      throw new Error(response.data?.message || '上传失败');
    }

    return response.data.file_info;
  }

  /**
   * 获取文件信息
   */
  async getFileInfo(objectName: string): Promise<FileInfo | null> {
    try {
      const response = await apiClient.get<FileInfo>(
        `${FILE_CONFIG.API_ENDPOINTS.info}/${objectName}`
      );
      return response.data || null;
    } catch (error: unknown) {
      const status = (error as { status?: number }).status;
      if (status === 404) {
        return null;
      }
      console.error('获取文件信息失败:', error);
      return null;
    }
  }

  /**
   * 删除文件
   */
  async deleteFile(objectName: string): Promise<boolean> {
    try {
      const response = await apiClient.delete(
        `${FILE_CONFIG.API_ENDPOINTS.delete}/${objectName}`
      );
      return response.status >= 200 && response.status < 300;
    } catch (error) {
      console.error('删除文件失败:', error);
      return false;
    }
  }

  /**
   * 根据文件ID获取文件
   */
  async getFileById(fileId: string): Promise<Blob> {
    const response = await apiClient.get<Blob>(
      `/files/${fileId}/preview`,
      {
        headers: {
          'Accept': 'image/*,application/pdf,text/plain,audio/*,video/*'
        },
        skipContentType: true
      }
    );

    if (!response.data) {
      throw new Error('获取文件失败');
    }

    return response.data;
  }

  /**
   * 根据文件ID获取文件信息
   */
  async getFileInfoById(fileId: string): Promise<FileInfo | null> {
    try {
      const response = await apiClient.get<FileInfo>(
        `/files/${fileId}/info`
      );
      return response.data || null;
    } catch (error: unknown) {
      const status = (error as { status?: number }).status;
      if (status === 404) {
        return null;
      }
      console.error('获取文件信息失败:', error);
      return null;
    }
  }

  /**
   * 根据文件ID获取文件预览流（用于音频/视频等）
   */
  async getFilePreviewStreamById(fileId: string): Promise<Blob> {
    const response = await apiClient.get<Blob>(
      `/files/${fileId}/preview`,
      {
        headers: {
          'Accept': 'image/*,application/pdf,text/plain,audio/*,video/*'
        },
        skipContentType: true
      }
    );

    if (!response.data) {
      throw new Error('获取文件失败');
    }

    return response.data;
  }

  /**
   * 获取文件预览URL（通过文件ID）
   */
  static getPreviewUrlByFileId(fileId: string): string {
    return `/api/v1/files/${fileId}/preview`;
  }

  /**
   * 获取文件下载URL（通过文件ID）
   */
  static getDownloadUrlByFileId(fileId: string): string {
    return `/api/v1/files/${fileId}/download`;
  }

  /**
   * 获取文件预览URL（向后兼容，使用objectName）
   */
  static getPreviewUrl(objectName: string): string {
    return `${FILE_CONFIG.API_ENDPOINTS.preview}/${objectName}`;
  }

  /**
   * 获取文件下载URL（向后兼容，使用objectName）
   */
  static getDownloadUrl(objectName: string): string {
    return `${FILE_CONFIG.API_ENDPOINTS.download}/${objectName}`;
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

  /**
   * 根据文件ID获取文件预览流
   */
  async getFilePreviewStreamByFileId(fileId: string): Promise<Blob> {
    return this.getFileById(fileId);
  }

  /**
   * 获取认证的文件预览流（向后兼容，使用objectName）
   */
  async getFilePreviewStream(objectName: string): Promise<Blob> {
    const response = await apiClient.get<Blob>(
      `${FILE_CONFIG.API_ENDPOINTS.preview}/${objectName}`,
      {
        headers: {
          'Accept': 'image/*,application/pdf,text/plain,audio/*,video/*'
        },
        skipContentType: true
      }
    );

    if (!response.data) {
      throw new Error('获取文件流失败');
    }

    return response.data;
  }
} 