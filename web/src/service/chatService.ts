import { Message, Conversation, CustomerProfile } from "@/types/chat";
import { mockMessages, mockConversations, mockCustomerProfiles } from "./mockData";
import { v4 as uuidv4 } from 'uuid';

// 保存运行时的消息数据（会话ID -> 消息数组）
let chatMessages: Record<string, Message[]> = { ...mockMessages };

// 保存运行时的会话数据
let conversations: Conversation[] = [...mockConversations];

// 当前顾问信息（模拟从登录状态获取）
const consultantInfo = {
  id: '2',
  name: '李顾问',
  avatar: '/avatars/consultant1.png',
  type: 'consultant' as const,
};

// AI信息
const aiInfo = {
  id: 'ai1',
  name: 'AI助手',
  avatar: '/avatars/ai.png',
  type: 'ai' as const,
};

// 保存AI状态（会话ID -> 是否由顾问接管）
let consultantTakeover: Record<string, boolean> = {};

// 生成模拟AI回复
const generateAIResponse = (content: string): string => {
  // 简单的模拟AI回复
  if (content.includes('恢复') || content.includes('术后')) {
    return '术后恢复时间因人而异，一般需要1-2周的恢复期。建议术后遵循医生的指导，保持伤口清洁，避免剧烈运动，按时服用药物。';
  } else if (content.includes('价格') || content.includes('费用')) {
    return '我们的医美项目价格根据具体操作和材料有所不同。基础项目从数千元起，精细项目可能达到数万元。我们提供免费咨询和评估服务，可以根据您的需求提供详细报价。';
  } else if (content.includes('风险') || content.includes('副作用')) {
    return '任何医疗美容项目都存在一定风险。常见的副作用包括暂时性红肿、瘀斑等。严重但罕见的风险包括感染、过敏反应等。我们的专业医生会在术前详细告知您相关风险并制定个性化方案降低风险。';
  } else if (content.includes('玻尿酸') || content.includes('填充')) {
    return '玻尿酸是一种常见的注射填充剂，可用于面部轮廓塑造、唇部丰满等。效果通常可维持6-18个月，是一种临时性填充方案。注射过程快速，恢复期短，是许多客户的首选。';
  } else {
    return '感谢您的咨询。我们的专业医疗团队将为您提供个性化的方案和详细解答。您还有其他问题吗？';
  }
};

// 发送文字消息
export const sendTextMessage = async (conversationId: string, content: string): Promise<Message> => {
  // 创建用户消息
  const userMessage: Message = {
    id: `m_${uuidv4()}`,
    content,
    type: 'text',
    sender: {
      id: consultantInfo.id,
      type: consultantInfo.type,
      name: consultantInfo.name,
      avatar: consultantInfo.avatar,
    },
    timestamp: new Date().toISOString(),
  };
  
  // 添加到消息列表
  if (!chatMessages[conversationId]) {
    chatMessages[conversationId] = [];
  }
  chatMessages[conversationId].push(userMessage);
  
  // 更新会话最后一条消息
  const conversationIndex = conversations.findIndex(conv => conv.id === conversationId);
  if (conversationIndex >= 0) {
    conversations[conversationIndex] = {
      ...conversations[conversationIndex],
      lastMessage: userMessage,
      updatedAt: userMessage.timestamp,
    };
  }
  
  // 模拟异步API调用
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(userMessage);
    }, 300);
  });
};

// 发送图片消息
export const sendImageMessage = async (conversationId: string, imageUrl: string): Promise<Message> => {
  // 创建图片消息
  const imageMessage: Message = {
    id: `m_${uuidv4()}`,
    content: imageUrl,
    type: 'image',
    sender: {
      id: consultantInfo.id,
      type: consultantInfo.type,
      name: consultantInfo.name,
      avatar: consultantInfo.avatar,
    },
    timestamp: new Date().toISOString(),
  };
  
  // 添加到消息列表
  if (!chatMessages[conversationId]) {
    chatMessages[conversationId] = [];
  }
  chatMessages[conversationId].push(imageMessage);
  
  // 更新会话最后一条消息
  const conversationIndex = conversations.findIndex(conv => conv.id === conversationId);
  if (conversationIndex >= 0) {
    conversations[conversationIndex] = {
      ...conversations[conversationIndex],
      lastMessage: imageMessage,
      updatedAt: imageMessage.timestamp,
    };
  }
  
  // 模拟异步API调用
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(imageMessage);
    }, 500); // 图片上传通常需要更长时间
  });
};

