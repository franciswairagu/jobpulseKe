import React, { useState } from "react";
import AppShell from "./components/layout/AppShell";
import DashboardPage from "./pages/DashboardPage";
import CVAnalyzerPage from "./pages/CVAnalyzerPage";
import MarketSkillsPage from "./pages/MarketSkillsPage";

// Job Market is no longer a standalone screen - its search/filter/card
// components now live inside CV Analyzer's "Recommended Jobs" tab, so the
// only routes left are the ones in the (trimmed) sidebar.
const PAGE_META = {
  dashboard: { title: null, subtitle: null },
  "cv-analyzer": { title: "CV Analyzer", subtitle: "Your personal career-to-job matching engine" },
  "skill-demand": { title: "Skill Demand", subtitle: "African tech skills intelligence" },
};

export default function App() {
  const [activeKey, setActiveKey] = useState("dashboard");
  const meta = PAGE_META[activeKey] ?? {};

  return (
    <AppShell activeKey={activeKey} onNavigate={setActiveKey} title={meta.title} subtitle={meta.subtitle}>
      {activeKey === "dashboard" && <DashboardPage onNavigate={setActiveKey} />}
      {activeKey === "cv-analyzer" && <CVAnalyzerPage />}
      {activeKey === "skill-demand" && <MarketSkillsPage />}
    </AppShell>
  );
}
