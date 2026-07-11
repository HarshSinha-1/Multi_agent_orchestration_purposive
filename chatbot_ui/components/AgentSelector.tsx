import React from 'react';
import { Users, Server, DollarSign, BarChart2 } from 'lucide-react';

export type AgentType = 'hr' | 'it' | 'sales' | 'executive';

interface AgentSelectorProps {
  selectedAgent: AgentType;
  onChange: (agent: AgentType) => void;
  notionMcpStatus: 'checking' | 'connected' | 'disconnected';
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({ selectedAgent, onChange, notionMcpStatus }) => {
  const agents = [
    {
      id: 'hr' as AgentType,
      name: 'HR Agent',
      desc: 'Recruitment & Screening',
      icon: Users,
      color: 'var(--color-hr)',
      glow: 'var(--color-hr-glow)',
    },
    {
      id: 'it' as AgentType,
      name: 'IT Agent',
      desc: 'Incident Resolution & RCA',
      icon: Server,
      color: 'var(--color-it)',
      glow: 'var(--color-it-glow)',
    },
    {
      id: 'sales' as AgentType,
      name: 'Sales Agent',
      desc: 'Proposals & Insights',
      icon: DollarSign,
      color: 'var(--color-sales)',
      glow: 'var(--color-sales-glow)',
    },
    {
      id: 'executive' as AgentType,
      name: 'Executive Agent',
      desc: 'KPI Dashboard & BI',
      icon: BarChart2,
      color: 'var(--color-exec)',
      glow: 'var(--color-exec-glow)',
    },
  ];

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
      <div style={{ marginBottom: '10px' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>🧠</span> Brain Console
        </h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Select agent domain to route query
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flexGrow: 1 }}>
        {agents.map((agent) => {
          const Icon = agent.icon;
          const isSelected = selectedAgent === agent.id;
          return (
            <button
              key={agent.id}
              onClick={() => onChange(agent.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                border: isSelected ? `1px solid ${agent.color}` : '1px solid transparent',
                background: isSelected ? agent.glow : 'rgba(255, 255, 255, 0.02)',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'var(--transition-smooth)',
                outline: 'none',
              }}
            >
              <div
                className={agent.id === 'hr' ? (
                  notionMcpStatus === 'connected' ? 'mcp-radar-connected' :
                  notionMcpStatus === 'disconnected' ? 'mcp-radar-disconnected' : 'mcp-radar-checking'
                ) : ''}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '40px',
                  height: '40px',
                  borderRadius: '8px',
                  background: isSelected ? 'rgba(0, 0, 0, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                  color: isSelected ? agent.color : 'var(--text-secondary)',
                  transition: 'var(--transition-smooth)',
                }}
              >
                <Icon size={20} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', width: '100%', minWidth: 0 }}>
                <span
                  style={{
                    fontSize: '0.9rem',
                    fontWeight: 500,
                    color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
                  }}
                >
                  {agent.name}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', opacity: 0.8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {agent.desc}
                </span>
                {agent.id === 'hr' && (
                  <span 
                    style={{
                      fontSize: '0.625rem',
                      padding: '2px 6px',
                      borderRadius: '8px',
                      background: notionMcpStatus === 'connected' 
                        ? 'rgba(0, 255, 136, 0.08)' 
                        : notionMcpStatus === 'disconnected' 
                          ? 'rgba(255, 51, 51, 0.08)' 
                          : 'rgba(255, 187, 0, 0.08)',
                      border: notionMcpStatus === 'connected' 
                        ? '1px solid rgba(0, 255, 136, 0.3)' 
                        : notionMcpStatus === 'disconnected' 
                          ? '1px solid rgba(255, 51, 51, 0.3)' 
                          : '1px solid rgba(255, 187, 0, 0.3)',
                      color: notionMcpStatus === 'connected' 
                        ? '#00ff88' 
                        : notionMcpStatus === 'disconnected' 
                          ? '#ff4444' 
                          : '#ffbb00',
                      fontWeight: 600,
                      marginTop: '4px',
                      alignSelf: 'flex-start',
                      width: 'fit-content',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <span 
                      className="mcp-status-dot-pulse"
                      style={{ 
                        width: '4px', 
                        height: '4px', 
                        borderRadius: '50%', 
                        background: 'currentColor',
                        display: 'inline-block'
                      }}
                    />
                    {notionMcpStatus === 'connected' 
                      ? 'Notion Active' 
                      : notionMcpStatus === 'disconnected' 
                        ? 'Notion Offline' 
                        : 'Checking...'}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
      
      <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
        <span>Prototype Console v1.0.0</span>
      </div>
    </div>
  );
};

