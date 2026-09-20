import React from "react";
import {
  Target,
  Users,
  BarChart3,
  Compass,
  Sparkles,
  Globe,
  Heart,
  ArrowRight,
  Shield,
  Zap,
  TrendingUp,
} from "lucide-react";
import { COLORS, FONTS } from "../lib/theme";
import { useAuth } from "../state/AuthContext";

const FEATURES = [
  {
    icon: BarChart3,
    title: "Market Intelligence",
    description: "Real-time skill demand analytics across 10+ African countries. See top skills, growth trends, and geographic hiring patterns.",
    color: "#FA510F",
    bg: "rgba(250,81,15,0.1)",
  },
  {
    icon: Target,
    title: "CV Analysis",
    description: "Upload your CV and get a market readiness score (0-100), skill gaps, strengths/weaknesses, and personalized course recommendations.",
    color: "#10B981",
    bg: "rgba(16,185,129,0.1)",
  },
  {
    icon: TrendingUp,
    title: "Career Paths",
    description: "Discover career progression paths and see what skills separate Entry, Mid, Senior, and Lead roles in your field.",
    color: "#F59E0B",
    bg: "rgba(245,158,11,0.1)",
  },
  {
    icon: Sparkles,
    title: "AI Assistant",
    description: "RAG-powered chatbot that answers job market questions grounded in real data from 14,000+ job postings. Streams responses in real-time.",
    color: "#8B5CF6",
    bg: "rgba(139,92,246,0.1)",
  },
  {
    icon: Globe,
    title: "Africa-Focused",
    description: "Built specifically for African tech markets — Nigeria, Kenya, South Africa, Ghana, Egypt, Rwanda, Uganda, Morocco, and more.",
    color: "#06B6D4",
    bg: "rgba(6,182,212,0.1)",
  },
  {
    icon: Shield,
    title: "Transparent Scoring",
    description: "Every score is explainable. Your match score breaks down by skills (65%), experience (15%), preferred skills (15%), and location (5%).",
    color: "#EC4899",
    bg: "rgba(236,72,153,0.1)",
  },
];

const STATS = [
  { value: "14,000+", label: "Job Records Analyzed" },
  { value: "10+", label: "Countries Covered" },
  { value: "800+", label: "Tech Skills Tracked" },
  { value: "15+", label: "Data Sources" },
];

