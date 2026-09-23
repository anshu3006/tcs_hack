import { useState, useRef, useEffect } from 'react';
import { askApi } from '../api';

export default function AskApiChat({ code, language }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "👋 Hi! I'm your API assistant. Ask me anything about your API — like \"How do I create a user?\" or \"What parameters does the posts endpoint need?\""
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesRef = useRef(null);

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: question }]);
    setLoading(true);

    try {
      const result = await askApi(question, code, language);

      let response = result.answer || 'No answer found.';

      // Add relevant endpoints
      if (result.relevant_endpoints?.length > 0) {
        response += '\n\n**Relevant Endpoints:**';
        result.relevant_endpoints.forEach(ep => {
          response += `\n• \`${ep.method} ${ep.path}\``;
          if (ep.why) response += ` — ${ep.why}`;
        });
      }

      // Add example request
      if (result.example_request) {
        const ex = result.example_request;
        response += `\n\n**Example:**\n\`\`\`bash\ncurl -X ${ex.method} ${ex.url}`;
        if (ex.body) {
          response += ` \\\n  -H "Content-Type: application/json" \\\n  -d '${JSON.stringify(ex.body)}'`;
        }
        response += '\n```';
      }

      setMessages(prev => [...prev, { role: 'assistant', content: response }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${err.message}. Make sure the backend is running.`
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="ask-api">
      <div className="ask-messages" ref={messagesRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`ask-message ${msg.role}`}>
            {msg.content.split('\n').map((line, j) => {
              if (line.startsWith('```')) return null;
              if (line.startsWith('**')) {
                return <div key={j} style={{fontWeight:600,marginTop:'8px',color: msg.role === 'user' ? 'white' : 'var(--text-primary)'}}>{line.replace(/\*\*/g, '')}</div>;
              }
              if (line.startsWith('•') || line.startsWith('- ')) {
                return <div key={j} style={{paddingLeft:'12px',fontSize:'0.8125rem'}}>{line}</div>;
              }
              return <div key={j}>{line || <br />}</div>;
            })}
          </div>
        ))}
        {loading && (
          <div className="ask-message assistant">
            <div className="loading" style={{padding:'4px 0',justifyContent:'flex-start'}}>
              <span className="spinner"></span> Thinking...
            </div>
          </div>
        )}
      </div>

      <div className="ask-input-area">
        <input
          className="ask-input"
          type="text"
          placeholder="Ask about your API... (e.g., 'How do I create a user?')"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="btn btn-primary btn-sm"
          onClick={handleSend}
          disabled={loading || !input.trim()}
          style={{borderRadius:'var(--radius-xl)'}}
        >
          ↑
        </button>
      </div>
    </div>
  );
}
