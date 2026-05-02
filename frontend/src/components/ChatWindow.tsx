import { useEffect, useRef, useState } from 'react';
import type { FC, FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Brain } from 'lucide-react';

interface ToolCall {
  name: string;
  args: any;
  success?: boolean;
  result?: any;
  error?: string;
}

interface Message {
  role: 'user' | 'bot';
  content: string;
  skill_used?: string;
  x_axis?: string;
  y_axis?: string;
  timestamp: string;
  debug?: { steps: string[] };
  tools?: ToolCall[];
  pending?: boolean;
}

interface ChatWindowProps {
  messages: Message[];
  onSendMessage: (msg: string) => void;
  isLoading: boolean;
}

export const ChatWindow: FC<ChatWindowProps> = ({ messages, onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input);
    setInput('');
  };

  return (
    <div className="flex-1 flex flex-col bg-bg-0 relative overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 scroll-smooth">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center mt-32 text-center opacity-50">
            <div className="text-6xl mb-6">💹</div>
            <h2 className="text-2xl font-bold mb-2">欢迎进入专家矩阵</h2>
            <p className="text-sm max-width-[400px]">机构级交易情报，全天候为您服务。请开始您的咨询。</p>
          </div>
        )}
        
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-4 max-w-[90%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
            >
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 border ${
                msg.role === 'user' ? 'border-accent text-accent' : 'border-white/10 bg-bg-2'
              }`}>
                {msg.role === 'user' ? 'Y' : 'S'}
              </div>
              
              <div className="flex flex-col gap-2">
                <div className={`flex items-center gap-3 text-[11px] text-text-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <span className="font-bold">{msg.role === 'user' ? 'YOU' : 'SUCKER_MATRIX'}</span>
                  <span>{msg.timestamp}</span>
                  {msg.x_axis && <span className="text-accent font-mono">[{msg.x_axis}{msg.y_axis}]</span>}
                  {msg.skill_used && (
                    <span className="bg-gradient-to-br from-yellow-600 to-yellow-400 text-black px-2 py-0.5 rounded-full font-bold text-[9px] uppercase tracking-tighter">
                      ⚡ {msg.skill_used}
                    </span>
                  )}
                </div>
                
                <div className={`p-4 rounded-r text-sm leading-relaxed ${
                  msg.role === 'user' ? 'bg-bg-3 rounded-tr-none' : 'bg-bg-2 border border-white/5 rounded-tl-none'
                }`}>
                  {msg.content
                    ? msg.content.split('\n').map((line, idx) => (
                        <p key={idx} className={idx > 0 ? 'mt-2' : ''}>{line}</p>
                      ))
                    : msg.pending && (
                        <div className="flex items-center gap-2 text-text-3 text-xs">
                          <span className="inline-flex gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: '0ms' }} />
                            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: '150ms' }} />
                            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: '300ms' }} />
                          </span>
                          矩阵推理中...
                        </div>
                      )}
                </div>

                {msg.tools && msg.tools.length > 0 && (
                  <div className="flex flex-col gap-1.5 mt-1">
                    {msg.tools.map((tool, ti) => {
                      const failed = tool.success === false;
                      const pending = tool.success === undefined && msg.pending;
                      const resultStr = tool.result !== undefined
                        ? (typeof tool.result === 'string' ? tool.result : JSON.stringify(tool.result, null, 2))
                        : '';
                      const argsStr = tool.args ? JSON.stringify(tool.args, null, 2) : '';
                      return (
                        <details
                          key={ti}
                          open={failed}
                          className={`rounded border text-[10px] font-mono ${
                            failed
                              ? 'border-red-500/40 bg-red-500/5'
                              : pending
                              ? 'border-yellow-500/30 bg-yellow-500/5'
                              : 'border-accent/20 bg-accent/5'
                          }`}
                        >
                          <summary className={`cursor-pointer px-2 py-1 flex items-center gap-2 list-none ${
                            failed ? 'text-red-300' : pending ? 'text-yellow-300' : 'text-accent'
                          }`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${
                              failed ? 'bg-red-400' : pending ? 'bg-yellow-400 animate-pulse' : 'bg-accent'
                            }`} />
                            <span className="font-bold">{tool.name?.toUpperCase()}</span>
                            <span className="opacity-60">
                              {failed ? '✗ FAIL' : pending ? '… RUNNING' : '✓ OK'}
                            </span>
                          </summary>
                          <div className="px-3 py-2 border-t border-white/5 space-y-2 text-text-2">
                            {argsStr && (
                              <div>
                                <div className="text-text-3 mb-0.5 text-[9px] uppercase tracking-wider">args</div>
                                <pre className="whitespace-pre-wrap break-all text-[10px] opacity-80">{argsStr}</pre>
                              </div>
                            )}
                            {tool.error && (
                              <div>
                                <div className="text-red-400 mb-0.5 text-[9px] uppercase tracking-wider">error</div>
                                <pre className="whitespace-pre-wrap break-all text-[10px] text-red-300">{tool.error}</pre>
                              </div>
                            )}
                            {resultStr && (
                              <div>
                                <div className="text-text-3 mb-0.5 text-[9px] uppercase tracking-wider">result</div>
                                <pre className="whitespace-pre-wrap break-all text-[10px] opacity-80 max-h-48 overflow-y-auto">{resultStr}</pre>
                              </div>
                            )}
                          </div>
                        </details>
                      );
                    })}
                  </div>
                )}

                {msg.debug?.steps && msg.debug.steps.length > 0 && (
                  <details className="mt-2 group" open={msg.pending}>
                    <summary className="text-[10px] text-text-3 cursor-pointer hover:text-text-2 flex items-center gap-1 list-none">
                      <Brain size={12} /> {msg.pending ? `矩阵思辨中 · ${msg.debug.steps.length} 步` : '查看矩阵思辨过程'}
                    </summary>
                    <div className="mt-2 p-3 bg-black/30 rounded border border-white/5 font-mono text-[11px] text-text-2 space-y-1">
                      {msg.debug.steps.map((step, si) => {
                        const isLast = si === msg.debug!.steps.length - 1;
                        const live = msg.pending && isLast;
                        return (
                          <div key={si} className={live ? 'text-accent' : 'opacity-70'}>
                            {live ? '▶' : '>'} {step}
                          </div>
                        );
                      })}
                    </div>
                  </details>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={endRef} />
      </div>

      <div className="p-6 bg-bg-1 border-t border-white/5">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex gap-3 bg-bg-2 p-2 rounded-r border border-white/5 focus-within:border-accent transition-all">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="下达矩阵查询指令..."
            className="flex-1 bg-transparent border-none outline-none px-3 text-sm text-white"
          />
          <button 
            disabled={isLoading}
            className="w-10 h-10 rounded-lg bg-accent text-bg-0 flex items-center justify-center hover:scale-105 active:scale-95 transition-all disabled:opacity-50"
          >
            <Send size={18} strokeWidth={3} />
          </button>
        </form>
      </div>
    </div>
  );
};
