import React, { useState } from "react";
import { COLORS, FONTS } from "../lib/theme";
import { loginUser, registerUser } from "../api/client";
import { useAuthActions } from "../state/AuthContext";

export default function AuthPage() {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login, setUser } = useAuthActions();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        const tokens = await registerUser({ name, email, password });
        login({ token: tokens.access_token, refreshToken: tokens.refresh_token });
      } else {
        const tokens = await loginUser({ email, password });
        login({ token: tokens.access_token, refreshToken: tokens.refresh_token });
      }
      // Fetch user profile
      try {
        const me = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${localStorage.getItem("jobpulse_auth") ? JSON.parse(localStorage.getItem("jobpulse_auth")).token : ""}` },
        }).then((r) => r.json());
        setUser(me);
      } catch {}
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4" style={{ background: COLORS.pageBg, fontFamily: FONTS.body }}>
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl" style={{ background: COLORS.navy }}>
            <svg width="22" height="22" viewBox="0 0 18 18" fill="none">
              <polyline points="1,9 5,9 7,3 10,15 12,9 17,9" stroke={COLORS.lightBlue} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" fill="none" />
            </svg>
          </div>
          <h1 className="text-2xl font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Welcome to JobPulse</h1>
          <p className="mt-1.5 text-sm" style={{ color: COLORS.textSecondary }}>
            {mode === "login" ? "Sign in to your account" : "Create your account"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 rounded-2xl border p-6" style={{ borderColor: COLORS.border, background: "#fff" }}>
          {mode === "register" && (
            <div>
              <label className="mb-1 block text-xs font-medium" style={{ color: COLORS.textSecondary }}>Full name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-lg border px-3.5 py-2.5 text-sm outline-none"
                style={{ borderColor: COLORS.border, color: COLORS.textDark }}
                placeholder="Jane Doe"
              />
            </div>
          )}
          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: COLORS.textSecondary }}>Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border px-3.5 py-2.5 text-sm outline-none"
              style={{ borderColor: COLORS.border, color: COLORS.textDark }}
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: COLORS.textSecondary }}>Password</label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border px-3.5 py-2.5 text-sm outline-none"
              style={{ borderColor: COLORS.border, color: COLORS.textDark }}
              placeholder="Minimum 6 characters"
            />
          </div>

          {error && (
            <p className="rounded-lg px-3 py-2 text-xs font-medium" style={{ background: "rgba(220,38,38,0.08)", color: COLORS.error }}>
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg py-2.5 text-sm font-semibold text-white transition-opacity"
            style={{ background: COLORS.navy, opacity: loading ? 0.7 : 1, cursor: loading ? "not-allowed" : "pointer" }}
          >
            {loading ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}
          </button>

          <p className="text-center text-xs" style={{ color: COLORS.textSecondary }}>
            {mode === "login" ? "Don't have an account? " : "Already have an account? "}
            <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }} className="font-semibold" style={{ color: COLORS.deepBlue }}>
              {mode === "login" ? "Sign up" : "Sign in"}
            </button>
          </p>
        </form>
      </div>
    </div>
  );
}
