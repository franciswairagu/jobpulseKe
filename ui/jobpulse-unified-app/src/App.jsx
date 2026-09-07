import React, { useState } from "react";
import AppShell from "./components/layout/AppShell";
import DashboardPage from "./pages/DashboardPage";
import CVAnalyzerPage from "./pages/CVAnalyzerPage";
import JobMarketPage from "./pages/JobMarketPage";
import MarketSkillsPage from "./pages/MarketSkillsPage";

// Simple state-based routing - no react-router dependency needed for four
// screens, and it keeps the "which page is active" concern in one place
// alongside the sidebar that already knows about all of them.
const PAGE_META = {
  dashboard: { title: null, subtitle: null },
  "cv-analyzer": { title: "CV Analyzer", subtitle: "Upload and analyze your CV" },
  "skill-demand": { title: "Skill Demand", subtitle: "African tech skills intelligence" },
  "job-market": { title: "Job Market", subtitle: "Open roles across African tech" },
};

export default function App() {
  const [activeKey, setActiveKey] = useState("dashboard");
  const meta = PAGE_META[activeKey] ?? {};

  return (
    <AppShell activeKey={activeKey} onNavigate={setActiveKey} title={meta.title} subtitle={meta.subtitle}>
      {activeKey === "dashboard" && <DashboardPage onNavigate={setActiveKey} />}
      {activeKey === "cv-analyzer" && <CVAnalyzerPage onNavigate={setActiveKey} />}
      {activeKey === "skill-demand" && <MarketSkillsPage onNavigate={setActiveKey} />}
      {activeKey === "job-market" && <JobMarketPage onNavigate={setActiveKey} />}
    </AppShell>
  );
}
