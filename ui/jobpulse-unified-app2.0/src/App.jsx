import React, { useState } from "react";
import AppShell from "./components/layout/AppShell";
import DashboardPage from "./pages/DashboardPage";
import CVAnalyzerPage from "./pages/CVAnalyzerPage";
import MarketSkillsPage from "./pages/MarketSkillsPage";
import AssistantPage from "./pages/AssistantPage";
import AuthPage from "./pages/AuthPage";
import { useAuth } from "./state/AuthContext";

// Job Market is no longer a standalone screen - its search/filter/card
// components now live inside CV Analyzer's "Recommended Jobs" tab, so the
// only routes left are the ones in the (trimmed) sidebar.
const PAGE_META = {
  dashboard: { title: null, subtitle: null },
  "cv-analyzer": { title: "CV Analyzer", subtitle: "Your personal career-to-job matching engine" },
  "skill-demand": { title: "Skill Demand", subtitle: "African tech skills intelligence" },
  "ai-assistant": { title: "AI Assistant", subtitle: "Ask questions about the African tech job market" },
};

export default function App() {
  const { token } = useAuth();
  const [activeKey, setActiveKey] = useState("dashboard");
  const meta = PAGE_META[activeKey] ?? {};

  if (!token) return <AuthPage />;

  return (
    <AppShell activeKey={activeKey} onNavigate={setActiveKey} title={meta.title} subtitle={meta.subtitle}>
      {activeKey === "dashboard" && <DashboardPage onNavigate={setActiveKey} />}
      {activeKey === "cv-analyzer" && <CVAnalyzerPage />}
      {activeKey === "skill-demand" && <MarketSkillsPage />}
      {activeKey === "ai-assistant" && <AssistantPage />}
    </AppShell>
  );
}
