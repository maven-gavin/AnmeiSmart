'use client';

import ChatLayout from '@/components/chat/ChatLayout'
import ChatWindow from '@/components/chat/ChatWindow'
import ConversationList from '@/components/chat/ConversationList'
import CustomerProfile from '@/components/chat/CustomerProfile'

export default function ChatPageClient() {
  return (
    <ChatLayout
      conversationList={<ConversationList />}
      chatWindow={<ChatWindow />}
      customerProfile={<CustomerProfile />}
    />
  )
} 