import React from "react";
import {
  BarChart3,
  Target,
  TrendingUp,
  Sparkles,
  Globe,
  Shield,
  ArrowRight,
} from "lucide-react";
import { COLORS, FONTS, GRADIENTS } from "../lib/theme";

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
    description: "RAG-powered chatbot that answers job market questions grounded in real data from 12,992 job postings. Streams responses in real-time.",
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
  { value: "12,992", label: "Job Records Analyzed" },
  { value: "10+", label: "Countries Covered" },
  { value: "600+", label: "Tech Skills Tracked" },
  { value: "15", label: "Job Board Scrapers" },
];

function PulseLine() {
  return (
    <svg viewBox="0 0 600 120" className="absolute inset-0 w-full h-full opacity-[0.15]" preserveAspectRatio="none">
      <polyline
        points="0,60 80,60 100,20 140,100 180,60 300,60 340,30 380,90 420,60 600,60"
        fill="none"
        stroke="rgba(96,165,250,0.5)"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function LandingPage({ onNavigateToAuth }) {
  return (
    <div className="min-h-screen overflow-y-auto" style={{ fontFamily: FONTS.body }}>
      {/* Hero */}
      <section className="relative overflow-hidden px-4 py-20 sm:px-8 sm:py-28 lg:py-36">
        <div
          className="absolute inset-0"
          style={{ background: GRADIENTS.hero }}
        />
        <div className="absolute inset-0">
          <PulseLine />
        </div>
        <div className="absolute top-20 left-20 h-72 w-72 rounded-full bg-blue-500/10 blur-3xl" />
        <div className="absolute bottom-20 right-20 h-96 w-96 rounded-full bg-emerald-500/10 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/5 blur-3xl" />

        <div className="relative z-10 mx-auto max-w-4xl text-center">
          <div className="mb-6 flex items-center justify-center gap-3">
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
            className="text-4xl font-bold text-white sm:text-5xl lg:text-6xl"
            style={{ fontFamily: FONTS.display, lineHeight: 1.1 }}
          >
            Empowering Africa's
            <br />
            Tech Workforce
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-white/60 sm:text-lg">
            JobPulse is an African-focused career intelligence platform that helps tech professionals
            understand market demand, identify skill gaps, and find the right opportunities — powered
            by real data from 12,992 job postings across 10+ countries.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <button
              onClick={() => onNavigateToAuth?.("register")}
              className="group flex items-center gap-2 rounded-xl px-8 py-3.5 text-sm font-semibold text-white transition-all duration-300 hover:shadow-glow-blue hover:scale-105"
              style={{
                background: "linear-gradient(135deg, #FA510F, #E04500)",
                boxShadow: "0 4px 14px rgba(250,81,15,0.3)",
              }}
            >
              Get Started
              <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
            </button>
            <button
              onClick={() => onNavigateToAuth?.("login")}
              className="flex items-center gap-2 rounded-xl border border-white/20 px-8 py-3.5 text-sm font-semibold text-white/80 transition-all duration-300 hover:border-white/40 hover:bg-white/5 hover:text-white"
            >
              Sign In
            </button>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="px-4 py-12 sm:px-8">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-4 sm:grid-cols-4">
          {STATS.map((stat) => (
            <div
              key={stat.label}
              className="rounded-2xl border p-5 text-center"
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
      </section>

      {/* Features */}
      <section className="px-4 py-16 sm:px-8">
        <div className="mx-auto max-w-5xl">
          <h2
            className="mb-3 text-center text-2xl font-bold sm:text-3xl"
            style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
          >
            Everything You Need to Advance Your Career
          </h2>
          <p className="mx-auto mb-10 max-w-xl text-center text-sm" style={{ color: COLORS.textSecondary }}>
            From market intelligence to personalized career guidance, JobPulse gives you the data-driven insights to make informed decisions.
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="group rounded-2xl border p-6 transition-all duration-300 hover:shadow-md"
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
      </section>

      {/* How It Works */}
      <section className="px-4 py-16 sm:px-8" style={{ background: COLORS.surfaceSecondary }}>
        <div className="mx-auto max-w-4xl">
          <h2
            className="mb-3 text-center text-2xl font-bold sm:text-3xl"
            style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
          >
            How It Works
          </h2>
          <p className="mx-auto mb-10 max-w-xl text-center text-sm" style={{ color: COLORS.textSecondary }}>
            Get personalized career insights in three simple steps.
          </p>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
            {[
              {
                step: "01",
                title: "Upload Your CV",
                description: "Share your resume and we'll extract your skills, experience, and qualifications using our NLP engine.",
              },
              {
                step: "02",
                title: "Get Matched",
                description: "We compare your profile against 12,992 real job postings to calculate match scores and identify gaps.",
              },
              {
                step: "03",
                title: "Take Action",
                description: "Get personalized course recommendations, career paths, and direct links to jobs that match your profile.",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="rounded-2xl border p-6 text-center"
                style={{ borderColor: COLORS.border, background: "#fff" }}
              >
                <div
                  className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl text-sm font-bold text-white"
                  style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
                >
                  {item.step}
                </div>
                <h3
                  className="text-base font-semibold"
                  style={{ color: COLORS.textDark, fontFamily: FONTS.display }}
                >
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed" style={{ color: COLORS.textSecondary }}>
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-4 py-16 sm:px-8">
        <div className="mx-auto max-w-4xl">
          <div
            className="relative overflow-hidden rounded-3xl px-8 py-12 text-center sm:px-12"
            style={{ background: GRADIENTS.hero }}
          >
            <div className="absolute inset-0 opacity-20">
              <PulseLine />
            </div>
            <div className="relative z-10">
              <h2
                className="text-2xl font-bold text-white sm:text-3xl"
                style={{ fontFamily: FONTS.display }}
              >
                Ready to Level Up Your Career?
              </h2>
              <p className="mx-auto mt-3 max-w-md text-sm text-white/60">
                Join JobPulse and get data-driven insights to navigate Africa's tech job market.
              </p>
              <button
                onClick={() => onNavigateToAuth?.("register")}
                className="mt-6 inline-flex items-center gap-2 rounded-xl px-8 py-3.5 text-sm font-semibold text-white transition-all duration-300 hover:shadow-glow-blue hover:scale-105"
                style={{
                  background: "linear-gradient(135deg, #FA510F, #E04500)",
                  boxShadow: "0 4px 14px rgba(250,81,15,0.3)",
                }}
              >
                Get Started
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t px-4 py-8 sm:px-8" style={{ borderColor: COLORS.border }}>
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 sm:flex-row">
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
            African Tech Career Intelligence Platform. Built for the African tech community.
          </p>
        </div>
      </footer>
    </div>
  );
}
