"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, Database, Zap, BookOpen } from 'lucide-react';

interface Metrics {
  corpus_coverage_pct: number;
  total_cached_queries: number;
  fallback_mode: boolean;
  collections: string[];
}

export default function LiveMetrics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get("http://localhost:8000/metrics");
        setMetrics(response.data);
      } catch (error) {
        console.error("Failed to fetch metrics", error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-full bg-[#050505]">
      {/* Header */}
      <div className="flex-none p-6 border-b border-[#222]">
        <h1 className="text-2xl font-bold uppercase tracking-tight">System Metrics</h1>
        <p className="text-sm text-slate-400 mt-1">Live overview of the Industrial Copilot platform.</p>
      </div>

      <div className="flex-1 p-8">
        {!metrics ? (
            <div className="flex items-center justify-center h-full text-slate-500">
                Loading metrics...
            </div>
        ) : (
            <div className="grid grid-cols-2 gap-6 max-w-4xl mx-auto">
                <div className="glass-card p-6 flex flex-col items-center justify-center text-center">
                    <Database size={32} className="text-blue-400 mb-4" />
                    <h3 className="text-sm font-semibold text-slate-400">CORPUS COVERAGE</h3>
                    <p className="text-4xl font-bold mt-2 text-white">{metrics.corpus_coverage_pct}%</p>
                </div>
                
                <div className="glass-card p-6 flex flex-col items-center justify-center text-center">
                    <Zap size={32} className="text-yellow-400 mb-4" />
                    <h3 className="text-sm font-semibold text-slate-400">CACHED QUERIES</h3>
                    <p className="text-4xl font-bold mt-2 text-white">{metrics.total_cached_queries}</p>
                </div>

                <div className="glass-card p-6 flex flex-col items-center justify-center text-center">
                    <Activity size={32} className={metrics.fallback_mode ? "text-red-400 mb-4" : "text-emerald-400 mb-4"} />
                    <h3 className="text-sm font-semibold text-slate-400">FALLBACK MODE</h3>
                    <p className="text-xl font-bold mt-2 text-white">
                        {metrics.fallback_mode ? (
                            <span className="px-3 py-1 bg-red-400/20 text-red-400 rounded-full">ACTIVE</span>
                        ) : (
                            <span className="px-3 py-1 bg-emerald-400/20 text-emerald-400 rounded-full">INACTIVE</span>
                        )}
                    </p>
                </div>

                <div className="glass-card p-6 flex flex-col items-center justify-center text-center">
                    <BookOpen size={32} className="text-purple-400 mb-4" />
                    <h3 className="text-sm font-semibold text-slate-400">ACTIVE COLLECTIONS</h3>
                    <div className="flex flex-wrap justify-center gap-2 mt-4">
                        {metrics.collections.map(c => (
                            <span key={c} className="text-xs px-2 py-1 bg-white/10 rounded-md text-slate-200">
                                {c}
                            </span>
                        ))}
                    </div>
                </div>
            </div>
        )}
      </div>
    </div>
  );
}
