import React, { useState, useEffect } from "react";
import {
  LayoutDashboard,
  FileSearch,
  TrendingUp,
  Compass,
  Sparkles,
  Info,
  LogOut,
  User,
  Search,
  Bell,
  Menu,
  X,
  PanelLeftClose,
  PanelLeftOpen,
  ChevronRight,
} from "lucide-react";
import { COLORS, FONTS, GRADIENTS } from "../../lib/theme";
import { useAppState } from "../../state/AppContext";
import { useAuth, useAuthActions } from "../../state/AuthContext";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "cv-analyzer", label: "CV Analyzer", icon: FileSearch },
  { key: "skill-demand", label: "Skill Demand", icon: TrendingUp },
  { key: "career-insights", label: "Career Insights", icon: Compass },
  { key: "ai-assistant", label: "AI Assistant", icon: Sparkles },
  { key: "about", label: "About", icon: Info },
];

function NavList({ activeKey, onNavigate, onItemClick, collapsed }) {
  return (
    <nav className="flex flex-col gap-1">
      {NAV_ITEMS.map(({ key, label, icon: Icon }) => {
        const active = key === activeKey;
        return (
          <button
            key={key}
            onClick={() => {
              onNavigate(key);
              onItemClick?.();
            }}
            title={collapsed ? label : undefined}
            className={`group relative flex items-center gap-3 rounded-xl py-2.5 text-left text-sm transition-all duration-300 ${
              collapsed ? "justify-center px-2" : "justify-between px-3"
            }`}
            style={{
              background: active
                ? "rgba(250,81,15,0.15)"
                : "transparent",
              color: active ? "#FF7A3D" : "rgba(234,243,250,0.6)",
              fontWeight: active ? 600 : 400,
            }}
          >
            {active && (
              <div
                className="absolute left-0 top-1/2 -translate-y-1/2 rounded-r-full"
                style={{
                  width: "3px",
                  height: "60%",
                  background: "linear-gradient(180deg, #FF7A3D, #FA510F)",
                }}
              />
            )}
            <span className="flex items-center gap-3">
              <Icon
                size={18}
                strokeWidth={active ? 2.2 : 1.8}
                className={`transition-all duration-200 ${
                  active ? "text-blue-400" : "text-white/50 group-hover:text-white/80"
                }`}
              />
              {!collapsed && (
                <span className="transition-colors duration-200 group-hover:text-white/90">
                  {label}
                </span>
              )}
            </span>
            {!collapsed && active && (
              <ChevronRight size={14} className="text-blue-400/60" />
            )}
          </button>
        );
      })}
    </nav>
  );
}

