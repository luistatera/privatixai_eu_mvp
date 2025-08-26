export interface ChatAskResponse {
  content: string;
  citations: Array<{
    chunk_id: string;
    file_id: string;
    file_name: string;
    start: number | null;
    end: number | null;
    score: number | null;
    snippet?: string;
  }>;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, unknown>;
}

export interface ChatAskRequest {
  prompt: string;
  k?: number;
  max_tokens?: number;
  temperature?: number;
  conversation_id?: string;
  history?: ChatMessage[];
  anchor?: { file_ids?: string[]; chunk_ids?: string[] };
}

export async function askChat(req: ChatAskRequest): Promise<ChatAskResponse> {
  const res = await fetch(`${window.privatixEnv.backendUrl}/api/chat/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    try {
      const body = await res.json();
      if (res.status === 503 && body?.detail === 'Nothing was sent: secure transport unavailable') {
        throw new Error('Nothing was sent. Please check your secure connection and try again.');
      }
    } catch {}
    throw new Error(`Chat failed: ${res.status}`);
  }
  return res.json();
}


