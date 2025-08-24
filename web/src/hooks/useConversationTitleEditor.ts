import { useState, useRef } from 'react';
import { Conversation } from '@/types/chat';
import { updateConversationTitle } from '@/service/chatService';

export const useConversationTitleEditor = () => {
  const [editingTitleId, setEditingTitleId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const editInputRef = useRef<HTMLInputElement>(null);

  // 标题编辑相关函数
  const startEditTitle = (conversation: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingTitleId(conversation.id);
    setEditingTitle(conversation.title || '');
    setTimeout(() => {
      editInputRef.current?.focus();
      editInputRef.current?.select();
    }, 0);
  };

  const saveTitle = async (conversationId: string) => {
    if (!editingTitle.trim()) {
      cancelEditTitle();
      return;
    }

    try {
      await updateConversationTitle(conversationId, editingTitle.trim());
      setEditingTitleId(null);
      setEditingTitle('');
    } catch (error) {
      console.error('更新会话标题失败:', error);
    }
  };

  const cancelEditTitle = () => {
    setEditingTitleId(null);
    setEditingTitle('');
  };

  const handleKeyDown = (e: React.KeyboardEvent, conversationId: string) => {
    if (e.key === 'Enter') {
      saveTitle(conversationId);
    } else if (e.key === 'Escape') {
      cancelEditTitle();
    }
  };

  return {
    editingTitleId,
    editingTitle,
    editInputRef,
    setEditingTitle,
    startEditTitle,
    saveTitle,
    cancelEditTitle,
    handleKeyDown,
  };
};