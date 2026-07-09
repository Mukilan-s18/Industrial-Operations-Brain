"use client";

import React, { useState } from 'react';
import { Shield, Settings, Server, User, Search, Activity } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const PERSONAS = [
  { id: 'Ravi (Operator)', role: 'Operator' },
  { id: 'Priya (Engineer)', role: 'Engineer' },
  { id: 'Arjun (Auditor)', role: 'Auditor' },
];

export default function Sidebar({
  activeRole,
  setActiveRole,
  activeTab,
  setActiveTab
}: {
  activeRole: string;
  setActiveRole: (role: string) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}) {
  return (
    <div className="w-72 bg-[#0A0A0B] border-r border-[#222] h-full flex flex-col pt-8 pb-4 px-6 fixed left-0 top-0">
      <div className="mb-8">
        <h2 className="text-xl font-bold uppercase tracking-tight border-b-2 border-white inline-block pb-1">
          Operations Brain
        </h2>
        <p className="text-sm text-slate-400 mt-1">Industrial Copilot</p>
      </div>

      <div className="flex-1 space-y-8">
        {/* RBAC Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-300">
            <Shield size={16} />
            <span>IDENTITY & ACCESS</span>
          </div>
          <div className="space-y-2">
            {PERSONAS.map((p) => (
              <button
                key={p.id}
                onClick={() => setActiveRole(p.id)}
                className={twMerge(
                  "w-full flex items-center gap-3 px-3 py-2 rounded-md transition-all text-sm font-medium",
                  activeRole === p.id 
                    ? "bg-white text-black shadow-[0_0_15px_rgba(255,255,255,0.2)]" 
                    : "text-slate-400 hover:bg-white/10 hover:text-white"
                )}
              >
                <User size={16} />
                {p.id}
              </button>
            ))}
          </div>
        </div>

        {/* Navigation */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-300">
            <Settings size={16} />
            <span>MODULES</span>
          </div>
          <div className="space-y-2">
            <button 
              onClick={() => setActiveTab('chat')}
              className={twMerge(
                "w-full flex items-center gap-3 px-3 py-2 rounded-md transition-all text-sm font-medium",
                activeTab === 'chat' ? "bg-white/10 text-white border border-white/20" : "text-slate-400 hover:bg-white/10 hover:text-white"
              )}
            >
              <Search size={16} />
              RCA Chat
            </button>
            <button 
              onClick={() => setActiveTab('graph')}
              className={twMerge(
                "w-full flex items-center gap-3 px-3 py-2 rounded-md transition-all text-sm font-medium",
                activeTab === 'graph' ? "bg-white/10 text-white border border-white/20" : "text-slate-400 hover:bg-white/10 hover:text-white"
              )}
            >
              <Server size={16} />
              Knowledge Graph
            </button>
            <button 
              onClick={() => setActiveTab('metrics')}
              className={twMerge(
                "w-full flex items-center gap-3 px-3 py-2 rounded-md transition-all text-sm font-medium",
                activeTab === 'metrics' ? "bg-white/10 text-white border border-white/20" : "text-slate-400 hover:bg-white/10 hover:text-white"
              )}
            >
              <Activity size={16} />
              Live Metrics
            </button>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-[#222]">
        <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-400/10 p-2 rounded">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          SYSTEM ONLINE
        </div>
      </div>
    </div>
  );
}
