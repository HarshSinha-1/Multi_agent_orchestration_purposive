import React from 'react';
import { AgentType } from './AgentSelector';

interface TypingIndicatorProps {
  agentType: AgentType;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ agentType }) => {
  const agentColor = {
    hr: 'var(--color-hr)',
    it: 'var(--color-it)',
    sales: 'var(--color-sales)',
    executive: 'var(--color-exec)',
  }[agentType];

  const dotStyle = {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    backgroundColor: agentColor,
    animation: 'bounce 1s infinite ease-in-out',
    display: 'inline-block',
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '12px 18px',
        borderRadius: '16px',
        borderTopLeftRadius: '4px',
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid var(--border-glass)',
        width: 'max-content',
        marginBottom: '16px',
      }}
    >
      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
      `}</style>
      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginRight: '4px' }}>
        Agent thinking
      </span>
      <div style={{ display: 'flex', gap: '3px', alignItems: 'center' }}>
        <div style={{ ...dotStyle, animationDelay: '0s' }}></div>
        <div style={{ ...dotStyle, animationDelay: '0.2s' }}></div>
        <div style={{ ...dotStyle, animationDelay: '0.4s' }}></div>
      </div>
    </div>
  );
};
