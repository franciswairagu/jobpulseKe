import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, ExternalLink, Loader2, AlertTriangle } from "lucide-react";
import { COLORS, FONTS } from "../lib/theme";
import { askRAG } from "../api/client";

const SUGGESTIONS = [
  "What remote Python jobs are available in Kenya?",
  "Which companies are hiring data scientists in Nigeria?",
  "What skills do I need for cloud engineering roles?",
  "Show me entry-level tech jobs in South Africa",
];

function SourceCard({ source }) {
  return (
    <div className="rounded-lg border p-3" style={{ borderColor: COLORS.border, background: "#FBFCFE" }}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold" style={{ color: COLORS.textDark }}>{source.title}</p>
          <p className="text-xs" style={{ color: COLORS.textSecondary }}>{source.company}</p>
        </div>
        {source.url && source.url !== "N/A" && (
          <a href={source.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="shrink-0">
            <ExternalLink size={13} style={{ color: COLORS.deepBlue }} />
          </a>
        )}
      </div>
      <div className="mt-1.5 flex items-center gap-2">
        <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ background: COLORS.lightBlue, color: COLORS.deepBlue }}>
          {(source.score * 100).toFixed(0)}% match
        </span>
      </div>
    </div>
  );
}

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full" style={{ background: COLORS.navy }}>
          <Bot size={15} color="#fff" />
        </div>
      )}
      <div className={`flex max-w-[80%] flex-col gap-2`}>
        <div
          className="rounded-2xl px-4 py-3 text-sm leading-relaxed"
          style={{
            background: isUser ? COLORS.navy : "#fff",
            color: isUser ? "#fff" : COLORS.textDark,
            border: isUser ? "none" : `1px solid ${COLORS.border}`,
            whiteSpace: "pre-wrap",
          }}
        >
          {msg.text}
        </div>
        {msg.sources && msg.sources.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-[11px] font-medium" style={{ color: COLORS.textSecondary }}>Sources from JobPulse dataset:</p>
            {msg.sources.map((s, i) => <SourceCard key={i} source={s} />)}
          </div>
        )}
        {msg.confidence && msg.confidence !== "grounded" && (
          <p className="flex items-center gap-1 text-[11px]" style={{ color: COLORS.warning }}>
            <AlertTriangle size={11} /> Weak match — try a more specific question
          </p>
        )}
      </div>
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full" style={{ background: COLORS.deepBlue }}>
          <User size={15} color="#fff" />
        </div>
      )}
    </div>
  );
}

export default function AssistantPage() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! I'm the JobPulse assistant. I can help you find jobs, understand skill demands, and explore the African tech market. Ask me anything about the indexed job postings.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (question) => {
    const q = question || input.trim();
    if (!q || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setLoading(true);

    try {
      const res = await askRAG(q);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: res.answer, sources: res.sources, confidence: res.confidence },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Sorry, something went wrong: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-120px)] flex-col">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold sm:text-[28px]" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>AI Assistant</h1>
        <p className="mt-1.5 text-sm" style={{ color: COLORS.textSecondary }}>
          Ask questions about the African tech job market — answers are grounded in real JobPulse data.
        </p>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto rounded-2xl border p-4 sm:p-5" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <div className="flex flex-col gap-5">
          {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
          {loading && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full" style={{ background: COLORS.navy }}>
                <Bot size={15} color="#fff" />
              </div>
              <div className="flex items-center gap-2 rounded-2xl px-4 py-3" style={{ background: "#fff", border: `1px solid ${COLORS.border}` }}>
                <Loader2 size={15} className="animate-spin" style={{ color: COLORS.deepBlue }} />
                <span className="text-sm" style={{ color: COLORS.textSecondary }}>Searching job postings...</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors hover:bg-gray-50"
              style={{ borderColor: COLORS.border, color: COLORS.textDark }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <div className="mt-3 flex items-center gap-2 rounded-xl border px-4 py-2.5" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask about jobs, skills, salaries, companies..."
          className="flex-1 bg-transparent text-sm outline-none"
          style={{ color: COLORS.textDark }}
          disabled={loading}
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || loading}
          className="flex h-9 w-9 items-center justify-center rounded-lg transition-opacity"
          style={{ background: input.trim() ? COLORS.navy : "#CBD5E1", cursor: input.trim() ? "pointer" : "not-allowed" }}
        >
          <Send size={15} color="#fff" />
        </button>
      </div>
    </div>
  );
}
