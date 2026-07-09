"use client";

import React, { useState } from 'react';
import { Search } from 'lucide-react';

export default function KnowledgeGraph({ activeRole }: { activeRole: string }) {
  const [nodeId, setNodeId] = useState("");
  const [query, setQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setNodeId(query);
  };

  const iframeSrc = `http://localhost:8000/api/graph-viz?role=${encodeURIComponent(activeRole)}${nodeId ? `&node_id=${encodeURIComponent(nodeId)}` : ""}`;

  return (
    <div className="flex flex-col h-full bg-[#050505]">
      {/* Header */}
      <div className="flex-none p-6 border-b border-[#222]">
        <h1 className="text-2xl font-bold uppercase tracking-tight">Knowledge Graph</h1>
        <p className="text-sm text-slate-400 mt-1">Interactive visualization of the operations data.</p>
        
        <form onSubmit={handleSearch} className="mt-4 relative max-w-md">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search Ego Network (e.g. P-101)..."
            className="w-full bg-[#111] border border-[#333] rounded-lg pl-10 pr-4 py-2 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all font-sans"
          />
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
        </form>
      </div>

      {/* Graph iframe */}
      <div className="flex-1 bg-black overflow-hidden relative p-4">
        <div className="glass-card w-full h-full p-2">
            <iframe 
                src={iframeSrc} 
                className="w-full h-full rounded-lg bg-black border-none"
                title="Knowledge Graph Visualization"
            />
        </div>
      </div>
    </div>
  );
}
