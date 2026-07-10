"use client";

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';
import dynamic from 'next/dynamic';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

const COLORS: Record<string, string> = {
  "EQUIPMENT": "#3B82F6",
  "REGULATION": "#EF4444",
  "FAILURE_MODE": "#F59E0B",
  "PARAMETER": "#10B981",
  "PERSON": "#8B5CF6",
  "DOCUMENT": "#06B6D4",
  "DATE": "#6B7280",
};

export default function KnowledgeGraph({ activeRole }: { activeRole: string }) {
  const [nodeId, setNodeId] = useState("");
  const [query, setQuery] = useState("");
  
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const fgRef = useRef<any>();

  useEffect(() => {
    const fetchGraphData = async () => {
      setIsLoading(true);
      try {
        const [nodesRes, edgesRes] = await Promise.all([
          fetch('http://localhost:8000/api/nodes'),
          fetch('http://localhost:8000/api/edges')
        ]);
        const nodes = await nodesRes.json();
        const edges = await edgesRes.json();

        // Apply RBAC filtering locally just like the backend did
        let filteredNodes = nodes;
        let filteredEdges = edges;
        
        if (activeRole.includes("Operator")) {
          const restrictedNodes = new Set(
            nodes.filter((n: any) => n.label === "REGULATION").map((n: any) => n.id)
          );
          filteredNodes = nodes.filter((n: any) => !restrictedNodes.has(n.id));
          filteredEdges = edges.filter(
            (e: any) => !restrictedNodes.has(e.source) && !restrictedNodes.has(e.target)
          );
        }

        setGraphData({
          nodes: filteredNodes,
          links: filteredEdges
        });
      } catch (err) {
        console.error("Failed to load graph data", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchGraphData();
  }, [activeRole]);

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setNodeId(query);
    
    // Find node and center camera
    if (fgRef.current && query) {
      const node = graphData.nodes.find((n: any) => n.id.toLowerCase() === query.toLowerCase());
      if (node) {
        fgRef.current.centerAt(node.x, node.y, 1000);
        fgRef.current.zoom(4, 2000);
      }
    }
  }, [query, graphData.nodes]);

  const handleNodeClick = useCallback((node: any) => {
    setQuery(node.id);
    setNodeId(node.id);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(4, 2000);
    }
  }, []);

  const getNodeColor = useCallback((node: any) => {
    return COLORS[node.label] || "#94A3B8";
  }, []);

  const getEdgeColor = useCallback((link: any) => {
    const type = link.type;
    if (type === "HAS_FAILURE") return "#3B82F6";
    if (type === "HAS_INSPECTION") return "#10B981";
    if (type === "GOVERNED_BY") return "#EF4444";
    return "rgba(71, 85, 105, 0.5)"; // faded standard color
  }, []);

  return (
    <div className="flex flex-col h-full bg-[#050505]">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex-none p-6 border-b border-[#222] z-10">
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
      </motion.div>

      {/* Graph Canvas */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1, duration: 0.4 }} className="flex-1 bg-black overflow-hidden relative">
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500">
             Loading graph topology...
          </div>
        ) : (
          <div className="w-full h-full relative cursor-move">
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              nodeLabel={(node: any) => {
                const props = Object.entries(node.properties || {})
                  .map(([k, v]) => `${k}: ${v}`)
                  .join('<br>');
                return `<div class="bg-[#111] p-2 rounded border border-[#333] text-white text-xs font-mono">
                  <b>${node.id}</b> <span class="text-slate-400">(${node.label})</span>
                  ${props ? `<div class="mt-1 pt-1 border-t border-[#333]">${props}</div>` : ''}
                </div>`;
              }}
              nodeColor={getNodeColor}
              nodeRelSize={6}
              nodeVal={(node: any) => node.id === nodeId ? 15 : (node.label === "DOCUMENT" ? 4 : 8)}
              linkColor={getEdgeColor}
              linkWidth={(link: any) => 1 + ((link.weight || 1) - 1) * 1.5}
              linkDirectionalArrowLength={3.5}
              linkDirectionalArrowRelPos={1}
              onNodeClick={handleNodeClick}
              backgroundColor="#000000"
            />
          </div>
        )}
      </motion.div>
    </div>
  );
}