// 发送语音消息
export const sendVoiceMessage = async (conversationId: string, audioUrl: string): Promise<Message> => {
  // 创建语音消息
  const voiceMessage: Message = {
    id: `m_${uuidv4()}`,
    content: audioUrl,
    type: 'voice',
    sender: {
      id: consultantInfo.id,
      type: consultantInfo.type,
      name: consultantInfo.name,
      avatar: consultantInfo.avatar,
    },
    timestamp: new Date().toISOString(),
  };
  
  // 添加到消息列表
  if (!chatMessages[conversationId]) {
    chatMessages[conversationId] = [];
  }
  chatMessages[conversationId].push(voiceMessage);
  
  // 更新会话最后一条消息
  const conversationIndex = conversations.findIndex(conv => conv.id === conversationId);
  if (conversationIndex >= 0) {
    conversations[conversationIndex] = {
      ...conversations[conversationIndex],
      lastMessage: voiceMessage,
      updatedAt: voiceMessage.timestamp,
    };
  }
  
  // 模拟异步API调用
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(voiceMessage);
    }, 500);
  });
};

// 获取AI回复
export const getAIResponse = async (conversationId: string, userMessage: Message): Promise<Message | null> => {
  // 如果顾问已接管，不再生成AI回复
  if (consultantTakeover[conversationId]) {
    return null;
  }
  
  // 根据用户消息内容生成AI回复
  const responseContent = generateAIResponse(userMessage.content);
  
  // 创建AI回复消息
  const aiMessage: Message = {
    id: `m_${uuidv4()}`,
    content: responseContent,
    type: 'text',
    sender: {
      id: aiInfo.id,
      type: aiInfo.type,
      name: aiInfo.name,
      avatar: aiInfo.avatar,
    },
    timestamp: new Date().toISOString(),
  };
  
  // 添加到消息列表
  chatMessages[conversationId].push(aiMessage);
  
  // 模拟异步AI处理时间
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(aiMessage);
    }, 1000); // AI回复需要一定时间
  });
};

// 获取会话消息
export const getConversationMessages = (conversationId: string): Message[] => {
  return chatMessages[conversationId] || [];
};

// 获取所有会话
export const getConversations = (): Conversation[] => {
  return conversations;
};

// 标记消息为重点
export const markMessageAsImportant = (conversationId: string, messageId: string, isImportant: boolean): Message | null => {
  const messages = chatMessages[conversationId];
  if (!messages) return null;
  
  const messageIndex = messages.findIndex(msg => msg.id === messageId);
  if (messageIndex >= 0) {
    const updatedMessage = {
      ...messages[messageIndex],
      isImportant,
    };
    
    // 更新消息
    messages[messageIndex] = updatedMessage;
    return updatedMessage;
  }
  
  return null;
};

// 获取重点消息
export const getImportantMessages = (conversationId: string): Message[] => {
  const messages = chatMessages[conversationId];
  if (!messages) return [];
  
  return messages.filter(msg => msg.isImportant);
};

// 获取客户档案
export const getCustomerProfile = (customerId: string): CustomerProfile | null => {
  return mockCustomerProfiles[customerId] || null;
};

// 获取客户历史咨询记录
export const getCustomerConsultationHistory = (customerId: string): CustomerProfile['consultationHistory'] => {
  const profile = mockCustomerProfiles[customerId];
  if (!profile) return [];
  
  return profile.consultationHistory;
};

// 顾问接管会话
export const takeoverConversation = (conversationId: string): boolean => {
  consultantTakeover[conversationId] = true;
  
  // 发送系统消息通知顾问接管
  const systemMessage: Message = {
    id: `m_${uuidv4()}`,
    content: '顾问已接管会话',
    type: 'text',
    sender: {
      id: 'system',
      type: 'system',
      name: '系统',
      avatar: '',
    },
    timestamp: new Date().toISOString(),
    isSystemMessage: true,
  };
  
  // 添加到消息列表
  if (!chatMessages[conversationId]) {
    chatMessages[conversationId] = [];
  }
  chatMessages[conversationId].push(systemMessage);
  
  return true;
};

// 切回AI模式
export const switchBackToAI = (conversationId: string): boolean => {
  consultantTakeover[conversationId] = false;
  
  // 发送系统消息通知切回AI模式
  const systemMessage: Message = {
    id: `m_${uuidv4()}`,
    content: 'AI助手已接管会话',
    type: 'text',
    sender: {
      id: 'system',
      type: 'system',
      name: '系统',
      avatar: '',
    },
    timestamp: new Date().toISOString(),
    isSystemMessage: true,
  };
  
  // 添加到消息列表
  if (!chatMessages[conversationId]) {
    chatMessages[conversationId] = [];
  }
  chatMessages[conversationId].push(systemMessage);
  
  return true;
};

// 是否处于顾问模式
export const isConsultantMode = (conversationId: string): boolean => {
  return !!consultantTakeover[conversationId];
}; 