'use client';

import { useState, useRef, useEffect, FormEvent } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  imageUrl?: string | null;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: newMessages.map(({ imageUrl, ...rest }) => rest),
        }), // imageUrlを除外
      });

      if (!response.ok) {
        throw new Error('API request failed');
      }

      const data = await response.json();
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.content,
        imageUrl: data.imageUrl,
      };
      setMessages([...newMessages, assistantMessage]);
    } catch (error) {
      console.error(error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'エラーが発生しました。もう一度お試しください。',
      };
      setMessages([...newMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='flex flex-col h-full'>
      <header className='bg-gray-200 dark:bg-gray-900 p-4 text-center rounded-t-lg'>
        <h1 className='text-xl font-bold text-gray-800 dark:text-gray-200'>
          データ分析＆可視化アシスタント(MCPサーバーのデモ)
        </h1>
        <p className='text-sm text-gray-600 dark:text-gray-400'>
          架空の企業データをAIを使って分析しましょう。
        </p>
      </header>
      <div className='flex-1 overflow-y-auto p-6 space-y-4'>
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-xl p-3 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
              }`}
            >
              <p className='whitespace-pre-wrap'>{msg.content}</p>
              {msg.imageUrl && (
                <div className='mt-2'>
                  <img
                    src={msg.imageUrl}
                    alt='Generated Chart'
                    className='rounded-lg max-w-full h-auto'
                  />
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className='flex justify-start'>
            <div className='max-w-lg p-3 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'>
              <div className='flex items-center space-x-2'>
                <div className='w-2 h-2 bg-gray-500 rounded-full animate-pulse'></div>
                <div className='w-2 h-2 bg-gray-500 rounded-full animate-pulse delay-75'></div>
                <div className='w-2 h-2 bg-gray-500 rounded-full animate-pulse delay-150'></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className='border-t border-gray-200 dark:border-gray-700 p-4'>
        <form onSubmit={handleSubmit} className='flex items-center space-x-2'>
          <input
            type='text'
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder='メッセージを入力してください...'
            className='flex-1 p-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
            disabled={isLoading}
          />
          <button
            type='submit'
            className='px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-blue-300'
            disabled={isLoading || !input.trim()}
          >
            送信
          </button>
        </form>
      </div>
    </div>
  );
}
