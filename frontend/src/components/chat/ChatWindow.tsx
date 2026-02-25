'use client';

import { useRef, useEffect } from 'react';
import { Button, Input, Tag, Typography, Spin, Empty, Badge } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import MessageBubble from './MessageBubble';
import { Message, ConversationDetail } from '@/types';

const { Text } = Typography;
const { TextArea } = Input;

interface ChatWindowProps {
  conversation: ConversationDetail | null;
  messages: Message[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onClose: () => void;
  onTakeover: () => void;
  sending?: boolean;
  loading?: boolean;
  wsConnected?: boolean;
}

export default function ChatWindow({
  conversation,
  messages,
  inputValue,
  onInputChange,
  onSend,
  onClose,
  onTakeover,
  sending = false,
  loading = false,
  wsConnected = false,
}: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const formatUserId = (id: string) => {
    if (id.startsWith('VIP')) return id;
    return `访客 #${id.slice(-4)}`;
  };

  if (!conversation) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <Empty description="选择一个会话开始" />
      </div>
    );
  }

  const isClosed = conversation.status === 'closed';
  const isWaiting = conversation.status === 'waiting';
  const inputDisabled = isClosed;

  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      {/* Header */}
      <div className="h-16 px-5 flex items-center justify-between bg-white border-b border-gray-200">
        <div className="flex items-center gap-3">
          <Text strong>{formatUserId(conversation.user_external_id)}</Text>
          {isWaiting ? (
            <Tag color="orange">人工接管中</Tag>
          ) : (
            <Tag color={conversation.status === 'active' ? 'green' : 'default'}>
              {conversation.status === 'active' ? '在线' : '离线'}
            </Tag>
          )}
          <Badge
            status={wsConnected ? 'success' : 'default'}
            text={<Text type="secondary" className="text-xs">{wsConnected ? 'WS已连接' : 'WS未连接'}</Text>}
          />
        </div>
        <div className="flex gap-2">
          <Button danger onClick={onClose} disabled={isClosed}>
            结束会话
          </Button>
          <Button type="primary" onClick={onTakeover} disabled={isWaiting || isClosed}>
            人工接管
          </Button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Spin tip="加载消息中..." />
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <MessageBubble key={message.message_id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-5 bg-white border-t border-gray-200">
        <TextArea
          value={inputValue}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={isClosed ? '会话已结束' : '输入回复内容...'}
          autoSize={{ minRows: 3, maxRows: 6 }}
          className="mb-3"
          disabled={inputDisabled}
        />
        <div className="flex items-center justify-between">
          <Text type="secondary" className="text-sm">
            快捷键: <Tag>Shift+Enter</Tag> 换行
          </Text>
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={onSend}
            loading={sending}
            disabled={!inputValue.trim() || inputDisabled}
          >
            发送
          </Button>
        </div>
      </div>
    </div>
  );
}
