"use client";

import { useState } from "react";
import Sidebar, { PERSONAS } from "@/components/Sidebar";
import ChatInterface from "@/components/ChatInterface";
import KnowledgeGraph from "@/components/KnowledgeGraph";
import LiveMetrics from "@/components/LiveMetrics";
import { AnimatePresence, motion } from "framer-motion";

export default function Home() {
  const [activeRole, setActiveRole] = useState(PERSONAS[0].id);
  const [activeTab, setActiveTab] = useState("chat");

  return (
    <div className="flex h-screen bg-black overflow-hidden">
      <Sidebar 
        activeRole={activeRole} setActiveRole={setActiveRole}
        activeTab={activeTab} setActiveTab={setActiveTab}
      />
      
      <main className="ml-72 flex-1 h-full relative overflow-y-auto bg-black">
        <AnimatePresence mode="wait">
          {activeTab === "chat" && (
            <motion.div key="chat" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="h-full w-full">
              <ChatInterface activeRole={activeRole} />
            </motion.div>
          )}
          {activeTab === "graph" && (
            <motion.div key="graph" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="h-full w-full">
              <KnowledgeGraph activeRole={activeRole} />
            </motion.div>
          )}
          {activeTab === "metrics" && (
            <motion.div key="metrics" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="h-full w-full">
              <LiveMetrics activeRole={activeRole} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