export default function AboutPage() {
  const { onNavigate } = useAuth();
  const user = useAuth()?.user;

  return (
    <div className="space-y-12">
      {/* Hero section */}
      <div className="relative overflow-hidden rounded-3xl px-8 py-12 sm:px-12 sm:py-16">
        <div
          className="absolute inset-0"
          style={{ background: "linear-gradient(135deg, #101F3C 0%, #1a2d4a 50%, #101F3C 100%)" }}
        />
        <div className="absolute inset-0 opacity-20">
          <svg viewBox="0 0 600 120" className="w-full h-full" preserveAspectRatio="none">
            <polyline
              points="0,60 80,60 100,20 140,100 180,60 300,60 340,30 380,90 420,60 600,60"
              fill="none"
              stroke="rgba(96,165,250,0.4)"
              strokeWidth="2"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-accent/10 blur-3xl" />
        <div className="absolute -bottom-20 -left-20 h-48 w-48 rounded-full bg-emerald-500/10 blur-3xl" />

        <div className="relative z-10 max-w-2xl">
          <div className="mb-6 flex items-center gap-3">
            <div
              className="flex h-12 w-12 items-center justify-center rounded-2xl"
              style={{
                background: "linear-gradient(135deg, #FA510F, #E04500)",
                boxShadow: "0 4px 12px rgba(250,81,15,0.3)",
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
            <span className="text-2xl font-bold text-white" style={{ fontFamily: FONTS.display }}>
              JobPulse
            </span>
          </div>

          <h1
            className="text-3xl font-bold text-white sm:text-4xl"
            style={{ fontFamily: FONTS.display, lineHeight: 1.2 }}
          >
            Empowering Africa's Tech Workforce
          </h1>
          <p className="mt-4 max-w-xl text-base leading-relaxed text-white/70">
            JobPulse is an African-focused career intelligence platform that helps tech professionals
            understand market demand, identify skill gaps, and find the right opportunities.
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 stagger-children">
        {STATS.map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl border p-5 text-center transition-all duration-300 hover-lift"
            style={{ borderColor: COLORS.border, background: "#fff" }}
          >
            <p
              className="text-2xl font-bold"
              style={{ color: COLORS.accent, fontFamily: FONTS.display }}
            >
              {stat.value}
            </p>
            <p className="mt-1 text-xs font-medium" style={{ color: COLORS.textSecondary }}>
              {stat.label}
            </p>
          </div>
        ))}
      </div>

      {/* Mission */}
      <div className="max-w-3xl">
        <h2
          className="text-2xl font-bold"
          style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
        >
          Our Mission
        </h2>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: COLORS.textSecondary }}>
          Africa's tech ecosystem is growing rapidly, but navigating the job market remains challenging.
          JobPulse bridges the gap between talent and opportunity by providing data-driven insights
          into what skills are in demand, which companies are hiring, and how professionals can
          position themselves for success.
        </p>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: COLORS.textSecondary }}>
          Our 4-stage data pipeline collects 14,000+ job records from 15+ scrapers and TechMap across platforms like
          BrighterMonday, Jobberman, Careers24, LinkedIn, Indeed, and 27 additional portals. We extract 600+ skills across 15
          categories, analyze salary distributions, career pathways, and remote work trends — giving
          you an unbiased, real-time view of the market.
        </p>
      </div>

      {/* Features */}
      <div>
        <h2
          className="mb-6 text-2xl font-bold"
          style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
        >
          What We Offer
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-children">
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="group rounded-2xl border p-6 transition-all duration-300 hover-lift"
                style={{ borderColor: COLORS.border, background: "#fff" }}
              >
                <div
                  className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl transition-transform group-hover:scale-110"
                  style={{ background: feature.bg }}
                >
                  <Icon size={22} style={{ color: feature.color }} />
                </div>
                <h3
                  className="text-base font-semibold"
                  style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
                >
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed" style={{ color: COLORS.textSecondary }}>
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* How it works */}
      <div className="rounded-2xl border p-6 sm:p-8" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <h2
          className="mb-6 text-2xl font-bold"
          style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
        >
          How It Works
        </h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {[
            {
              step: "01",
              title: "Upload Your CV",
              description: "Share your resume and we'll extract your skills, experience, and qualifications.",
            },
            {
              step: "02",
              title: "Get Matched",
              description: "We compare your profile against real job postings to calculate match scores and identify gaps.",
            },
            {
              step: "03",
              title: "Take Action",
              description: "Get personalized course recommendations, career paths, and direct links to apply.",
            },
          ].map((item, i) => (
            <div key={item.step} className="flex gap-4">
              <div
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold text-white"
                style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
              >
                {item.step}
              </div>
              <div>
                <h3
                  className="text-sm font-semibold"
                  style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
                >
                  {item.title}
                </h3>
                <p className="mt-1 text-xs leading-relaxed" style={{ color: COLORS.textSecondary }}>
                  {item.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Values */}
      <div>
        <h2
          className="mb-6 text-2xl font-bold"
          style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
        >
          Our Values
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[
            {
              icon: Heart,
              title: "User-First",
              description: "Every feature is designed to help you make better career decisions.",
            },
            {
              icon: Shield,
              title: "Transparency",
              description: "We show our work. Every score, every recommendation — you see how it's calculated.",
            },
            {
              icon: Globe,
              title: "Africa-Focused",
              description: "Built by Africans, for Africans. We understand the unique dynamics of our tech markets.",
            },
            {
              icon: Zap,
              title: "Data-Driven",
              description: "No opinions, no biases. Just real job posting data analyzed to give you actionable insights.",
            },
          ].map((value) => {
            const Icon = value.icon;
            return (
              <div
                key={value.title}
                className="flex gap-4 rounded-xl border p-4 transition-all duration-200 hover:shadow-sm"
                style={{ borderColor: COLORS.borderLight, background: "#FAFBFC" }}
              >
                <div
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
                  style={{ background: COLORS.lightBlue }}
                >
                  <Icon size={18} style={{ color: COLORS.accent }} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold" style={{ color: COLORS.textDark }}>
                    {value.title}
                  </h3>
                  <p className="mt-0.5 text-xs leading-relaxed" style={{ color: COLORS.textSecondary }}>
                    {value.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t pt-6 pb-4" style={{ borderColor: COLORS.border }}>
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <div
              className="flex h-6 w-6 items-center justify-center rounded-md"
              style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
            >
              <svg width="12" height="12" viewBox="0 0 18 18" fill="none">
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
            <span className="text-sm font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>
              JobPulse
            </span>
          </div>
          <p className="text-xs" style={{ color: COLORS.textMuted }}>
            African Tech Career Intelligence Platform. Open source and built for the African tech community.
          </p>
        </div>
      </div>
    </div>
  );
}
