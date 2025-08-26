import React, { useState } from 'react';
import { useChat } from '@/features/chat/hooks/useChat';

export function ChatView(): React.ReactElement {
  const { messages, isTyping, errorText, send, reset } = useChat();
  const [inputValue, setInputValue] = useState('');
  const [showSources, setShowSources] = useState(true);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = inputValue;
    setInputValue('');
    await send(text);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-heading font-semibold text-navy-900 dark:text-cyan-400">Chat with your Private Vault</h2>
            <p className="text-gray-600 dark:text-gray-300 text-sm mt-1">Ask me anything from your locally stored knowledge</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => setShowSources(!showSources)} className={`text-sm px-3 py-1.5 rounded-lg border transition-colors ${showSources ? 'bg-navy-50 dark:bg-cyan-900/20 border-navy-200 dark:border-cyan-700 text-navy-700 dark:text-cyan-300' : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'}`}>{showSources ? 'Hide' : 'Show'} Sources</button>
            <button onClick={reset} className="text-sm px-3 py-1.5 rounded-lg border text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">New chat</button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full max-w-2xl mx-auto text-center">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-navy-100 to-navy-200 dark:from-navy-900/30 dark:to-navy-800/30 mb-6">
              <svg className="w-12 h-12 text-navy-600 dark:text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
            </div>
            <h3 className="text-2xl font-heading font-semibold text-gray-900 dark:text-gray-100 mb-3">Ready to explore your private vault</h3>
            <p className="text-gray-600 dark:text-gray-300 mb-8 max-w-md">Start a conversation by asking about your files, or try one of these suggestions:</p>
            {errorText && (<div className="text-sm text-coral-600 dark:text-coral-400 mb-4">{errorText}</div>)}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
              {["Summarize my meeting notes from this week","What are the key points from my research on AI?","Find mentions of 'productivity' in my documents","What did I learn about design principles?"].map((q, i) => (
                <button key={i} onClick={() => setInputValue(q)} className="p-4 text-left rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-navy-300 dark:hover:border-cyan-500 hover:bg-navy-50 dark:hover:bg-navy-900/20 transition-all duration-200">
                  <span className="text-sm text-gray-700 dark:text-gray-300">"{q}"</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((m) => (
              <div key={m.id} className={`flex gap-4 ${m.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.type === 'assistant' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-navy-600 to-navy-800 dark:from-cyan-400 dark:to-cyan-600 flex items-center justify-center">
                    <div className="w-4 h-4 bg-white dark:bg-gray-900 rounded-sm flex items-center justify-center"><div className="w-1.5 h-1.5 bg-navy-600 dark:bg-cyan-400 rounded-full"></div></div>
                  </div>
                )}
                <div className={`max-w-3xl ${m.type === 'user' ? 'order-first' : ''}`}>
                  <div className={`rounded-2xl px-6 py-4 ${m.type === 'user' ? 'bg-navy-600 dark:bg-cyan-500 text-white dark:text-gray-900' : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'}`}>
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      {m.content.split('\n').map((line, i) => (
                        <p key={i} className={`${i === 0 ? '' : 'mt-2'} ${m.type === 'user' ? 'text-white dark:text-gray-900' : 'text-gray-900 dark:text-gray-100'}`}>{line}</p>
                      ))}
                    </div>
                  </div>
                  {m.sources && showSources && (
                    <div className="mt-3 space-y-2">
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Sources</p>
                      {m.sources.map((s, i) => (
                        <div key={i} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 border-l-4 border-navy-200 dark:border-cyan-400">
                          <span className="text-xs font-medium text-navy-700 dark:text-cyan-300">{s.name}</span>
                          <p className="text-xs text-gray-600 dark:text-gray-300 italic">"{s.snippet}"</p>
                        </div>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">{m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-navy-600 to-navy-800 dark:from-cyan-400 dark:to-cyan-600 flex items-center justify-center"><div className="w-4 h-4 bg-white dark:bg-gray-900 rounded-sm flex items-center justify-center"><div className="w-1.5 h-1.5 bg-navy-600 dark:bg-cyan-400 rounded-full animate-pulse"></div></div></div>
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl px-6 py-4">
                  <div className="flex items-center gap-1"><div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div><div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div><div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div></div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-6">
        <form onSubmit={handleSend} className="max-w-4xl mx-auto">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} placeholder="Ask me anything from your private vault..." className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:border-navy-500 dark:focus:border-cyan-500 focus:ring-2 focus:ring-navy-500/20 dark:focus:ring-cyan-500/20 transition-all duration-200 pr-12" disabled={isTyping} />
            </div>
            <button type="submit" disabled={!inputValue.trim() || isTyping} className="inline-flex items-center justify-center px-6 py-3 rounded-xl font-medium text-white bg-navy-900 hover:bg-navy-800 focus:ring-2 focus:ring-navy-500 focus:ring-offset-2 transition-all duration-200 dark:bg-cyan-500 dark:text-gray-900 dark:hover:bg-cyan-400 px-8 disabled:opacity-50 disabled:cursor-not-allowed group">
              {isTyping ? (
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              ) : (
                <svg className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


