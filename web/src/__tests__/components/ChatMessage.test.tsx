import { render, screen, fireEvent } from '@testing-library/react';
import ChatMessage from '@/components/chat/ChatMessage';
import { type Message } from '@/types/chat';

// Mock message data
const createMockMessage = (overrides: Partial<Message> = {}): Message => ({
  id: 'test-message-1',
  conversationId: 'conv-1',
  localId: 'local-test-1',
  content: 'Test message content',
  type: 'text',
  sender: {
    id: 'user-1',
    type: 'user',
    name: 'Test User',
    avatar: '/avatars/test.png'
  },
  timestamp: new Date().toISOString(),
  createdAt: new Date().toISOString(),
  status: 'sent',
  ...overrides
});

describe('ChatMessage', () => {
  it('renders message content correctly', () => {
    const message = createMockMessage();
    render(<ChatMessage message={message} />);
    
    expect(screen.getByText('Test message content')).toBeInTheDocument();
    expect(screen.getByText('Test User')).toBeInTheDocument();
  });

  it('shows pending status indicator', () => {
    const message = createMockMessage({ status: 'pending' });
    render(<ChatMessage message={message} />);
    
    expect(screen.getByText('发送中...')).toBeInTheDocument();
  });

  it('shows failed status indicator with error message', () => {
    const message = createMockMessage({ 
      status: 'failed', 
      error: 'Network error',
      canRetry: true,
      canDelete: true
    });
    
    render(<ChatMessage message={message} />);
    
    expect(screen.getByText('发送失败')).toBeInTheDocument();
    expect(screen.getByText('(Network error)')).toBeInTheDocument();
  });

  it('shows action buttons on hover for failed messages', () => {
    const message = createMockMessage({ 
      status: 'failed',
      canRetry: true,
      canDelete: true
    });
    
    render(<ChatMessage message={message} />);
    
    const messageContainer = screen.getByTestId('message-test-message-1');
    fireEvent.mouseEnter(messageContainer);
    
    expect(screen.getByText('重试')).toBeInTheDocument();
    expect(screen.getByText('删除')).toBeInTheDocument();
  });



  it('highlights search terms correctly', () => {
    const message = createMockMessage({ content: 'This is a test message' });
    render(<ChatMessage message={message} searchTerm="test" />);
    
    const highlightedText = screen.getByText('test');
    expect(highlightedText).toHaveClass('bg-yellow-200');
  });

  it('does not show status indicator for sent messages without errors', () => {
    const message = createMockMessage({ status: 'sent' });
    render(<ChatMessage message={message} />);
    
    expect(screen.queryByText('发送中...')).not.toBeInTheDocument();
    expect(screen.queryByText('发送失败')).not.toBeInTheDocument();
  });
}); 