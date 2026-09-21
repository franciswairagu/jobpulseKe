import React, { useState, useEffect, useCallback, useRef } from "react";
import AppShell from "./components/layout/AppShell";
import DashboardPage from "./pages/DashboardPage";
import CVAnalyzerPage from "./pages/CVAnalyzerPage";
import MarketSkillsPage from "./pages/MarketSkillsPage";
import CareerInsightsPage from "./pages/CareerInsightsPage";
import AssistantPage from "./pages/AssistantPage";
import AuthPage from "./pages/AuthPage";
import LandingPage from "./pages/LandingPage";
import AboutPage from "./pages/AboutPage";
import AiAssistantWidget from "./components/shared/AiAssistantWidget";
import { useAuth, useAuthActions } from "./state/AuthContext";

const PAGE_META = {
  dashboard: { title: null, subtitle: null },
  "cv-analyzer": { title: "CV Analyzer", subtitle: "Your personal career-to-job matching engine" },
  "skill-demand": { title: "Skill Demand", subtitle: "African tech skills intelligence" },
  "career-insights": { title: "Career Insights", subtitle: "Career progression, skill distribution & opportunities" },
  "ai-assistant": { title: "AI Assistant", subtitle: "Ask questions about the African tech job market" },
  about: { title: "About JobPulse", subtitle: "Empowering Africa's tech workforce" },
};

export default function App() {
  const { token, startupId } = useAuth();
  const { logout, setStartupId } = useAuthActions();
  const [activeKey, setActiveKey] = useState("dashboard");
  const [checkingStartup, setCheckingStartup] = useState(true);
  const [authMode, setAuthMode] = useState("login");
  const [showAuth, setShowAuth] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [serverReady, setServerReady] = useState(false);
  const meta = PAGE_META[activeKey] ?? {};

  const checkStartup = useCallback((retries = 5, delay = 2000) => {
    fetch("/api/startup-id")
      .then((r) => r.json())
      .then((data) => {
        const serverId = data.startup_id;
        if (startupId && startupId !== serverId) {
          logout();
        } else {
          setStartupId(serverId);
        }
        setServerReady(true);
        setCheckingStartup(false);
      })
      .catch(() => {
        if (retries > 0) {
          setTimeout(() => checkStartup(retries - 1, delay * 1.5), delay);
        } else {
          logout();
          setServerReady(true);
          setCheckingStartup(false);
        }
      });
  }, [startupId, logout, setStartupId]);

  const checkStartupRef = useRef(checkStartup);
  checkStartupRef.current = checkStartup;

  useEffect(() => {
    if (!token) {
      setCheckingStartup(false);
      setServerReady(true);
      return;
    }
    setCheckingStartup(true);
    setServerReady(false);
    checkStartupRef.current();
  }, [token]);

  if (checkingStartup) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ background: "#FAFAFA" }}>
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-[#FA510F]" />
          <p className="text-sm text-gray-500">Connecting to server...</p>
        </div>
      </div>
    );
  }

  if (!token && !showAuth) {
    return <LandingPage onNavigateToAuth={(mode) => { setAuthMode(mode); setShowAuth(true); }} />;
  }

  if (!token) {
    return <AuthPage initialMode={authMode} onBack={() => setShowAuth(false)} />;
  }

  const handleSearch = (query) => {
    setSearchQuery(query);
    if (query.trim()) {
      setActiveKey("skill-demand");
    }
  };

  return (
    <>
    <AppShell activeKey={activeKey} onNavigate={setActiveKey} title={meta.title} subtitle={meta.subtitle} searchQuery={searchQuery} onSearch={handleSearch}>
      {activeKey === "dashboard" && <DashboardPage onNavigate={setActiveKey} searchQuery={searchQuery} />}
      {activeKey === "cv-analyzer" && <CVAnalyzerPage />}
      {activeKey === "skill-demand" && <MarketSkillsPage initialQuery={searchQuery} />}
      {activeKey === "career-insights" && <CareerInsightsPage />}
      {activeKey === "ai-assistant" && <AssistantPage />}
      {activeKey === "about" && <AboutPage />}
    </AppShell>
    <AiAssistantWidget />
  </>
  );
}
