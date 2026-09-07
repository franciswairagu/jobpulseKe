import React, { useState } from "react";
import {
  LayoutDashboard,
  FileSearch,
  TrendingUp,
  Compass,
  DollarSign,
  Sparkles,
  Settings,
  LogOut,
  User,
  Search,
  Bell,
  Menu,
  X,
} from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";
import { useAppState } from "../../state/AppContext";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "cv-analyzer", label: "CV Analyzer", icon: FileSearch },
  { key: "skill-demand", label: "Skill Demand", icon: TrendingUp },
  { key: "career-insights", label: "Career Insights", icon: Compass, comingSoon: true },
  { key: "salary-insights", label: "Salary Insights", icon: DollarSign, comingSoon: true },
  { key: "ai-assistant", label: "AI Assistant", icon: Sparkles, comingSoon: true },
];

function NavList({ activeKey, onNavigate, onItemClick }) {
  return (
    <nav className="flex flex-col gap-1">
      {NAV_ITEMS.map(({ key, label, icon: Icon, comingSoon }) => {
        const active = key === activeKey;
        return (
          <button
            key={key}
            disabled={comingSoon}
            onClick={() => {
              if (comingSoon) return;
              onNavigate(key);
              onItemClick?.();
            }}
            className="flex items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors"
            style={{
              background: active ? "rgba(255,255,255,0.09)" : "transparent",
              color: comingSoon ? "rgba(234,243,250,0.35)" : active ? "#fff" : "rgba(234,243,250,0.65)",
              fontWeight: active ? 600 : 400,
              cursor: comingSoon ? "default" : "pointer",
            }}
          >
            <span className="flex items-center gap-3">
              <Icon size={17} strokeWidth={2} />
              {label}
            </span>
            {comingSoon && (
              <span className="rounded-full px-1.5 py-0.5 text-[9px] font-semibold" style={{ background: "rgba(255,255,255,0.08)" }}>
                SOON
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
}

export default function AppShell({ activeKey, onNavigate, title, subtitle, children }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const { profile } = useAppState();

  return (
    <div className="flex min-h-screen w-full" style={{ background: COLORS.pageBg, fontFamily: FONTS.body }}>
      {/* Sidebar (desktop) */}
      <aside className="hidden w-64 shrink-0 flex-col justify-between px-5 py-6 lg:flex" style={{ background: COLORS.navy }}>
        <div>
          <div className="mb-9 flex items-center gap-2 px-1">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ background: "rgba(255,255,255,0.08)" }}>
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <polyline points="1,9 5,9 7,3 10,15 12,9 17,9" stroke={COLORS.lightBlue} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" fill="none" />
              </svg>
            </div>
            <span className="text-lg font-semibold tracking-tight text-white" style={{ fontFamily: FONTS.display }}>
              JobPulse
            </span>
          </div>
          <NavList activeKey={activeKey} onNavigate={onNavigate} />
        </div>

        <div className="flex flex-col gap-1 border-t pt-4" style={{ borderColor: "rgba(255,255,255,0.1)" }}>
          {[{ label: "Profile", icon: User }, { label: "Settings", icon: Settings }, { label: "Logout", icon: LogOut }].map(({ label, icon: Icon }) => (
            <button key={label} className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors" style={{ color: "rgba(234,243,250,0.65)" }}>
              <Icon size={17} strokeWidth={2} />
              {label}
            </button>
          ))}
        </div>
      </aside>

      {/* Mobile nav drawer */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-30 flex lg:hidden">
          <div className="w-64 px-5 py-6" style={{ background: COLORS.navy }}>
            <div className="mb-8 flex items-center justify-between px-1">
              <span className="text-lg font-semibold text-white" style={{ fontFamily: FONTS.display }}>JobPulse</span>
              <button onClick={() => setMobileNavOpen(false)}>
                <X size={20} color="#fff" />
              </button>
            </div>
            <NavList activeKey={activeKey} onNavigate={onNavigate} onItemClick={() => setMobileNavOpen(false)} />
          </div>
          <div className="flex-1" style={{ background: "rgba(11,31,58,0.4)" }} onClick={() => setMobileNavOpen(false)} />
        </div>
      )}

      {/* Main content */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-4 border-b px-5 py-4 lg:px-8" style={{ borderColor: COLORS.border, background: "#fff" }}>
          <div className="flex items-center gap-3">
            <button className="lg:hidden" onClick={() => setMobileNavOpen(true)}>
              <Menu size={22} color={COLORS.textDark} />
            </button>
            <div>
              <p className="text-base font-semibold sm:text-lg" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
                {title ?? `${profile.greeting}, ${profile.name}`}
              </p>
              {subtitle && <p className="hidden text-xs sm:block" style={{ color: COLORS.textSecondary }}>{subtitle}</p>}
            </div>
          </div>

          <div className="hidden flex-1 items-center gap-2 rounded-lg border px-3 py-2 md:flex md:max-w-sm" style={{ borderColor: COLORS.border, background: COLORS.pageBg }}>
            <Search size={16} style={{ color: COLORS.textSecondary }} />
            <input placeholder="Search jobs, skills or companies..." className="w-full bg-transparent text-sm outline-none" style={{ color: COLORS.textDark }} />
          </div>

          <div className="flex items-center gap-4">
            <button className="relative">
              <Bell size={19} style={{ color: COLORS.textSecondary }} />
              <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full" style={{ background: COLORS.warning }} />
            </button>
            <div className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold text-white" style={{ background: COLORS.deepBlue, fontFamily: FONTS.display }}>
              {profile.name?.[0] ?? "U"}
            </div>
          </div>
        </header>

        <main className="flex-1 px-5 py-6 lg:px-8 lg:py-8">{children}</main>
      </div>
    </div>
  );
}
