import React, { useState, useRef, useEffect } from "react";
import { Bot, Send, X, Sparkles, ExternalLink, Loader2, Minus, AlertTriangle, User } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";
import { askRAG } from "../../api/client";

const SUGGESTIONS = [
  "What remote Python jobs are available in Kenya?",
  "Which companies are hiring data scientists in Nigeria?",
  "What skills do I need for cloud engineering roles?",
  "Show me entry-level tech jobs in South Africa",
];

function SourceCard({ source }) {
  return (
    <div
      className="rounded-lg border p-2.5"
      style={{ borderColor: COLORS.border, background: "#FBFCFE" }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold" style={{ color: COLORS.textDark }}>
            {source.title}
          </p>
          <p className="text-[11px]" style={{ color: COLORS.textSecondary }}>{source.company}</p>
        </div>
        {source.url && source.url !== "N/A" && (
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="shrink-0 rounded p-1 transition-colors hover:bg-gray-100"
          >
            <ExternalLink size={12} style={{ color: COLORS.deepBlue }} />
          </a>
        )}
      </div>
      <div className="mt-1.5">
        <span
          className="rounded-full px-2 py-0.5 text-[10px] font-medium"
          style={{ background: COLORS.lightBlue, color: COLORS.deepBlue }}
        >
          {(source.score * 100).toFixed(0)}% match
        </span>
      </div>
    </div>
  );
}

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-2.5 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
          style={{ background: COLORS.navy }}
        >
          <Bot size={13} color="#fff" />
        </div>
      )}
      <div className="flex max-w-[85%] flex-col gap-1.5">
        <div
          className="rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed"
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
          <div className="flex flex-col gap-1.5">
            <p className="text-[10px] font-medium" style={{ color: COLORS.textSecondary }}>Sources:</p>
            {msg.sources.map((s, i) => <SourceCard key={i} source={s} />)}
          </div>
        )}
        {msg.confidence && msg.confidence !== "grounded" && (
          <p className="flex items-center gap-1 text-[10px]" style={{ color: COLORS.warning }}>
            <AlertTriangle size={10} /> Weak match — try a more specific question
          </p>
        )}
      </div>
      {isUser && (
        <div
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
          style={{ background: COLORS.deepBlue }}
        >
          <User size={13} color="#fff" />
        </div>
      )}
    </div>
  );
}

