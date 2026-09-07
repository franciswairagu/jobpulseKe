import React, { useCallback } from "react";
import { TrendingUp, ArrowRight } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";
import { getOpportunityUnlocks } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";

// Spec sections 10/11: "Learning SQL could unlock +37 jobs". Only rendered
// when getOpportunityUnlocks actually finds jobs that cross the qualifying
// threshold once a missing skill is added - per the spec's rule to never
// show a number that can't be calculated from real job data.
export default function OpportunityUnlockCard({ cvAnalysis, onExplore }) {
  const fetcher = useCallback(() => getOpportunityUnlocks(cvAnalysis), [cvAnalysis]);
  const { status, data } = useAsync(fetcher, [cvAnalysis]);

  if (status !== "success" || !data.unlocks.length) return null;
  const top = data.unlocks[0];

  return (
    <div className="flex flex-col gap-3 rounded-2xl border p-5 sm:flex-row sm:items-center sm:justify-between" style={{ borderColor: COLORS.border, background: COLORS.lightBlue }}>
      <div className="flex items-start gap-3">
        <TrendingUp size={20} style={{ color: COLORS.deepBlue, marginTop: 2 }} />
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: COLORS.deepBlue }}>Opportunity you could unlock</p>
          <p className="mt-1 text-sm" style={{ color: COLORS.textDark }}>
            Learning <span className="font-semibold">{top.skill}</span> could unlock{" "}
            <span className="font-semibold" style={{ fontFamily: FONTS.display }}>+{top.unlockedCount} job{top.unlockedCount === 1 ? "" : "s"}</span> you're not currently a strong candidate for.
          </p>
        </div>
      </div>
      <button onClick={() => onExplore(top.skill)} className="flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-semibold text-white" style={{ background: COLORS.navy }}>
        Explore these jobs <ArrowRight size={14} />
      </button>
    </div>
  );
}
