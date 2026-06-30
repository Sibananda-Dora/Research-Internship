import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Cpu, User } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000';

const SUGGESTIONS = [
  "What is the crop failure risk in Balasore?",
  "Simulate 40% less rainfall during weeks 5-8",
  "Explain why Koraput has stress anomalies",
  "What are the biophysical thresholds for rice?"
];

export default function DSSChat({ district, year, season, onRunSimulation }) {
  const [messages, setMessages] = useState([
    { 
      id: 'welcome', 
      sender: 'assistant', 
      text: `Hello! I am the CDT Expert Advisory Agent. Select a district on the map, adjust weather variables on the timeline, or ask me questions about yield predictions, biophysical anomalies, and what-if simulations for the active season.`
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim()) return;

    // Add user message to state
    const userMsg = { id: Date.now().toString(), sender: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text })
      });

      if (!res.ok) throw new Error(`Backend returned ${res.status}`);

      const data = await res.json();
      const reply = data.advisory || "No advisory returned.";

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: reply
      }]);

      // Trigger simulation if LLM detected a what-if intent
      const lowerText = text.toLowerCase();
      if (onRunSimulation && (lowerText.includes("simulate") || lowerText.includes("less") || lowerText.includes("more"))) {
        onRunSimulation({
          precip: lowerText.includes("less") ? 0.6 : 1.4,
          weeks: [4, 5, 6, 7]
        });
      }
    } catch (e) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: `I encountered an error connecting to the advisory server (${e.message}). Please check that the FastAPI backend is running on ${API_BASE_URL}.`
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    handleSendMessage();
  };

  return (
    <div className="glass-card chat-card">
      <div className="card-header" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '8px' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }} className="text-cyan">
          <MessageSquare size={18} />
          Cognitive Advisory Node
        </h2>
      </div>

      <div className="chat-messages">
        {messages.map((m) => (
          <div key={m.id} className={`chat-message ${m.sender}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px', fontSize: '0.75rem', fontWeight: 600, color: m.sender === 'user' ? '#000' : 'var(--accent-cyan)' }}>
              {m.sender === 'user' ? <User size={12} /> : <Cpu size={12} />}
              {m.sender === 'user' ? 'User' : 'CDT Advisor'}
            </div>
            <div style={{ whiteSpace: 'pre-line' }}>{m.text}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-message assistant skeleton" style={{ width: '40%', height: '40px' }}></div>
        )}
        <div ref={chatEndRef} />
      </div>

      {messages.length === 1 && (
        <div style={{ marginBottom: '10px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>SUGGESTED QUERIES</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {SUGGESTIONS.map((s, idx) => (
              <button 
                key={idx}
                onClick={() => handleSendMessage(s)}
                style={{ 
                  background: 'rgba(255,255,255,0.03)', 
                  border: '1px solid var(--border-color)', 
                  color: 'var(--text-secondary)',
                  padding: '6px 10px',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                  e.currentTarget.style.color = '#fff';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-color)';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleFormSubmit} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Query yields for ${district}...`}
          className="chat-input"
        />
        <button type="submit" className="send-btn" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
