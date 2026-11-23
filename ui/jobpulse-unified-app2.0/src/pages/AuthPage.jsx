import React, { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Loader2, ShieldCheck } from "lucide-react";
import { COLORS, FONTS } from "../lib/theme";
import { fetchMe, getAuthConfig, loginWithGoogle } from "../api/client";
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
  const isSignup = initialMode === "register";
  const buttonRef = useRef(null);
  const [googleClientId, setGoogleClientId] = useState("");
  const [configError, setConfigError] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login, setUser } = useAuthActions();

  const handleGoogleCredential = useCallback(async (credential) => {
    setError(null);
    setLoading(true);
    try {
      const tokens = await loginWithGoogle(credential);
      if (!tokens || !tokens.access_token) {
        throw new Error("Google sign-in failed. Please try again.");
      }
      const payload = {
        token: tokens.access_token,
        refreshToken: tokens.refresh_token,
      };
      localStorage.setItem("jobpulse_auth", JSON.stringify(payload));
      login(payload);
      const me = await fetchMe();
      setUser(me);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [login, setUser]);

  useEffect(() => {
    let active = true;
    getAuthConfig()
      .then(({ google_client_id: clientId }) => {
        if (!active) return;
        if (!clientId) {
          setConfigError("Google sign-in isn't configured. Set GOOGLE_CLIENT_ID in the backend environment and restart the API.");
          return;
        }
        setGoogleClientId(clientId);
      })
      .catch((err) => {
        if (active) setConfigError(err.message);
      });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!googleClientId || !buttonRef.current) return undefined;
    let cancelled = false;
    const handleScriptError = () => setConfigError("Could not load Google sign-in. Check your connection and try again.");
    const renderGoogleButton = () => {
      if (cancelled || !window.google?.accounts?.id || !buttonRef.current) return;
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: ({ credential }) => handleGoogleCredential(credential),
      });
      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: "outline",
        size: "large",
        shape: "rectangular",
        text: "continue_with",
        width: 320,
      });
    };

    let script = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
    if (!script) {
      script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }
    script.addEventListener("load", renderGoogleButton);
    script.addEventListener("error", handleScriptError);
    renderGoogleButton();
    return () => {
      cancelled = true;
      script.removeEventListener("load", renderGoogleButton);
      script.removeEventListener("error", handleScriptError);
    };
  }, [googleClientId, handleGoogleCredential]);

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
            {isSignup
              ? "Create your account with your verified Google account"
              : "Sign in to access your career intelligence"}
          </p>
        </div>

        {/* Form card */}
        <div
          className="glass-strong rounded-3xl p-8"
          style={{
            boxShadow: "0 25px 60px rgba(0,0,0,0.3)",
          }}
        >
          <div className="flex flex-col items-center gap-5">
            {error && (
              <div
                role="alert"
                className="flex w-full items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium animate-fade-in"
                style={{ background: "rgba(239,68,68,0.08)", color: COLORS.error }}
              >
                <AlertTriangle size={14} />
                {error}
              </div>
            )}
            {configError && (
              <div
                role="alert"
                className="w-full rounded-xl px-4 py-3 text-sm"
                style={{ background: "rgba(239,68,68,0.08)", color: COLORS.error }}
              >
                {configError}
              </div>
            )}
            <div
              ref={buttonRef}
              className={loading ? "pointer-events-none opacity-50" : ""}
              aria-busy={loading}
            />
            {loading && (
              <div className="flex items-center gap-2 text-sm" style={{ color: COLORS.textSecondary }}>
                <Loader2 size={16} className="animate-spin" />
                Verifying your Google account...
              </div>
            )}
            {!configError && !googleClientId && (
              <div className="flex items-center gap-2 text-sm" style={{ color: COLORS.textSecondary }}>
                <Loader2 size={16} className="animate-spin" />
                Loading secure sign-in...
              </div>
            )}
            <div className="flex items-start gap-2 text-xs leading-relaxed" style={{ color: COLORS.textMuted }}>
              <ShieldCheck size={15} className="mt-0.5 shrink-0" />
              <span>Google verifies your email. Your CV and profile are private to your account.</span>
            </div>
            <p className="text-center text-xs" style={{ color: COLORS.textMuted }}>
              {isSignup
                ? "A JobPulse account will be created automatically the first time you continue."
                : "New to JobPulse? Continue with Google to create your account."}
            </p>
          </div>
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
