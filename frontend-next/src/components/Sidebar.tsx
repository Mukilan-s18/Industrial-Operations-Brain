"use client";

import React, { useState } from 'react';
import { Shield, Settings, Server, User, Search, Activity } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { motion } from 'framer-motion';

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
                className="w-full relative px-3 py-2 rounded-md transition-all text-sm font-medium flex items-center gap-3 text-slate-400 hover:text-white"
              >
                {activeRole === p.id && (
                  <motion.div
                    layoutId="activeRole"
                    className="absolute inset-0 bg-white shadow-[0_0_15px_rgba(255,255,255,0.2)] rounded-md"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <User size={16} className="relative z-10" />
                <span className={twMerge("relative z-10", activeRole === p.id ? "text-black" : "")}>{p.id}</span>
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
            {[
              { id: 'chat', label: 'RCA Chat', icon: Search },
              { id: 'graph', label: 'Knowledge Graph', icon: Server },
              { id: 'metrics', label: 'Live Metrics', icon: Activity }
            ].map((tab) => (
              <button 
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="w-full relative px-3 py-2 rounded-md transition-all text-sm font-medium flex items-center gap-3 text-slate-400 hover:text-white group"
              >
                {activeTab === tab.id && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute inset-0 bg-white/10 border border-white/20 rounded-md"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <tab.icon size={16} className="relative z-10 group-hover:scale-110 transition-transform" />
                <span className={twMerge("relative z-10", activeTab === tab.id ? "text-white" : "")}>{tab.label}</span>
              </button>
            ))}
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
