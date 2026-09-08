import React, { useState, useEffect } from "react";
import { MessageSquare, Clock, ExternalLink, Loader2 } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";
import { getRecommendations } from "../../api/client";

export default function InterviewPrepPanel({ foundSkills }) {
  const [prepItems, setPrepItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getRecommendations().then((data) => {
      if (!cancelled) {
        setPrepItems(data.interviewPrep);
        setLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-2xl border p-10" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <Loader2 size={20} className="animate-spin" style={{ color: COLORS.deepBlue }} />
        <span className="ml-2 text-sm" style={{ color: COLORS.textSecondary }}>Loading interview prep...</span>
      </div>
    );
  }

  if (prepItems.length === 0) {
    return (
      <div className="rounded-2xl border p-6 text-center" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <MessageSquare size={24} style={{ color: COLORS.textSecondary, margin: "0 auto 8px" }} />
        <p className="text-sm" style={{ color: COLORS.textSecondary }}>Upload your CV to see interview prep recommendations for your skills.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h3 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Interview preparation</h3>
        <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>Practice mock interviews for the skills you already have</p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {prepItems.map((item, i) => (
          <a
            key={`${item.skill}-${i}`}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex flex-col justify-between rounded-xl border p-4 transition-shadow hover:shadow-sm"
            style={{ borderColor: COLORS.border, background: "#fff", textDecoration: "none" }}
          >
            <div>
              <div className="flex items-start justify-between gap-2">
                <h4 className="text-sm font-semibold leading-snug" style={{ color: COLORS.textDark }}>{item.title}</h4>
                <ExternalLink size={13} className="shrink-0 mt-0.5" style={{ color: COLORS.textSecondary }} />
              </div>
              <p className="mt-1 text-xs" style={{ color: COLORS.textSecondary }}>{item.provider}</p>
              <p className="mt-2 text-xs" style={{ color: COLORS.textSecondary }}>{item.reason}</p>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {item.skill && (
                <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: "rgba(11,31,58,0.06)", color: COLORS.navy }}>
                  {item.skill}
                </span>
              )}
              <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: "rgba(139,92,246,0.1)", color: "#7C3AED" }}>
                {item.format}
              </span>
              <span className="flex items-center gap-1 text-[10px]" style={{ color: COLORS.textSecondary }}>
                <Clock size={10} /> {item.duration}
              </span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