export default function AiAssistantWidget() {
  const [open, setOpen] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! I'm the JobPulse AI assistant. I can help you find jobs, understand skill demands, and explore the African tech market. Ask me anything!",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [unread, setUnread] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open && !minimized) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, open, minimized]);

  useEffect(() => {
    if (open && !minimized) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [open, minimized]);

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
      if (!open || minimized) setUnread(true);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Sorry, something went wrong: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleOpen = () => {
    setOpen((prev) => !prev);
    setMinimized(false);
    if (!open) setUnread(false);
  };

  return (
    <>
      {/* Floating button */}
      <button
        onClick={toggleOpen}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full transition-all duration-300 hover:scale-110 hover:shadow-xl group"
        style={{
          background: open
            ? "linear-gradient(135deg, #374151, #1F2937)"
            : "linear-gradient(135deg, #FA510F, #E04500)",
          boxShadow: open
            ? "0 4px 20px rgba(0,0,0,0.25)"
            : "0 4px 20px rgba(250,81,15,0.4)",
        }}
        aria-label={open ? "Close AI assistant" : "Open AI assistant"}
      >
        {open ? (
          <X size={22} color="#fff" strokeWidth={2} />
        ) : (
          <Sparkles size={22} color="#fff" strokeWidth={2} />
        )}
        {unread && !open && (
          <span
            className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-bold text-white"
            style={{
              background: "linear-gradient(135deg, #DC2626, #B91C1C)",
              boxShadow: "0 0 8px rgba(220,38,38,0.5)",
            }}
          >
            1
          </span>
        )}
      </button>

      {/* Chat drawer */}
      {open && (
        <div
          className="fixed bottom-24 right-6 z-50 flex flex-col overflow-hidden rounded-2xl border animate-slide-up"
          style={{
            width: "min(400px, calc(100vw - 48px))",
            height: "min(560px, calc(100vh - 140px))",
            borderColor: COLORS.border,
            background: "#fff",
            boxShadow: "0 20px 60px rgba(16,31,60,0.2), 0 0 0 1px rgba(16,31,60,0.05)",
            animationDuration: "0.3s",
          }}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between px-4 py-3"
            style={{ background: COLORS.navy }}
          >
            <div className="flex items-center gap-2.5">
              <div
                className="flex h-8 w-8 items-center justify-center rounded-lg"
                style={{ background: "rgba(255,255,255,0.1)" }}
              >
                <Bot size={16} color="#fff" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white" style={{ fontFamily: FONTS.display }}>
                  JobPulse AI
                </p>
                <p className="text-[10px] text-white/60">Ask about jobs, skills & more</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setMinimized((m) => !m)}
                className="rounded-lg p-1.5 text-white/60 transition-colors hover:bg-white/10 hover:text-white"
                title={minimized ? "Expand" : "Minimize"}
              >
                <Minus size={16} />
              </button>
              <button
                onClick={toggleOpen}
                className="rounded-lg p-1.5 text-white/60 transition-colors hover:bg-white/10 hover:text-white"
                title="Close"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Body */}
          {!minimized && (
            <>
              {/* Messages */}
              <div
                className="flex-1 overflow-y-auto px-4 py-4"
                style={{ background: COLORS.pageBg }}
              >
                <div className="flex flex-col gap-4">
                  {messages.map((msg, i) => (
                    <MessageBubble key={i} msg={msg} />
                  ))}
                  {loading && (
                    <div className="flex gap-2.5">
                      <div
                        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
                        style={{ background: COLORS.navy }}
                      >
                        <Bot size={13} color="#fff" />
                      </div>
                      <div
                        className="flex items-center gap-2 rounded-2xl px-3.5 py-2.5"
                        style={{ background: "#fff", border: `1px solid ${COLORS.border}` }}
                      >
                        <Loader2 size={14} className="animate-spin" style={{ color: COLORS.deepBlue }} />
                        <span className="text-sm" style={{ color: COLORS.textSecondary }}>Searching...</span>
                      </div>
                    </div>
                  )}
                  <div ref={bottomRef} />
                </div>
              </div>

              {/* Suggestions */}
              {messages.length <= 1 && (
                <div className="flex flex-wrap gap-1.5 border-t px-4 py-2.5" style={{ borderColor: COLORS.border }}>
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="rounded-full border px-3 py-1.5 text-[11px] font-medium transition-colors hover:bg-gray-50"
                      style={{ borderColor: COLORS.border, color: COLORS.textDark }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}

              {/* Input */}
              <div
                className="flex items-center gap-2 border-t px-3 py-3"
                style={{ borderColor: COLORS.border, background: "#fff" }}
              >
                <input
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
                  placeholder="Ask about jobs, skills..."
                  className="flex-1 bg-transparent text-sm outline-none placeholder:text-gray-400"
                  style={{ color: COLORS.textDark }}
                  disabled={loading}
                />
                <button
                  onClick={() => send()}
                  disabled={!input.trim() || loading}
                  className="flex h-9 w-9 items-center justify-center rounded-lg transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed hover:scale-105"
                  style={{
                    background: input.trim() ? COLORS.navy : "#CBD5E1",
                  }}
                >
                  <Send size={15} color="#fff" />
                </button>
              </div>
            </>
          )}
        </div>
      )}

      <style>{`
        @keyframes slide-up {
          from { opacity: 0; transform: translateY(16px) scale(0.96); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
      `}</style>
    </>
  );
}
