import { Suspense } from 'react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ChatPageClient from '@/app/consultant/chat/ChatPageClient'

export const metadata = {
  title: '智能客服 - 安美智享',
  description: '医美顾问智能客服系统',
}

export default function ChatPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <ChatPageClient />
    </Suspense>
  )
} 