import React, { useCallback } from "react";
import { TrendingUp, ArrowRight, Sparkles } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";
import { getOpportunityUnlocks } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";

export default function OpportunityUnlockCard({ cvAnalysis, onExplore }) {
  const fetcher = useCallback(() => getOpportunityUnlocks(cvAnalysis), [cvAnalysis]);
  const { status, data } = useAsync(fetcher, [cvAnalysis]);

  if (status !== "success" || !data.unlocks.length) return null;
  const top = data.unlocks[0];

  return (
    <div
      className="relative overflow-hidden rounded-2xl p-5 sm:p-6 transition-all duration-300 hover-lift sm:flex-row sm:items-center sm:justify-between animate-fade-in"
      style={{
        background: "linear-gradient(135deg, rgba(250,81,15,0.05), rgba(16,185,129,0.05))",
        border: "1px solid rgba(250,81,15,0.15)",
      }}
    >
      <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-accent/10 blur-2xl" />
      <div className="relative z-10 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
            style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
          >
            <TrendingUp size={18} color="#fff" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider" style={{ color: COLORS.accent }}>
              <Sparkles size={12} className="mr-1 inline" />
              Opportunity you could unlock
            </p>
            <p className="mt-1.5 text-sm leading-relaxed" style={{ color: COLORS.textDark }}>
              Learning{" "}
              <span className="font-bold" style={{ color: COLORS.accent }}>
                {top.skill}
              </span>{" "}
              could unlock{" "}
              <span className="font-bold" style={{ fontFamily: FONTS.display }}>
                +{top.unlockedCount} job{top.unlockedCount === 1 ? "" : "s"}
              </span>{" "}
              you're not currently a strong candidate for.
            </p>
          </div>
        </div>
        <button
          onClick={() => onExplore(top.skill)}
          className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:shadow-glow-blue hover:scale-105"
          style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}
        >
          Explore these jobs <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}
