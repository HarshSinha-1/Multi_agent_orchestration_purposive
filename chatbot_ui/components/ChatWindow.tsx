import React, { useState, useEffect, useRef } from 'react';
import { Message, MessageBubble } from './MessageBubble';
import { AgentType } from './AgentSelector';
import { TypingIndicator } from './TypingIndicator';
import { Send, AlertCircle, RefreshCw, Paperclip } from 'lucide-react';

interface ChatWindowProps {
  agentType: AgentType;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ agentType }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // KPI Snapshots for Executive Dashboard Mode
  const [kpis, setKpis] = useState<any>(null);
  const [loadingKpis, setLoadingKpis] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize with greeting messages matching the agent
  useEffect(() => {
    const greeting = {
      hr: "Hello! I am the HR Agent. I can help you with candidate resume screening, job creation, and tracking recruitment pipelines. Try asking: 'Screen candidate Priya Sharma for backend role' or 'Create a new job for Senior Frontend Engineer'.",
      it: "IT Systems online. I can assist with ticket classification, error log triage, and incident root cause analysis. Try asking: 'Analyze timeout error log in checkout-service' or 'Submit ticket for database pool exhaustion'.",
      sales: "Welcome! I am your Sales proposal drafting assistant. I analyze leads, suggest pricing tiers, and generate custom proposals. Try asking: 'Draft standard proposal for lead Northwind Traders' or 'Ingest lead for NovaTech Solutions'.",
      executive: "Executive Reporting Hub loaded. I synthesize KPIs and analyze trend patterns to support leadership decisions. Try asking: 'Explain IT ticket MTTR trend and suggest actions' or 'Evaluate recruitment pipeline health'.",
    }[agentType];

    setMessages([
      {
        id: 'greet_' + agentType,
        sender: 'agent',
        text: greeting,
        agentType: agentType,
        timestamp: new Date(),
      },
    ]);
    
    // Fetch metrics if Executive Agent is selected
    if (agentType === 'executive') {
      fetchKpis();
    } else {
      setKpis(null);
    }
  }, [agentType]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const fetchKpis = async () => {
    setLoadingKpis(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const res = await fetch(`${backendUrl}/api/v1/executive/kpis`);
      if (res.ok) {
        const data = await res.json();
        setKpis(data);
      }
    } catch (err) {
      console.error("Failed to load KPIs", err);
    } finally {
      setLoadingKpis(false);
    }
  };

  const handleAttachmentClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setErrorMsg('');
    setIsLoading(true);

    const userMsgText = `📎 [Attached File: ${file.name}]`;
    const userMessage: Message = {
      id: 'usr_' + Date.now(),
      sender: 'user',
      text: userMsgText,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

    try {
      if (agentType === 'hr') {
        // Create requisition automatically
        const jobRes = await fetch(`${backendUrl}/api/v1/hr/jobs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: "Automated Evaluation Requisition",
            department: "AI & Software Division",
            full_jd_text: "Requires developer experience, programming languages (Python, JavaScript, Go etc), framework knowledge (FastAPI, React etc), database usage (SQL/NoSQL) and vector indexing."
          })
        });

        if (!jobRes.ok) {
          throw new Error("Failed to initialize job requisition for candidate screening");
        }

        const jobData = await jobRes.json();
        const jobId = jobData.job_id;

        // Upload resume via FormData
        const formData = new FormData();
        formData.append('file', file);
        formData.append('job_id', jobId);

        const uploadRes = await fetch(`${backendUrl}/api/v1/hr/resumes/upload`, {
          method: 'POST',
          body: formData
        });

        if (!uploadRes.ok) {
          throw new Error("Failed to process resume screening on server");
        }

        const candidateData = await uploadRes.json();

        // Format evaluation results
        const responseText = `📄 **Resume Screening Results**
Candidate: **${candidateData.name}**
Match Score: **${(candidateData.match_score * 100).toFixed(0)}%**
Recommendation: **${candidateData.recommendation.toUpperCase()}**

**Skills Matched:**
${candidateData.skills ? candidateData.skills.split(',').map((s: string) => `- ${s}`).join('\n') : 'None Identified'}

**Skills Missing:**
${candidateData.missing_skills ? candidateData.missing_skills.split(',').map((s: string) => `- ${s}`).join('\n') : 'None Identified'}

**Summary Evaluation:**
${candidateData.summary}`;

        const agentMessage: Message = {
          id: 'agt_' + Date.now(),
          sender: 'agent',
          text: responseText,
          agentType: 'hr',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, agentMessage]);

      } else if (agentType === 'it') {
        // Submit incident automatically
        const incidentRes = await fetch(`${backendUrl}/api/v1/it/incidents`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            affected_service: "Infrastructure Log Analyzer",
            description: `Automated analysis incident for log file: ${file.name}`
          })
        });

        if (!incidentRes.ok) {
          throw new Error("Failed to initialize incident ticket");
        }

        const incidentData = await incidentRes.json();
        const incidentId = incidentData.incident_id;

        // Read log contents
        const reader = new FileReader();
        reader.onload = async (event) => {
          try {
            const logsText = event.target?.result as string;
            
            // Run RCA analysis
            const rcaRes = await fetch(`${backendUrl}/api/v1/it/incidents/${incidentId}/rca`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ logs: logsText })
            });

            if (!rcaRes.ok) {
              throw new Error("Failed to execute log diagnostics on server");
            }

            const rcaData = await rcaRes.json();

            const responseText = `⚙️ **Root Cause Analysis (RCA)**
Incident: **${incidentId}**
Service: **Infrastructure Log Analyzer**
Auto-Remediated: **${rcaData.auto_remediated ? 'Yes (Fixed)' : 'No (Escalated to engineer)'}**
Matched Known Issue: **${rcaData.matched_known_issue || 'None Matched'}**

**Technical Root Cause:**
${rcaData.root_cause}

**Recommended Action Steps:**
${rcaData.recommended_fix}`;

            const agentMessage: Message = {
              id: 'agt_' + Date.now(),
              sender: 'agent',
              text: responseText,
              agentType: 'it',
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, agentMessage]);
          } catch (err: any) {
            setErrorMsg(err.message || 'Log analysis failed.');
          } finally {
            setIsLoading(false);
          }
        };
        reader.readAsText(file);
        return;

      } else {
        // Fallback for sales/executive
        const reader = new FileReader();
        reader.onload = async (event) => {
          try {
            const fileContent = event.target?.result as string;
            
            const response = await fetch(`${backendUrl}/api/v1/chat`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                message: `Analyzing file content for ${file.name}:\n\n${fileContent.slice(0, 4000)}`,
                agent: agentType,
              }),
            });

            if (!response.ok) throw new Error("Failed file query processing");

            const data = await response.json();
            const agentMessage: Message = {
              id: 'agt_' + Date.now(),
              sender: 'agent',
              text: data.answer || "No response received.",
              agentType: agentType,
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, agentMessage]);
          } catch (err: any) {
            setErrorMsg(err.message || 'Generic file upload failed.');
          } finally {
            setIsLoading(false);
          }
        };
        reader.readAsText(file);
        return;
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Attachment upload failed.');
    } finally {
      if (agentType === 'hr') {
        setIsLoading(false);
      }
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userQuery = inputValue;
    setInputValue('');
    setErrorMsg('');
    
    const userMessage: Message = {
      id: 'usr_' + Date.now(),
      sender: 'user',
      text: userQuery,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const historyPayload = messages.map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text
      }));

      const response = await fetch(`${backendUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userQuery,
          agent: agentType,
          history: historyPayload
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned error status ${response.status}`);
      }

      const data = await response.json();
      
      const agentMessage: Message = {
        id: 'agt_' + Date.now(),
        sender: 'agent',
        text: data.answer || "No response received.",
        agentType: agentType,
        processingTime: data.processing_time,
        confidenceScore: data.confidence_score,
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, agentMessage]);
      
      // Re-fetch metrics if Executive Agent is selected in case database states changed
      if (agentType === 'executive') {
        fetchKpis();
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Network error communicating with the agent.');
    } finally {
      setIsLoading(false);
    }
  };

  const agentAccent = {
    hr: 'var(--color-hr)',
    it: 'var(--color-it)',
    sales: 'var(--color-sales)',
    executive: 'var(--color-exec)',
  }[agentType];

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      
      {/* Chat Window Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-glass)',
          background: 'rgba(0,0,0,0.1)',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.1rem', fontWeight: 600, textTransform: 'capitalize', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: agentAccent }}>●</span> {agentType} Service Console
          </h1>
        </div>
        
        {agentType === 'executive' && (
          <button 
            onClick={fetchKpis} 
            disabled={loadingKpis}
            style={{ 
              background: 'none', 
              border: 'none', 
              color: 'var(--text-secondary)', 
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.8rem'
            }}
          >
            <RefreshCw size={14} className={loadingKpis ? 'animate-spin' : ''} />
            Sync Metrics
          </button>
        )}
      </div>

      {/* KPI metrics layout for Executive Agent */}
      {agentType === 'executive' && kpis && (
        <div 
          style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(3, 1fr)', 
            gap: '12px', 
            padding: '16px 20px', 
            background: 'rgba(255,255,255,0.01)',
            borderBottom: '1px solid var(--border-glass)' 
          }}
        >
          {/* HR KPI */}
          <div style={{ background: 'rgba(255,51,119,0.05)', border: '1px solid rgba(255,51,119,0.15)', borderRadius: '10px', padding: '10px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-hr)', fontWeight: 600 }}>HR DEPARTMENT</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '6px' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>{kpis.hr.open_positions}</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Job Reqs</span>
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Shortlist Rate: {((kpis.hr.shortlist_rate || 0) * 100).toFixed(0)}%
            </div>
          </div>
          
          {/* IT KPI */}
          <div style={{ background: 'rgba(0,221,255,0.05)', border: '1px solid rgba(0,221,255,0.15)', borderRadius: '10px', padding: '10px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-it)', fontWeight: 600 }}>IT DEPT (MTTR)</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '6px' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>{kpis.it.avg_mttr_minutes}m</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Avg MTTR</span>
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Auto Remed: {((kpis.it.auto_remediation_rate || 0) * 100).toFixed(0)}%
            </div>
          </div>

          {/* Sales KPI */}
          <div style={{ background: 'rgba(0,255,136,0.05)', border: '1px solid rgba(0,255,136,0.15)', borderRadius: '10px', padding: '10px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-sales)', fontWeight: 600 }}>SALES PIPELINE</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '6px' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>${(kpis.sales.pipeline_value || 0).toLocaleString()}</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Val</span>
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Win Rate Benchmark: {((kpis.sales.win_rate || 0.31) * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      )}

      {/* Chat Messages Log */}
      <div style={{ flexGrow: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isLoading && <TypingIndicator agentType={agentType} />}
        {errorMsg && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'rgba(255, 51, 51, 0.1)',
              border: '1px solid rgba(255, 51, 51, 0.3)',
              borderRadius: '8px',
              padding: '12px',
              color: '#ff8888',
              fontSize: '0.85rem',
              marginBottom: '16px',
            }}
          >
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input Bar */}
      <form
        onSubmit={handleSend}
        style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border-glass)',
          background: 'rgba(0,0,0,0.15)',
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
        }}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          style={{ display: 'none' }}
          accept={agentType === 'hr' ? '.pdf,.txt,.doc,.docx' : agentType === 'it' ? '.log,.txt' : '*'}
        />
        <button
          type="button"
          onClick={handleAttachmentClick}
          disabled={isLoading}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-glass)',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'var(--transition-smooth)',
            outline: 'none',
          }}
        >
          <Paperclip size={18} />
        </button>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={isLoading}
          placeholder={`Type message to ${agentType} agent...`}
          style={{
            flexGrow: 1,
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-glass)',
            borderRadius: '12px',
            padding: '14px 18px',
            color: 'var(--text-primary)',
            fontSize: '0.925rem',
            outline: 'none',
            transition: 'var(--transition-smooth)',
          }}
          onFocus={(e) => (e.target.style.border = `1px solid ${agentAccent}`)}
          onBlur={(e) => (e.target.style.border = '1px solid var(--border-glass)')}
        />
        <button
          type="submit"
          disabled={isLoading || !inputValue.trim()}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: inputValue.trim() ? agentAccent : 'rgba(255,255,255,0.05)',
            color: inputValue.trim() ? '#000' : 'var(--text-secondary)',
            border: 'none',
            cursor: inputValue.trim() ? 'pointer' : 'default',
            transition: 'var(--transition-smooth)',
            outline: 'none',
          }}
        >
          <Send size={18} />
        </button>
      </form>
      
    </div>
  );
};
