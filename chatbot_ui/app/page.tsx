'use client';

import React, { useState } from 'react';
import { AgentSelector, AgentType } from '../components/AgentSelector';
import { ChatWindow } from '../components/ChatWindow';

export default function Home() {
  const [selectedAgent, setSelectedAgent] = useState<AgentType>('hr');

  return (
    <main className="app-container">
      <div style={{ height: '100%' }}>
        <AgentSelector selectedAgent={selectedAgent} onChange={setSelectedAgent} />
      </div>
      <div style={{ height: '100%' }}>
        <ChatWindow agentType={selectedAgent} />
      </div>
    </main>
  );
}
