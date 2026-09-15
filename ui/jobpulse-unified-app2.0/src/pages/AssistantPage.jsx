import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, ExternalLink, Loader2, Sparkles } from "lucide-react";
import { COLORS, FONTS } from "../lib/theme";
import { askRAGStream } from "../api/client";

const SUGGESTIONS = [
  "What remote Python jobs are available in Kenya?",
  "Which companies are hiring data scientists in Nigeria?",
  "What skills do I need for cloud engineering roles?",
  "Show me entry-level tech jobs in South Africa",
];

function SourceCard({ source }) {
  return (
    <div
      className="rounded-xl border p-3 transition-all hover:shadow-sm"
      style={{ borderColor: COLORS.borderLight, background: "#FAFBFC" }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold" style={{ color: COLORS.textDark }}>
            {source.title}
          </p>
          <p className="text-xs" style={{ color: COLORS.textSecondary }}>{source.company}</p>
        </div>
        {source.url && source.url !== "N/A" && (
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="shrink-0 rounded-lg p-1.5 transition-colors hover:bg-surface-tertiary"
          >
            <ExternalLink size={13} style={{ color: COLORS.accent }} />
          </a>
        )}
      </div>
      <div className="mt-2">
        <span
          className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
          style={{ background: COLORS.lightBlue, color: COLORS.accent }}
        >
          {(source.score * 100).toFixed(0)}% match
        </span>
      </div>
    </div>
  );
}

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  const isStreaming = msg.streaming && !msg.text;
  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}>
      {!isUser && (
        <div
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
          style={{
            background: "linear-gradient(135deg, #FA510F, #E04500)",
            boxShadow: "0 2px 8px rgba(250,81,15,0.25)",
          }}
        >
          <Bot size={16} color="#fff" />
        </div>
      )}
      <div className="flex max-w-[80%] flex-col gap-2">
        <div
          className="rounded-2xl px-4 py-3 text-sm leading-relaxed"
          style={{
            background: isUser
              ? "linear-gradient(135deg, #FA510F, #E04500)"
              : "#fff",
            color: isUser ? "#fff" : COLORS.textDark,
            border: isUser ? "none" : `1px solid ${COLORS.border}`,
            boxShadow: isUser
              ? "0 2px 8px rgba(250,81,15,0.2)"
              : "0 2px 8px rgba(16,31,60,0.05)",
            whiteSpace: "pre-wrap",
          }}
        >
          {isStreaming ? (
            <span className="inline-flex items-center gap-1.5">
              <span className="pulse-dot" style={{ background: COLORS.accent }} />
              <span className="text-sm" style={{ color: COLORS.textSecondary }}>thinking...</span>
            </span>
          ) : (
            msg.text
          )}
        </div>
        {!isStreaming && msg.sources && msg.sources.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>
              Sources from JobPulse dataset
            </p>
            {msg.sources.map((s, i) => (
              <SourceCard key={i} source={s} />
            ))}
          </div>
        )}
        {!isStreaming && msg.confidence && msg.confidence !== "grounded" && (
          <p className="flex items-center gap-1 text-[11px] font-medium" style={{ color: COLORS.warning }}>
            <span className="pulse-dot" style={{ background: COLORS.warning }} />
            Weak match — try a more specific question
          </p>
        )}
      </div>
      {isUser && (
        <div
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
          style={{ background: COLORS.surfaceTertiary }}
        >
          <User size={16} style={{ color: COLORS.textSecondary }} />
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
      let text = "";
      let meta = { confidence: "grounded", sources: [], method: "template" };

      // Optimistically add an assistant bubble that we update as tokens arrive
      setMessages((prev) => [...prev, { role: "assistant", text: "", streaming: true }]);

      for await (const event of askRAGStream(q)) {
        if (event.type === "token") {
          text += event.content;
          // Update the last message (our streaming bubble) in place
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = { role: "assistant", text, streaming: true };
            return next;
          });
        } else if (event.type === "done") {
          meta = { confidence: event.confidence, sources: event.sources, method: event.method };
        } else if (event.type === "error") {
          text = `Sorry, something went wrong: ${event.message}`;
        }
      }

      // Finalize the message with sources and remove streaming flag
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          text: text || "No response received.",
          sources: meta.sources,
          confidence: meta.confidence,
          streaming: false,
        };
        return next;
      });
    } catch (err) {
      // If streaming failed entirely, replace the streaming bubble with error
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last?.streaming) {
          next[next.length - 1] = {
            role: "assistant",
            text: `Sorry, something went wrong: ${err.message}`,
            streaming: false,
          };
        } else {
          next.push({ role: "assistant", text: `Sorry, something went wrong: ${err.message}` });
        }
        return next;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-120px)] flex-col">
      <div className="mb-4">
        <h1 className="text-2xl font-bold sm:text-3xl" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
          AI Assistant
        </h1>
        <p className="mt-1.5 text-sm" style={{ color: COLORS.textSecondary }}>
          Ask questions about the African tech job market — answers are grounded in real JobPulse data.
        </p>
      </div>

      {/* Messages area */}
      <div
        className="flex-1 overflow-y-auto rounded-2xl border p-4 sm:p-5"
        style={{ borderColor: COLORS.border, background: "#fff" }}
      >
        <div className="flex flex-col gap-5">
          {messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg} />
          ))}
          {loading && !messages.some((m) => m.streaming) && (
            <div className="flex gap-3 animate-fade-in">
              <div
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
                style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
              >
                <Bot size={16} color="#fff" />
              </div>
              <div
                className="flex items-center gap-2 rounded-2xl px-4 py-3"
                style={{ background: "#fff", border: `1px solid ${COLORS.border}` }}
              >
                <Loader2 size={15} className="animate-spin" style={{ color: COLORS.accent }} />
                <span className="text-sm" style={{ color: COLORS.textSecondary }}>Thinking...</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="mt-3 flex flex-wrap gap-2 animate-fade-in-up">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="group flex items-center gap-1.5 rounded-full border px-4 py-2 text-xs font-medium transition-all duration-200 hover:border-accent/30 hover:bg-accent/5 hover:shadow-sm"
              style={{ borderColor: COLORS.border, color: COLORS.textDark }}
            >
              <Sparkles size={12} className="text-accent/50 group-hover:text-accent" />
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <div
        className="mt-3 flex items-center gap-3 rounded-xl border px-4 py-3 transition-all duration-200 focus-within:border-accent focus-within:shadow-glow-blue"
        style={{ borderColor: COLORS.border, background: "#fff" }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask about jobs, skills, salaries, companies..."
          className="flex-1 bg-transparent text-sm outline-none placeholder:text-textMuted"
          style={{ color: COLORS.textDark }}
          disabled={loading}
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || loading}
          className="flex h-10 w-10 items-center justify-center rounded-xl transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed hover:scale-105"
          style={{
            background: input.trim() ? "linear-gradient(135deg, #FA510F, #E04500)" : COLORS.surfaceTertiary,
            boxShadow: input.trim() ? "0 2px 8px rgba(250,81,15,0.25)" : "none",
          }}
        >
          <Send size={16} color={input.trim() ? "#fff" : COLORS.textMuted} />
        </button>
      </div>
    </div>
  );
}
