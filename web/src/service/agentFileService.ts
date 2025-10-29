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
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.upload<FileUploadResult>(
    `/agent/${agentConfigId}/upload`,
    formData
  );
  
  return response.data;
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

