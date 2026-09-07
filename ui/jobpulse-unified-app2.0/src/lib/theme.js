// Single source of truth for the JobPulse design system.
// Every page/component imports from here instead of redefining hex values,
// so the visual language stays consistent as the app grows.

export const COLORS = {
  navy: "#0B1F3A",
  deepBlue: "#123B63",
  lightBlue: "#EAF3FA",
  pageBg: "#F7F9FC",
  textDark: "#172033",
  textSecondary: "#667085",
  success: "#16A34A",
  warning: "#F59E0B",
  error: "#DC2626",
  border: "#E4E9F2",
  rowBorder: "#EEF2F7",
};

export const FONTS = {
  display: "Space Grotesk, sans-serif",
  body: "Inter, sans-serif",
};

export const PRIORITY_STYLES = {
  HIGH: { bg: "rgba(220,38,38,0.1)", fg: COLORS.error },
  MEDIUM: { bg: "rgba(245,158,11,0.12)", fg: "#B45309" },
  LOW: { bg: "rgba(22,163,74,0.1)", fg: COLORS.success },
};

export const AFRICAN_COUNTRIES = [
  "Kenya",
  "Nigeria",
  "South Africa",
  "Ghana",
  "Uganda",
  "Rwanda",
  "Egypt",
];

export const PERIODS = ["Last 30 days", "Last 3 months", "Last 6 months", "Last year"];
