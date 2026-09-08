import React, { useState, useEffect } from "react";
import { BookOpen, Clock, ExternalLink, Loader2 } from "lucide-react";
import { COLORS, FONTS } from "../../lib/theme";
import { getRecommendations } from "../../api/client";

const PRIORITY_STYLE = {
  HIGH: { bg: "rgba(22,163,74,0.1)", fg: COLORS.success },
  MEDIUM: { bg: "rgba(245,158,11,0.12)", fg: "#B45309" },
  LOW: { bg: "rgba(102,112,133,0.1)", fg: COLORS.textSecondary },
};

const DIFFICULTY_STYLE = {
  Beginner: { bg: "rgba(22,163,74,0.08)", fg: COLORS.success },
  Intermediate: { bg: "rgba(245,158,11,0.1)", fg: "#B45309" },
  Advanced: { bg: "rgba(220,38,38,0.08)", fg: COLORS.error },
};

export default function CourseRecommendations({ missingSkills }) {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getRecommendations().then((data) => {
      if (!cancelled) {
        setCourses(data.courses);
        setLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-2xl border p-10" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <Loader2 size={20} className="animate-spin" style={{ color: COLORS.deepBlue }} />
        <span className="ml-2 text-sm" style={{ color: COLORS.textSecondary }}>Loading course recommendations...</span>
      </div>
    );
  }

  if (courses.length === 0) {
    return (
      <div className="rounded-2xl border p-6 text-center" style={{ borderColor: COLORS.border, background: "#fff" }}>
        <BookOpen size={24} style={{ color: COLORS.textSecondary, margin: "0 auto 8px" }} />
        <p className="text-sm" style={{ color: COLORS.textSecondary }}>Upload your CV to see personalized course recommendations based on your skill gaps.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h3 className="text-base font-semibold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Recommended courses</h3>
        <p className="mt-0.5 text-xs" style={{ color: COLORS.textSecondary }}>Based on skills your top-matching jobs require that you're missing</p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {courses.map((course, i) => {
          const pStyle = PRIORITY_STYLE[course.priority] || PRIORITY_STYLE.MEDIUM;
          const dStyle = DIFFICULTY_STYLE[course.difficulty] || DIFFICULTY_STYLE.Beginner;
          return (
            <a
              key={`${course.skill}-${i}`}
              href={course.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex flex-col justify-between rounded-xl border p-4 transition-shadow hover:shadow-sm"
              style={{ borderColor: COLORS.border, background: "#fff", textDecoration: "none" }}
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-semibold leading-snug" style={{ color: COLORS.textDark }}>{course.title}</h4>
                  <ExternalLink size={13} className="shrink-0 mt-0.5" style={{ color: COLORS.textSecondary }} />
                </div>
                <p className="mt-1 text-xs" style={{ color: COLORS.textSecondary }}>{course.provider}</p>
                <p className="mt-2 text-xs" style={{ color: COLORS.textSecondary }}>{course.reason}</p>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {course.skill && (
                  <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: "rgba(11,31,58,0.06)", color: COLORS.navy }}>
                    {course.skill}
                  </span>
                )}
                <span className="flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: dStyle.bg, color: dStyle.fg }}>
                  {course.difficulty}
                </span>
                <span className="flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: pStyle.bg, color: pStyle.fg }}>
                  {course.priority}
                </span>
                <span className="flex items-center gap-1 text-[10px]" style={{ color: COLORS.textSecondary }}>
                  <Clock size={10} /> {course.duration}
                </span>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
