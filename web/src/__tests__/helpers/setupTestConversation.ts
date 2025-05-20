/**
 * 聊天测试数据管理脚本
 * 提供创建和清理测试会话的功能
 */

import { apiClient } from '@/service/apiClient';

/**
 * 创建测试会话
 * @returns 新创建会话的ID
 */
export async function createTestSession(): Promise<string> {
  try {
    const response = await apiClient.post('conversations', {
      customer_email: 'customer1@example.com',
      title: `测试会话 ${new Date().toISOString()}`
    });
    
    if (!response.ok) {
      throw new Error(`创建会话失败: ${response.status}`);
    }
    
    return response.data.id;
  } catch (error) {
    console.error('创建测试会话失败:', error);
    throw error;
  }
}

/**
 * 清理测试会话
 * 注意：仅在测试环境使用，生产环境应不允许物理删除会话
 * @param conversationId 要清理的会话ID
 */
export async function cleanupTestSession(conversationId: string): Promise<void> {
  try {
    // 大多数情况下，我们不会真正删除会话，而是标记为已删除
    const response = await apiClient.delete(`conversations/${conversationId}`);
    
    if (!response.ok) {
      throw new Error(`清理会话失败: ${response.status}`);
    }
    
    console.log(`测试会话已清理: ${conversationId}`);
  } catch (error) {
    console.error(`清理测试会话失败 ${conversationId}:`, error);
    // 不抛出异常，以避免阻止测试清理过程
  }
}

/**
 * 清理所有测试会话
 * 谨慎使用，仅用于测试环境重置
 */
export async function cleanupAllTestSessions(): Promise<void> {
  try {
    // 获取所有测试会话
    const response = await apiClient.get('conversations');
    
    if (!response.ok) {
      throw new Error(`获取测试会话失败: ${response.status}`);
    }
    
    const testSessions = response.data.conversations.filter(
      (conv: any) => conv.title.startsWith('测试会话')
    );
    
    // 批量清理
    await Promise.all(
      testSessions.map((session: any) => cleanupTestSession(session.id))
    );
    
    console.log(`已清理 ${testSessions.length} 个测试会话`);
  } catch (error) {
    console.error('清理所有测试会话失败:', error);
  }
} 