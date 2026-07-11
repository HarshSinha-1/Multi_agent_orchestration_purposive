'use client';

import React, { useState, useEffect } from 'react';
import { AgentSelector, AgentType } from '../components/AgentSelector';
import { ChatWindow } from '../components/ChatWindow';

export default function Home() {
  const [selectedAgent, setSelectedAgent] = useState<AgentType>('hr');
  const [notionMcpStatus, setNotionMcpStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');

  const checkNotionStatus = async () => {
    setNotionMcpStatus('checking');
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const res = await fetch(`${backendUrl}/api/v1/hr/notion-status`);
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'connected') {
          setNotionMcpStatus('connected');
        } else {
          setNotionMcpStatus('disconnected');
        }
      } else {
        setNotionMcpStatus('disconnected');
      }
    } catch (err) {
      console.error("Failed to check Notion status", err);
      setNotionMcpStatus('disconnected');
    }
  };

  useEffect(() => {
    checkNotionStatus();
  }, []);

  return (
    <main className="app-container">
      <div style={{ height: '100%', minHeight: 0, overflow: 'hidden' }}>
        <AgentSelector 
          selectedAgent={selectedAgent} 
          onChange={setSelectedAgent} 
          notionMcpStatus={notionMcpStatus}
        />
      </div>
      <div style={{ height: '100%', minHeight: 0, overflow: 'hidden' }}>
        <ChatWindow 
          agentType={selectedAgent} 
          notionMcpStatus={notionMcpStatus}
          onCheckNotionStatus={checkNotionStatus}
        />
      </div>
    </main>
  );
}

