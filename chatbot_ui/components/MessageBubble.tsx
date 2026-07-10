import React from 'react';
import { AgentType } from './AgentSelector';

export interface Message {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  agentType?: AgentType;
  processingTime?: number;
  confidenceScore?: number;
  timestamp: Date;
}

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.sender === 'user';
  
  const agentColor = {
    hr: 'var(--color-hr)',
    it: 'var(--color-it)',
    sales: 'var(--color-sales)',
    executive: 'var(--color-exec)',
  }[message.agentType || 'hr'];

  const agentBg = {
    hr: 'var(--color-hr-glow)',
    it: 'var(--color-it-glow)',
    sales: 'var(--color-sales-glow)',
    executive: 'var(--color-exec-glow)',
  }[message.agentType || 'hr'];

  return (
    <div
      className="animate-fade-in"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        width: '100%',
        marginBottom: '16px',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          maxWidth: '75%',
          padding: '14px 18px',
          borderRadius: '16px',
          borderTopRightRadius: isUser ? '4px' : '16px',
          borderTopLeftRadius: !isUser ? '4px' : '16px',
          background: isUser ? 'rgba(255, 255, 255, 0.05)' : agentBg,
          border: isUser ? '1px solid var(--border-glass)' : `1px solid ${agentColor}`,
          boxShadow: isUser ? 'none' : `0 4px 20px 0 ${agentBg}`,
        }}
      >
        {!isUser && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginBottom: '8px',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: agentColor,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            <span>🤖</span>
            <span>{message.agentType} agent</span>
          </div>
        )}

        <div
          style={{
            fontSize: '0.925rem',
            lineHeight: 1.5,
            color: 'var(--text-primary)',
            whiteSpace: 'pre-wrap',
          }}
        >
          {message.text}
        </div>

        {!isUser && message.processingTime !== undefined && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginTop: '10px',
              paddingTop: '8px',
              borderTop: '1px solid rgba(255, 255, 255, 0.05)',
              fontSize: '0.7rem',
              color: 'var(--text-secondary)',
            }}
          >
            <span>Time: <strong>{message.processingTime.toFixed(2)}s</strong></span>
            <span>Confidence: <strong>{((message.confidenceScore || 0.9) * 100).toFixed(0)}%</strong></span>
          </div>
        )}
      </div>
      
      <span
        style={{
          fontSize: '0.7rem',
          color: 'var(--text-secondary)',
          marginTop: '4px',
          padding: '0 8px',
          opacity: 0.7,
        }}
      >
        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </span>
    </div>
  );
};
