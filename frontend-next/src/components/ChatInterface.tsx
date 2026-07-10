"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, AlertTriangle, CheckCircle, Database, Mic, Image as ImageIcon, X } from 'lucide-react';
import api, { fetchToken } from '@/lib/api';
import { twMerge } from 'tailwind-merge';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  image?: string;
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
  const [isListening, setIsListening] = useState(false);
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImageBase64(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;
        
        recognitionRef.current.onresult = (event: any) => {
          let finalTranscript = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            }
          }
          if (finalTranscript) {
             setInput(prev => prev ? prev + " " + finalTranscript : finalTranscript);
          }
        };

        recognitionRef.current.onerror = (event: any) => {
          console.error("Speech recognition error", event.error);
          setIsListening(false);
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      }
    }
  }, []);

  const toggleMicrophone = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }
    
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (e) {
        console.error(e);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !imageBase64 || isLoading) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input, image: imageBase64 || undefined };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setImageBase64(null);
    setIsLoading(true);

    try {
      await fetchToken(activeRole);
      
      const aiMsgId = (Date.now() + 1).toString();
      const initialAiMsg: Message = {
        id: aiMsgId,
        role: 'assistant',
        content: ""
      };
      setMessages(prev => [...prev, initialAiMsg]);

      // Use fetch directly for streaming
      const response = await fetch("http://localhost:8000/api/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify({
          query: userMsg.content,
          role: activeRole,
          image: userMsg.image
        })
      });

      if (!response.ok) throw new Error("Stream failed");
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (reader) {
        let done = false;
        while (!done) {
          const { value, done: doneReading } = await reader.read();
          done = doneReading;
          if (value) {
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const event = JSON.parse(line.slice(6));
                  
                  setMessages(prev => prev.map(msg => {
                    if (msg.id === aiMsgId) {
                      const newContent = event.answer || msg.content || `[Agent Status]: Running step '${event.node}'...`;
                      return {
                        ...msg,
                        content: newContent,
                        metrics: event.answer ? {
                          contradiction: event.contradiction_detected || false,
                          faithfulness: event.faithfulness_score || 0,
                          sources: event.sources ? event.sources.map((s: any) => s.doc || s) : []
                        } : msg.metrics,
                        action: event.action_taken && event.action_taken !== "NONE" ? {
                          taken: event.action_taken,
                          result: event.action_result
                        } : msg.action
                      };
                    }
                    return msg;
                  }));
                } catch (e) {
                  console.error("Error parsing stream JSON", e);
                }
              }
            }
          }
        }
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => prev.map(msg => 
        msg.id === (Date.now() + 1).toString() ? { ...msg, content: "Error connecting to the Industrial Brain API." } : msg
      ));
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

        <AnimatePresence>
        {messages.map((msg) => (
          <motion.div 
            key={msg.id} 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={twMerge(
              "flex w-full",
              msg.role === 'user' ? "justify-end" : "justify-start"
            )}
          >
            <div className={twMerge(
              "max-w-[80%] rounded-xl p-5",
              msg.role === 'user' 
                ? "bg-white text-black" 
                : "glass-card text-slate-200 border-[#222]"
            )}>
              <div className="whitespace-pre-wrap font-sans text-[15px] leading-relaxed">
                {msg.content}
              </div>
              
              {msg.image && (
                <img src={msg.image} alt="User upload" className="mt-3 max-w-full rounded-lg max-h-48 object-contain border border-[#333]" />
              )}
              
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
          </motion.div>
        ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }} 
            className="flex w-full justify-start"
          >
            <div className="glass-card max-w-[80%] rounded-xl p-5 border-emerald-500/20 text-slate-400 flex items-center gap-3">
              <div className="flex gap-1">
                <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0 }} className="w-2 h-2 bg-emerald-400 rounded-full"></motion.div>
                <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }} className="w-2 h-2 bg-emerald-400 rounded-full"></motion.div>
                <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }} className="w-2 h-2 bg-emerald-400 rounded-full"></motion.div>
              </div>
              <span className="text-emerald-400/80 font-mono text-sm">Agent is reasoning...</span>
            </div>
          </motion.div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      {/* Input */}
      <div className="flex-none p-6 border-t border-[#222] relative">
        {imageBase64 && (
          <div className="absolute bottom-full left-6 mb-2">
            <div className="relative inline-block">
              <img src={imageBase64} alt="Preview" className="h-16 w-16 object-cover rounded-md border border-[#333]" />
              <button 
                type="button"
                onClick={() => setImageBase64(null)}
                className="absolute -top-2 -right-2 p-1 bg-red-500 rounded-full text-white hover:bg-red-600 shadow-md"
              >
                <X size={12} />
              </button>
            </div>
          </div>
        )}
        <form onSubmit={handleSubmit} className="relative">
          <input
            type="file"
            accept="image/*"
            ref={fileInputRef}
            onChange={handleImageChange}
            className="hidden"
          />
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask as ${activeRole}...`}
            className="w-full bg-[#111] border border-[#333] rounded-lg pl-5 pr-32 py-4 text-white placeholder-slate-500 focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all font-sans"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-2 bg-[#222] text-slate-400 hover:bg-[#333] hover:text-white rounded-md transition-colors"
            >
              <ImageIcon size={18} />
            </button>
            <button
              type="button"
              onClick={toggleMicrophone}
              className={`p-2 rounded-md transition-colors ${isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-[#222] text-slate-400 hover:bg-[#333] hover:text-white'}`}
            >
              <Mic size={18} />
            </button>
            <button 
              type="submit"
              disabled={isLoading || (!input.trim() && !imageBase64)}
              className="p-2 bg-white text-black rounded-md disabled:opacity-50 hover:bg-slate-200 transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
