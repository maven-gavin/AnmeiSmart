import { useState, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Plus, MessageSquare, Calendar, Edit2, Check, X, MoreVertical, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { renameAgentConversation } from '@/service/agentChatService';
import { toast } from 'react-hot-toast';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

export interface AgentConversation {
  id: string;
  title: string;
  agentId: string;
  lastMessageAt: Date;
  messageCount: number;
}

interface ConversationHistoryPanelProps {
  agentName: string;
  agentConfigId: string;  // 新增：Agent 配置ID
  conversations: AgentConversation[];
  selectedConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onCreateNewChat: () => void;
  onConversationUpdate?: (conversationId: string, title: string) => void;
  onDeleteConversation?: (conversationId: string) => void;
  isLoading?: boolean;
}

export function ConversationHistoryPanel({
  agentName,
  agentConfigId,
  conversations,
  selectedConversationId,
  onSelectConversation,
  onCreateNewChat,
  onConversationUpdate,
  onDeleteConversation,
  isLoading = false,
}: ConversationHistoryPanelProps) {
  // 标题编辑状态
  const [editingTitleId, setEditingTitleId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const editInputRef = useRef<HTMLInputElement>(null);
  
  // 删除确认对话框状态
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<string | null>(null);

  // 开始编辑标题
  const startEditTitle = (conversation: AgentConversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingTitleId(conversation.id);
    setEditingTitle(conversation.title || '');
    setTimeout(() => {
      editInputRef.current?.focus();
      editInputRef.current?.select();
    }, 0);
  };

  // 保存标题
  const saveTitle = async (conversationId: string) => {
    if (!editingTitle.trim()) {
      cancelEditTitle();
      return;
    }

    try {
      await renameAgentConversation(agentConfigId, conversationId, editingTitle.trim());
      onConversationUpdate?.(conversationId, editingTitle.trim());
      setEditingTitleId(null);
      setEditingTitle('');
      toast.success('标题更新成功');
    } catch (error) {
      console.error('更新会话标题失败:', error);
      toast.error('更新标题失败');
    }
  };

  // 取消编辑
  const cancelEditTitle = () => {
    setEditingTitleId(null);
    setEditingTitle('');
  };

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent, conversationId: string) => {
    if (e.key === 'Enter') {
      saveTitle(conversationId);
    } else if (e.key === 'Escape') {
      cancelEditTitle();
    }
  };

  // 打开删除确认对话框
  const handleDeleteClick = (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setConversationToDelete(conversationId);
    setDeleteDialogOpen(true);
  };

  // 确认删除
  const handleConfirmDelete = async () => {
    if (conversationToDelete && onDeleteConversation) {
      onDeleteConversation(conversationToDelete);
      setDeleteDialogOpen(false);
      setConversationToDelete(null);
    }
  };
  return (
    <div className="flex h-full w-80 flex-col border-r border-gray-200 bg-white">
      {/* Header with Agent Name */}
      <div className="border-b border-gray-200 p-4">
        <div className="mb-3 flex items-center space-x-2">
          <MessageSquare className="h-5 w-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">{agentName}</h2>
        </div>

        {/* Start New Chat Button */}
        <Button
          onClick={onCreateNewChat}
          className="w-full bg-orange-500 hover:bg-orange-600 text-white"
          size="sm"
        >
          <Plus className="mr-2 h-4 w-4" />
          Start New Chat
        </Button>
      </div>

      {/* Conversation List */}
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="flex items-center justify-center p-8">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
              <p className="mt-2 text-sm text-gray-500">加载中...</p>
            </div>
          </div>
        ) : conversations.length > 0 ? (
          <div className="space-y-1 p-2">
            {conversations.map((conversation) => {
              const isSelected = selectedConversationId === conversation.id;
              
              return (
                <div
                  key={conversation.id}
                  className={cn(
                    'w-full rounded-lg p-3 transition-colors group',
                    isSelected
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  )}
                >
                  {/* 标题区域 */}
                  <div className="mb-1 flex items-center justify-between">
                    {editingTitleId === conversation.id ? (
                      <div className="flex-1 flex items-center space-x-2">
                        <input
                          ref={editInputRef}
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onBlur={() => saveTitle(conversation.id)}
                          onKeyDown={(e) => handleKeyDown(e, conversation.id)}
                          className="flex-1 text-sm font-medium bg-white border border-orange-300 rounded px-2 py-1 focus:outline-none focus:border-orange-500"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            saveTitle(conversation.id);
                          }}
                          className="h-6 w-6 p-0 text-green-600 hover:text-green-700"
                        >
                          <Check className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            cancelEditTitle();
                          }}
                          className="h-6 w-6 p-0 text-red-600 hover:text-red-700"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ) : (
                      <>
                        <button
                          onClick={() => onSelectConversation(conversation.id)}
                          className="flex-1 text-left line-clamp-2 text-sm font-medium text-gray-900 hover:text-blue-600"
                        >
                          {conversation.title}
                        </button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0 text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreVertical className="h-3 w-3" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                startEditTitle(conversation, e);
                              }}
                            >
                              <Edit2 className="mr-2 h-4 w-4" />
                              编辑
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => handleDeleteClick(conversation.id, e)}
                              className="text-red-600 focus:text-red-600"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              删除
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </>
                    )}
                  </div>
                  
                  {/* 元信息区域 */}
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <Calendar className="h-3 w-3" />
                    <span>
                      {(() => {
                        try {
                          return formatDistanceToNow(conversation.lastMessageAt, {
                            addSuffix: true,
                            locale: zhCN,
                          });
                        } catch (error) {
                          console.warn('日期格式化失败:', conversation.lastMessageAt, error);
                          return '刚刚';
                        }
                      })()}
                    </span>
                    <span>·</span>
                    <span>{conversation.messageCount} 条消息</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <MessageSquare className="mb-3 h-12 w-12 text-gray-300" />
            <p className="mb-1 text-sm font-medium text-gray-900">
              暂无对话记录
            </p>
            <p className="text-xs text-gray-500">
              点击"Start New chat"开始新对话
            </p>
          </div>
        )}
      </ScrollArea>

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除这个对话吗？此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

