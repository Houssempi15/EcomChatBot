'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { message, Spin } from 'antd';
import {
  ConversationList,
  ChatWindow,
  RightPanel,
} from '@/components/chat';
import { conversationApi } from '@/lib/api';
import { useConversationStore } from '@/store/conversationStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Message } from '@/types';

export default function ChatPage() {
  const searchParams = useSearchParams();
  const initialId = searchParams.get('id');

  const [selectedId, setSelectedId] = useState<string | null>(initialId);
  const [inputValue, setInputValue] = useState('');
  const [searchValue, setSearchValue] = useState('');
  const [sending, setSending] = useState(false);

  const {
    conversations,
    currentConversation,
    messages,
    isLoading,
    pagination,
    statusFilter,
    ragSources,
    fetchConversations,
    selectConversation,
    addMessage,
    closeConversation,
    setStatusFilter,
    setWsStatus,
    startStreamingMessage,
    appendStreamChunk,
    finalizeStreamingMessage,
    setRagSources,
    takeoverConversation,
  } = useConversationStore();

  const streamingIdRef = useRef<string | null>(null);

  // Initial load + 30s polling
  useEffect(() => {
    fetchConversations();
    const timer = setInterval(() => fetchConversations(), 30000);
    return () => clearInterval(timer);
  }, [fetchConversations]);

  // Re-fetch when filter changes
  useEffect(() => {
    fetchConversations({ page: 1 });
  }, [statusFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load conversation detail when selected
  useEffect(() => {
    if (selectedId) {
      selectConversation(selectedId);
      setRagSources([]);
    }
  }, [selectedId]); // eslint-disable-line react-hooks/exhaustive-deps

  // WebSocket
  const { isConnected, sendMessage: wsSend } = useWebSocket({
    conversationId: selectedId || '',
    stream: true,
    autoConnect: !!selectedId,
    onConnect: () => setWsStatus('connected'),
    onDisconnect: () => setWsStatus('disconnected'),
    onMessage: (msg) => {
      if (msg.type === 'stream') {
        const chunk = msg.chunk ?? msg.content ?? '';
        if (!streamingIdRef.current) {
          streamingIdRef.current = startStreamingMessage(selectedId!);
        }
        appendStreamChunk(streamingIdRef.current, chunk);
        if (msg.is_final) {
          finalizeStreamingMessage(streamingIdRef.current);
          streamingIdRef.current = null;
        }
      } else if (msg.type === 'message') {
        if (streamingIdRef.current) {
          finalizeStreamingMessage(streamingIdRef.current);
          streamingIdRef.current = null;
        }
        if (msg.role === 'assistant' && msg.content) {
          const newMsg: Message = {
            id: Date.now(),
            message_id: `ws-${Date.now()}`,
            conversation_id: selectedId!,
            role: 'assistant',
            content: msg.content,
            created_at: msg.timestamp || new Date().toISOString(),
            input_tokens: msg.tokens?.input || 0,
            output_tokens: msg.tokens?.output || 0,
          };
          addMessage(newMsg);
        }
      } else if (msg.type === 'metadata' && msg.sources) {
        setRagSources(
          msg.sources.map((s) => ({
            knowledge_id: s.knowledge_id,
            title: s.title,
            content: '',
            score: s.score,
            source: s.title,
          }))
        );
      } else if (msg.type === 'error') {
        message.error(msg.content || '消息处理出错');
      }
    },
  });

  const handleSelectConversation = (id: string) => {
    setSelectedId(id);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !selectedId) return;

    const userMsg: Message = {
      id: Date.now(),
      message_id: `msg-${Date.now()}`,
      conversation_id: selectedId,
      role: 'user',
      content: inputValue,
      created_at: new Date().toISOString(),
      input_tokens: 0,
      output_tokens: 0,
    };
    addMessage(userMsg);
    const content = inputValue;
    setInputValue('');

    if (currentConversation?.status === 'waiting') {
      // Human takeover mode: use REST
      setSending(true);
      try {
        const response = await conversationApi.sendMessage(selectedId, { content });
        if (!response.success) {
          message.error(response.error?.message || '发送失败');
        }
      } catch {
        message.error('发送消息失败');
      } finally {
        setSending(false);
      }
    } else {
      // AI mode: use WebSocket
      wsSend(content);
    }
  };

  const handleCloseConversation = async () => {
    if (!selectedId) return;
    await closeConversation(selectedId);
    message.success('会话已结束');
  };

  const handleTakeover = async () => {
    if (!selectedId) return;
    await takeoverConversation(selectedId);
    message.success('已接管会话，切换至人工模式');
  };

  const handleStatusFilterChange = (status: 'all' | 'active' | 'waiting' | 'closed') => {
    setStatusFilter(status);
  };

  const handlePageChange = (page: number) => {
    fetchConversations({ page });
  };

  // Filter by search locally
  const filteredConversations = conversations.filter((c) => {
    if (!searchValue) return true;
    const s = searchValue.toLowerCase();
    return (
      c.conversation_id.toLowerCase().includes(s) ||
      c.user_external_id.toLowerCase().includes(s) ||
      c.last_message_preview?.toLowerCase().includes(s)
    );
  });

  if (isLoading && conversations.length === 0) {
    return (
      <div className="h-[calc(100vh-64px-48px)] flex items-center justify-center">
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-64px-48px)] flex bg-white rounded-lg overflow-hidden shadow">
      {/* Conversation List */}
      <div className="w-80 flex-shrink-0">
        <ConversationList
          conversations={filteredConversations}
          selectedId={selectedId}
          onSelect={handleSelectConversation}
          searchValue={searchValue}
          onSearchChange={setSearchValue}
          statusFilter={statusFilter}
          onStatusFilterChange={handleStatusFilterChange}
          pagination={pagination}
          onPageChange={handlePageChange}
          loading={isLoading}
        />
      </div>

      {/* Chat Window */}
      <ChatWindow
        conversation={currentConversation}
        messages={messages}
        inputValue={inputValue}
        onInputChange={setInputValue}
        onSend={handleSendMessage}
        onClose={handleCloseConversation}
        onTakeover={handleTakeover}
        sending={sending}
        loading={isLoading && !!selectedId && !currentConversation}
        wsConnected={isConnected}
      />

      {/* Right Panel */}
      <RightPanel user={currentConversation?.user || null} ragSources={ragSources} />
    </div>
  );
}
