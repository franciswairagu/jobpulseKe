import React, { useState } from "react";
import { ArrowRight, Loader2, Mail, Lock, User, ArrowLeft } from "lucide-react";
import { COLORS, FONTS } from "../lib/theme";
import { loginUser, registerUser } from "../api/client";
import { useAuthActions } from "../state/AuthContext";

function PulseLine() {
  return (
    <svg viewBox="0 0 600 120" className="absolute inset-0 w-full h-full opacity-[0.07]" preserveAspectRatio="none">
      <polyline
        points="0,60 80,60 100,20 140,100 180,60 300,60 340,30 380,90 420,60 600,60"
        fill="none"
        stroke="white"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function AuthPage({ initialMode = "login", onBack }) {
  const [mode, setMode] = useState(initialMode);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login, setUser, setStartupId } = useAuthActions();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      let tokens;
      if (mode === "register") {
        tokens = await registerUser({ name, email, password });
      } else {
        tokens = await loginUser({ email, password });
      }
      login({ token: tokens.access_token, refreshToken: tokens.refresh_token });
      try {
        const API_BASE = import.meta.env.VITE_API_BASE || "";
        const me = await fetch(`${API_BASE}/api/auth/me`, {
          headers: { Authorization: `Bearer ${tokens.access_token}` },
        }).then((r) => r.json());
        setUser(me);
      } catch {}
      // Store the server's startup ID so we can detect restarts later
      try {
        const API_BASE = import.meta.env.VITE_API_BASE || "";
        const res = await fetch(`${API_BASE}/api/startup-id`).then((r) => r.json());
        if (res.startup_id) setStartupId(res.startup_id);
      } catch {}
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="relative flex min-h-screen items-center justify-center overflow-hidden px-4"
      style={{ fontFamily: FONTS.body }}
    >
      {/* Animated background */}
      <div className="absolute inset-0 animated-gradient" />
      <div className="absolute inset-0 opacity-30">
        <PulseLine />
      </div>

      {/* Floating orbs */}
      <div className="absolute top-20 left-20 h-72 w-72 rounded-full bg-blue-500/10 blur-3xl animate-float" />
      <div className="absolute bottom-20 right-20 h-96 w-96 rounded-full bg-emerald-500/10 blur-3xl animate-float" style={{ animationDelay: "1s" }} />
      <div className="absolute top-1/2 left-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/5 blur-3xl animate-pulse-soft" />

      {/* Auth card */}
      <div className="relative z-10 w-full max-w-md animate-fade-in-up">
        {/* Back button */}
        {onBack && (
          <button
            onClick={onBack}
            className="mb-6 flex items-center gap-2 text-sm text-white/50 transition-colors hover:text-white/80"
          >
            <ArrowLeft size={16} />
            Back to home
          </button>
        )}

        {/* Logo */}
        <div className="mb-8 text-center">
          <div
            className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl"
            style={{
              background: "linear-gradient(135deg, #FA510F, #E04500)",
              boxShadow: "0 8px 24px rgba(250,81,15,0.35)",
            }}
          >
            <svg width="24" height="24" viewBox="0 0 18 18" fill="none">
              <polyline
                points="1,9 5,9 7,3 10,15 12,9 17,9"
                stroke="white"
                strokeWidth="2.2"
                strokeLinejoin="round"
                strokeLinecap="round"
                fill="none"
              />
            </svg>
          </div>
          <h1
            className="text-3xl font-bold text-white"
            style={{ fontFamily: FONTS.display }}
          >
            Welcome to JobPulse
          </h1>
          <p className="mt-2 text-sm text-white/60">
            {mode === "login"
              ? "Sign in to access your career intelligence"
              : "Create your account to get started"}
          </p>
        </div>

        {/* Form card */}
        <div
          className="glass-strong rounded-3xl p-8"
          style={{
            boxShadow: "0 25px 60px rgba(0,0,0,0.3)",
          }}
        >
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            {mode === "register" && (
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.textSecondary }}>
                  Full name
                </label>
                <div className="relative">
                  <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full rounded-xl border border-border bg-white py-3 pl-10 pr-4 text-sm outline-none transition-all duration-200 focus:border-accent focus:shadow-glow-blue"
                    style={{ color: COLORS.textDark }}
                    placeholder="Jane Doe"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.textSecondary }}>
                Email address
              </label>
              <div className="relative">
                <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-border bg-white py-3 pl-10 pr-4 text-sm outline-none transition-all duration-200 focus:border-accent focus:shadow-glow-blue"
                  style={{ color: COLORS.textDark }}
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.textSecondary }}>
                Password
              </label>
              <div className="relative">
                <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
                <input
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-border bg-white py-3 pl-10 pr-4 text-sm outline-none transition-all duration-200 focus:border-accent focus:shadow-glow-blue"
                  style={{ color: COLORS.textDark }}
                  placeholder="Minimum 8 characters"
                />
              </div>
            </div>

            {error && (
              <div
                className="flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium animate-fade-in"
                style={{ background: "rgba(239,68,68,0.08)", color: COLORS.error }}
              >
                <AlertTriangle size={14} />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="group flex w-full items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-semibold text-white transition-all duration-300 hover:shadow-glow-blue hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100"
              style={{
                background: "linear-gradient(135deg, #FA510F, #E04500)",
                boxShadow: "0 4px 14px rgba(250,81,15,0.3)",
              }}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Please wait...
                </>
              ) : (
                <>
                  {mode === "login" ? "Sign in" : "Create account"}
                  <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
                </>
              )}
            </button>

            <div className="relative my-2">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t" style={{ borderColor: COLORS.border }} />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-white px-3" style={{ color: COLORS.textMuted }}>
                  {mode === "login" ? "New here?" : "Already have an account?"}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setError(null);
              }}
              className="w-full rounded-xl border border-border py-3 text-sm font-semibold transition-all duration-200 hover:border-accent/30 hover:bg-surface-tertiary"
              style={{ color: COLORS.accent }}
            >
              {mode === "login" ? "Create an account" : "Sign in instead"}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-white/40">
          African Tech Career Intelligence Platform
        </p>
      </div>
    </div>
  );
}

function AlertTriangle({ size, className }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </svg>
  );
}
