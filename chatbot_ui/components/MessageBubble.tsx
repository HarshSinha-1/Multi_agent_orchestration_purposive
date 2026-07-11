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

const formatMessageText = (text: string) => {
  if (!text) return "";
  const lines = text.split('\n');

  return lines.map((line, lineIndex) => {
    let content: React.ReactNode = line;
    let isHeader = false;
    let headerLevel = 0;
    let isListItem = false;

    // Check for headers (e.g. ### Header)
    const headerMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headerMatch) {
      isHeader = true;
      headerLevel = headerMatch[1].length;
      content = headerMatch[2];
    } else {
      // Check for bullet items
      const listMatch = line.match(/^(\s*)[-*+]\s+(.*)$/);
      if (listMatch) {
        isListItem = true;
        content = listMatch[2];
      }
    }

    // Parse bold markdown **text** inside the line
    if (typeof content === 'string') {
      const parts = content.split(/(\*\*.*?\*\*)/g);
      content = parts.map((part, partIndex) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={partIndex}>{part.slice(2, -2)}</strong>;
        }
        return part;
      });
    }

    if (isHeader) {
      const HeaderTag = `h${Math.min(headerLevel + 2, 6)}` as keyof JSX.IntrinsicElements;
      return (
        <HeaderTag key={lineIndex} style={{ margin: '12px 0 6px 0', fontWeight: 700, color: 'inherit' }}>
          {content}
        </HeaderTag>
      );
    }

    if (isListItem) {
      return (
        <div key={lineIndex} style={{ display: 'flex', alignItems: 'flex-start', margin: '4px 0 4px 8px' }}>
          <span style={{ marginRight: '6px' }}>•</span>
          <div>{content}</div>
        </div>
      );
    }

    return (
      <div key={lineIndex} style={{ minHeight: '1.2em', marginBottom: lineIndex === lines.length - 1 ? 0 : '4px' }}>
        {content}
      </div>
    );
  });
};

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
          }}
        >
          {formatMessageText(message.text)}
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
