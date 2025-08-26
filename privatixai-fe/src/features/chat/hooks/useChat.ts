import { useCallback, useRef, useState } from 'react';
import { askChat, ChatAskRequest } from '@/features/chat/api';

export interface ChatMessageVM {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  sources?: Array<{ name: string; snippet: string }>; 
  timestamp: Date;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessageVM[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const conversationIdRef = useRef<string>(Math.random().toString(36).slice(2));

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const userMessage: ChatMessageVM = {
      id: Date.now().toString(),
      type: 'user',
      content: trimmed,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    setErrorText(null);
    try {
      // Get current history before adding user message
      const currentHistory = messages.map(m => ({
        role: m.type === 'user' ? 'user' : 'assistant',
        content: m.content,
      }));
      
      const req: ChatAskRequest = {
        prompt: trimmed,
        k: 8,
        conversation_id: conversationIdRef.current,
        history: currentHistory,
      };

      const resp = await askChat(req);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: resp.content,
        sources: resp.citations.map(c => ({ name: c.file_name, snippet: c.snippet ?? '' })),
        timestamp: new Date(),
      }]);
    } catch (e) {
      setErrorText('We could not process your request. Please try again.');
    } finally {
      setIsTyping(false);
    }
  }, [messages]);

  const reset = useCallback(() => {
    setMessages([]);
    setErrorText(null);
    conversationIdRef.current = Math.random().toString(36).slice(2);
  }, []);

  return { messages, isTyping, errorText, send, reset };
}




