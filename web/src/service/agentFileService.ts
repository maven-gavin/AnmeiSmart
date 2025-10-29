/**
 * Agent 文件上传服务
 * 处理文件上传到 Dify 服务器
 */

import { apiClient } from './apiClient';
import type { FileUploadResult } from '@/types/agent-chat';

/**
 * 上传单个文件到Dify
 * @param agentConfigId Agent配置ID
 * @param file 要上传的文件
 * @returns 包含Dify文件ID的响应
 */
export const uploadAgentFile = async (
  agentConfigId: string,
  file: File
): Promise<FileUploadResult> => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.upload<FileUploadResult>(
      `/agent/${agentConfigId}/upload`,
      formData
    );
    
    // 验证响应格式
    if (!response || !response.data) {
      throw new Error('上传响应格式错误');
    }
    
    const result = response.data;
    
    // 验证必需字段
    if (!result.id) {
      throw new Error('上传响应缺少文件ID');
    }
    
    return result;
  } catch (error: any) {
    console.error('文件上传详细错误:', {
      message: error?.message,
      status: error?.status,
      statusText: error?.statusText,
      response: error?.response,
      error
    });
    
    // 抛出更有意义的错误
    if (error?.status) {
      throw new Error(`上传失败 (${error.status}): ${error.statusText || '未知错误'}`);
    }
    throw new Error(error?.message || '文件上传失败');
  }
};

/**
 * 批量上传多个文件到Dify
 * @param agentConfigId Agent配置ID
 * @param files 要上传的文件数组
 * @returns 包含所有文件Dify ID的数组
 */
export const uploadAgentFiles = async (
  agentConfigId: string,
  files: File[]
): Promise<FileUploadResult[]> => {
  // 并行上传所有文件
  const uploadPromises = files.map(file => uploadAgentFile(agentConfigId, file));
  return Promise.all(uploadPromises);
};

// 导出服务对象
const agentFileService = {
  uploadAgentFile,
  uploadAgentFiles,
};

export default agentFileService;

