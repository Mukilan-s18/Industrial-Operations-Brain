"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, AlertTriangle, CheckCircle, Database } from 'lucide-react';
import axios from 'axios';
import { twMerge } from 'tailwind-merge';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  metrics?: {
    contradiction: boolean;
    faithfulness: number;
    sources: string[];
  };
  action?: {
    taken: string;
    result: string;
  };
}

export default function ChatInterface({ activeRole }: { activeRole: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post("http://localhost:8000/chat", {
        query: userMsg.content,
        role: activeRole,
      });

      const data = response.data;
      
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.final_answer || "No response generated.",
        metrics: {
          contradiction: data.contradiction_detected || false,
          faithfulness: data.faithfulness_score || 0,
          sources: data.sources || []
        },
        action: data.action_taken && data.action_taken !== "NONE" ? {
          taken: data.action_taken,
          result: data.action_result
        } : undefined
      };
      
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "Error connecting to the Industrial Brain API."
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#050505]">
      {/* Header */}
      <div className="flex-none p-6 border-b border-[#222]">
        <h1 className="text-2xl font-bold uppercase tracking-tight">Interactive RCA Chat</h1>
        <p className="text-sm text-slate-400 mt-1">Diagnosing issues and fetching real-time telemetry.</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center text-slate-500">
            <div className="text-center">
              <Database size={48} className="mx-auto mb-4 opacity-50" />
              <p>Ask a question about the P&ID, SOPs, or live SCADA data.</p>
              <p className="text-xs mt-2">Example: "Why is P-101 vibrating?"</p>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={twMerge(
            "flex w-full",
            msg.role === 'user' ? "justify-end" : "justify-start"
          )}>
            <div className={twMerge(
              "max-w-[80%] rounded-xl p-5",
              msg.role === 'user' 
                ? "bg-white text-black" 
                : "glass-card text-slate-200 border-[#222]"
            )}>
              <div className="whitespace-pre-wrap font-sans text-[15px] leading-relaxed">
                {msg.content}
              </div>
              
              {/* Metrics block for AI responses */}
              {msg.role === 'assistant' && msg.metrics && (
                <div className="mt-4 pt-4 border-t border-[#333] grid grid-cols-2 gap-4 text-xs font-mono">
                  <div className="flex items-center gap-2">
                    {msg.metrics.contradiction ? (
                      <span className="text-red-400 flex items-center gap-1"><AlertTriangle size={14} /> Contradiction Detected</span>
                    ) : (
                      <span className="text-emerald-400 flex items-center gap-1"><CheckCircle size={14} /> No Contradictions</span>
                    )}
                  </div>
                  <div className="text-slate-400 text-right">
                    Faithfulness: <span className="text-white">{msg.metrics.faithfulness.toFixed(2)}</span>
                  </div>
                  {msg.metrics.sources.length > 0 && (
                    <div className="col-span-2 text-slate-500 truncate">
                      Sources: {msg.metrics.sources.join(", ")}
                    </div>
                  )}
                </div>
              )}

              {/* Action block for Agent Actions */}
              {msg.role === 'assistant' && msg.action && (
                <div className="mt-4 p-3 bg-emerald-900/30 border border-emerald-500/30 rounded-lg text-emerald-400 text-sm flex items-start gap-2">
                  <CheckCircle size={16} className="mt-0.5 shrink-0" />
                  <div>
                    <div className="font-semibold">{msg.action.taken}</div>
                    <div className="text-emerald-500/80 text-xs mt-1">{msg.action.result}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex w-full justify-start">
            <div className="glass-card max-w-[80%] rounded-xl p-5 text-slate-400 flex items-center gap-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
              </div>
              Agent is reasoning...
            </div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      {/* Input */}
      <div className="flex-none p-6 border-t border-[#222]">
        <form onSubmit={handleSubmit} className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask as ${activeRole}...`}
            className="w-full bg-[#111] border border-[#333] rounded-lg pl-5 pr-14 py-4 text-white placeholder-slate-500 focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all font-sans"
          />
          <button 
            type="submit"
            disabled={isLoading || !input.trim()}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-white text-black rounded-md disabled:opacity-50 hover:bg-slate-200 transition-colors"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
