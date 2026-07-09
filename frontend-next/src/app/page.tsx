"use client";

import { useState } from "react";
import Sidebar, { PERSONAS } from "@/components/Sidebar";
import ChatInterface from "@/components/ChatInterface";
import KnowledgeGraph from "@/components/KnowledgeGraph";
import LiveMetrics from "@/components/LiveMetrics";

export default function Home() {
  const [activeRole, setActiveRole] = useState(PERSONAS[0].id);
  const [activeTab, setActiveTab] = useState("chat");

  return (
    <div className="flex h-screen bg-black overflow-hidden">
      <Sidebar 
        activeRole={activeRole} setActiveRole={setActiveRole}
        activeTab={activeTab} setActiveTab={setActiveTab}
      />
      
      <main className="ml-72 flex-1 h-full relative overflow-y-auto">
        {activeTab === "chat" && <ChatInterface activeRole={activeRole} />}
        {activeTab === "graph" && <KnowledgeGraph activeRole={activeRole} />}
        {activeTab === "metrics" && <LiveMetrics />}
      </main>
    </div>
  );
}