export default function AppShell({ activeKey, onNavigate, title, subtitle, searchQuery, onSearch, children }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [localSearch, setLocalSearch] = useState(searchQuery || "");
  const { profile } = useAppState();
  const { user } = useAuth();
  const { logout } = useAuthActions();

  const userName = user?.name || profile?.name || "User";
  const greeting = profile?.greeting || "Hello";

  useEffect(() => {
    const handleScroll = (e) => {
      setScrolled(e.target.scrollTop > 10);
    };
    const main = document.getElementById("main-content");
    if (main) main.addEventListener("scroll", handleScroll);
    return () => main?.removeEventListener("scroll", handleScroll);
  }, []);

  const sidebarWidth = sidebarCollapsed ? "w-[72px]" : "w-48";

  return (
    <div className="flex min-h-screen w-full" style={{ background: COLORS.pageBg, fontFamily: FONTS.body }}>
      {/* Sidebar (desktop) */}
      <aside
        className={`hidden ${sidebarWidth} shrink-0 flex-col justify-between py-6 transition-all duration-300 lg:flex fixed inset-y-0 left-0 z-30 overflow-y-auto ${
          sidebarCollapsed ? "px-3" : "px-5"
        }`}
        style={{ background: GRADIENTS.sidebar }}
      >
        <div>
          {/* Logo */}
          <div
            className={`mb-10 flex items-center ${
              sidebarCollapsed ? "justify-center" : "gap-3 px-1"
            }`}
          >
            <div
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
              style={{
                background: "linear-gradient(135deg, #FA510F, #E04500)",
                boxShadow: "0 4px 12px rgba(250,81,15,0.3)",
              }}
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <polyline
                  points="1,9 5,9 7,3 10,15 12,9 17,9"
                  stroke="white"
                  strokeWidth="2"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  fill="none"
                />
              </svg>
            </div>
            {!sidebarCollapsed && (
              <div>
                <span
                  className="text-lg font-bold tracking-tight text-white"
                  style={{ fontFamily: FONTS.display }}
                >
                  JobPulse
                </span>
                <p className="text-[10px] text-white/40">Career Intelligence</p>
              </div>
            )}
          </div>

          {/* Navigation */}
          <NavList
            activeKey={activeKey}
            onNavigate={onNavigate}
            collapsed={sidebarCollapsed}
          />
        </div>

        {/* Bottom section */}
        <div className="flex flex-col gap-1 border-t border-white/10 pt-4">
          <button
            onClick={() => setSidebarCollapsed((c) => !c)}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            className={`flex items-center gap-3 rounded-xl py-2.5 text-sm transition-all duration-200 hover:bg-white/5 ${
              sidebarCollapsed ? "justify-center px-2" : "px-3"
            }`}
            style={{ color: "rgba(234,243,250,0.5)" }}
          >
            {sidebarCollapsed ? (
              <PanelLeftOpen size={18} strokeWidth={1.8} />
            ) : (
              <PanelLeftClose size={18} strokeWidth={1.8} />
            )}
            {!sidebarCollapsed && <span>Collapse</span>}
          </button>

          <button
            onClick={logout}
            title={sidebarCollapsed ? "Logout" : undefined}
            className={`flex items-center gap-3 rounded-xl py-2.5 text-sm transition-all duration-200 hover:bg-red-500/10 ${
              sidebarCollapsed ? "justify-center px-2" : "px-3"
            }`}
            style={{ color: "rgba(234,243,250,0.5)" }}
          >
            <LogOut size={18} strokeWidth={1.8} />
            {!sidebarCollapsed && <span className="group-hover:text-red-400">Logout</span>}
          </button>
        </div>
      </aside>

      {/* Mobile nav drawer */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden animate-fade-in">
          <div
            className="w-52 px-5 py-6"
            style={{ background: GRADIENTS.sidebar }}
          >
            <div className="mb-8 flex items-center justify-between px-1">
              <div className="flex items-center gap-3">
                <div
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
                  style={{
                    background: "linear-gradient(135deg, #FA510F, #E04500)",
                  }}
                >
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                    <polyline
                      points="1,9 5,9 7,3 10,15 12,9 17,9"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinejoin="round"
                      strokeLinecap="round"
                      fill="none"
                    />
                  </svg>
                </div>
                <span
                  className="text-lg font-bold text-white"
                  style={{ fontFamily: FONTS.display }}
                >
                  JobPulse
                </span>
              </div>
              <button
                onClick={() => setMobileNavOpen(false)}
                className="rounded-lg p-1.5 text-white/60 hover:bg-white/10 hover:text-white"
              >
                <X size={20} />
              </button>
            </div>
            <NavList
              activeKey={activeKey}
              onNavigate={onNavigate}
              onItemClick={() => setMobileNavOpen(false)}
            />
          </div>
          <div
            className="flex-1 animate-fade-in"
            style={{ background: "rgba(16,31,60,0.5)", backdropFilter: "blur(4px)" }}
            onClick={() => setMobileNavOpen(false)}
          />
        </div>
      )}

      {/* Main content area */}
      <div
        className={`flex min-w-0 flex-1 flex-col ${
          sidebarCollapsed ? "lg:ml-[72px]" : "lg:ml-48"
        }`}
      >
        {/* Header */}
        <header
          className={`sticky top-0 z-20 flex items-center justify-between gap-4 border-b px-4 py-3 transition-all duration-300 lg:px-6 ${
            scrolled ? "shadow-sm" : ""
          }`}
          style={{
            borderColor: COLORS.border,
            background: scrolled
              ? "rgba(255,255,255,0.9)"
              : "#FFFFFF",
            backdropFilter: scrolled ? "blur(12px)" : "none",
          }}
        >
          <div className="flex items-center gap-4">
            <button
              className="lg:hidden rounded-lg p-2 hover:bg-surface-tertiary transition-colors"
              onClick={() => setMobileNavOpen(true)}
            >
              <Menu size={22} style={{ color: COLORS.textDark }} />
            </button>
            <div>
              <h1
                className="text-lg font-semibold sm:text-xl"
                style={{
                  color: COLORS.textDark,
                  fontFamily: FONTS.display,
                  lineHeight: 1.2,
                }}
              >
                {title ?? `${greeting}, ${userName}`}
              </h1>
              {subtitle && (
                <p
                  className="hidden text-xs sm:block mt-0.5"
                  style={{ color: COLORS.textSecondary }}
                >
                  {subtitle}
                </p>
              )}
            </div>
          </div>

          <div className="hidden flex-1 items-center gap-3 rounded-xl border px-4 py-2.5 md:flex md:max-w-md transition-all duration-200 focus-within:border-accent focus-within:shadow-glow-blue"
            style={{ borderColor: COLORS.border, background: COLORS.pageBg }}
          >
            <Search size={16} style={{ color: COLORS.textMuted }} />
            <input
              placeholder="Search jobs, skills or companies..."
              className="w-full bg-transparent text-sm outline-none placeholder:text-textMuted"
              style={{ color: COLORS.textDark }}
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  onSearch?.(localSearch);
                }
              }}
            />
          </div>

          <div className="flex items-center gap-3">
            <button className="relative rounded-xl p-2.5 transition-colors hover:bg-surface-tertiary">
              <Bell size={18} style={{ color: COLORS.textSecondary }} />
              <span
                className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full"
                style={{
                  background: "linear-gradient(135deg, #F59E0B, #D97706)",
                  boxShadow: "0 0 6px rgba(245,158,11,0.4)",
                }}
              />
            </button>
            <div
              className="flex h-9 w-9 items-center justify-center rounded-xl text-sm font-semibold text-white transition-transform hover:scale-105"
              style={{
                background: "linear-gradient(135deg, #FA510F, #E04500)",
                boxShadow: "0 2px 8px rgba(250,81,15,0.3)",
                fontFamily: FONTS.display,
              }}
            >
              {userName?.[0]?.toUpperCase() ?? "U"}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main
          id="main-content"
          className="flex-1 overflow-y-auto px-4 py-5 sm:px-6 lg:px-10 lg:py-6"
        >
          <div className="page-enter" key={activeKey}>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
