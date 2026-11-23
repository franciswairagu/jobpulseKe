import React, { useEffect, useState } from "react";
import { Download, FileText, Loader2, Save, UserRound } from "lucide-react";
import { downloadCV, getProfile, updateProfile } from "../api/client";
import { useAuthActions } from "../state/AuthContext";
import { COLORS, FONTS } from "../lib/theme";

const EMPTY_PROFILE = {
  name: "",
  country: "",
  city: "",
  career_interest: "",
  years_experience: "",
  preferred_work_mode: "",
};

function ErrorMessage({ children }) {
  if (!children) return null;
  return (
    <div role="alert" className="rounded-xl px-4 py-3 text-sm" style={{ background: "rgba(239,68,68,0.08)", color: COLORS.error }}>
      {children}
    </div>
  );
}

export default function ProfilePage() {
  const [profile, setProfile] = useState(EMPTY_PROFILE);
  const [email, setEmail] = useState("");
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);
  const { setUser } = useAuthActions();

  useEffect(() => {
    let active = true;
    getProfile()
      .then((data) => {
        if (!active) return;
        setEmail(data.email);
        setResume(data.latest_resume);
        setProfile({
          name: data.name || "",
          country: data.country || "",
          city: data.city || "",
          career_interest: data.career_interest || "",
          years_experience: data.years_experience ?? "",
          preferred_work_mode: data.preferred_work_mode || "",
        });
      })
      .catch((loadError) => {
        if (active) setError(loadError.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const updateField = (event) => {
    setSaved(false);
    setProfile((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSave = async (event) => {
    event.preventDefault();
    setError(null);
    setSaved(false);
    setSaving(true);
    try {
      const updated = await updateProfile({
        ...profile,
        years_experience: profile.years_experience === "" ? null : Number(profile.years_experience),
      });
      setEmail(updated.email);
      setResume(updated.latest_resume);
      setProfile({
        name: updated.name || "",
        country: updated.country || "",
        city: updated.city || "",
        career_interest: updated.career_interest || "",
        years_experience: updated.years_experience ?? "",
        preferred_work_mode: updated.preferred_work_mode || "",
      });
      setUser(updated);
      setSaved(true);
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDownload = async () => {
    if (!resume) return;
    setError(null);
    setDownloading(true);
    try {
      await downloadCV(resume.resume_id, resume.original_filename);
    } catch (downloadError) {
      setError(downloadError.message);
    } finally {
      setDownloading(false);
    }
  };

  const inputClass = "w-full rounded-xl border bg-white px-3.5 py-3 text-sm outline-none transition focus:border-accent";
  const inputStyle = { color: COLORS.textDark, borderColor: COLORS.border };

  if (loading) {
    return (
      <div className="flex items-center gap-3 py-12 text-sm" style={{ color: COLORS.textSecondary }}>
        <Loader2 size={18} className="animate-spin" /> Loading your profile...
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h2 className="text-2xl font-bold" style={{ color: COLORS.textDark, fontFamily: FONTS.display }}>Your profile</h2>
        <p className="mt-1 text-sm" style={{ color: COLORS.textSecondary }}>Manage your account details and saved career documents.</p>
      </div>

      <ErrorMessage>{error}</ErrorMessage>

      <form onSubmit={handleSave} className="rounded-2xl border bg-white p-5 sm:p-7" style={{ borderColor: COLORS.border }}>
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl p-2.5" style={{ color: COLORS.accent, background: "rgba(250,81,15,0.08)" }}><UserRound size={20} /></div>
          <div>
            <h3 className="font-semibold" style={{ color: COLORS.textDark }}>Personal details</h3>
            <p className="text-xs" style={{ color: COLORS.textMuted }}>Your Google account controls your sign-in email.</p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-1.5 text-xs font-medium" style={{ color: COLORS.textSecondary }}>
            Email
            <input className={inputClass} style={inputStyle} value={email} readOnly aria-readonly="true" />
          </label>
          <label className="space-y-1.5 text-xs font-medium" style={{ color: COLORS.textSecondary }}>
            Full name
            <input className={inputClass} style={inputStyle} name="name" value={profile.name} onChange={updateField} maxLength={255} />
          </label>
          <label className="space-y-1.5 text-xs font-medium" style={{ color: COLORS.textSecondary }}>
            Country
            <input className={inputClass} style={inputStyle} name="country" value={profile.country} onChange={updateField} maxLength={100} />
          </label>
          <label className="space-y-1.5 text-xs font-medium" style={{ color: COLORS.textSecondary }}>
            City
            <input className={inputClass} style={inputStyle} name="city" value={profile.city} onChange={updateField} maxLength={100} />
          </label>
          <label className="space-y-1.5 text-xs font-medium" style={{ color: COLORS.textSecondary }}>
            Career interest
            <input className={inputClass} style={inputStyle} name="career_interest" value={profile.career_interest} onChange={updateField} maxLength={255} placeholder="e.g. Data Analyst" />
          </label>
          <label className="space-y-1.5 text-xs font-medium" style={{ color: COLORS.textSecondary }}>
            Years of experience
            <input className={inputClass} style={inputStyle} name="years_experience" type="number" min="0" max="70" value={profile.years_experience} onChange={updateField} />
          </label>
          <label className="space-y-1.5 text-xs font-medium sm:col-span-2" style={{ color: COLORS.textSecondary }}>
            Preferred work mode
            <select className={inputClass} style={inputStyle} name="preferred_work_mode" value={profile.preferred_work_mode} onChange={updateField}>
              <option value="">Select a preference</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">On-site</option>
              <option value="flexible">Flexible</option>
            </select>
          </label>
        </div>

        <div className="mt-5 flex items-center justify-between gap-3">
          <span aria-live="polite" className="text-sm" style={{ color: COLORS.success }}>
            {saved ? "Profile saved." : ""}
          </span>
          <button type="submit" disabled={saving} className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60" style={{ background: "linear-gradient(135deg, #FA510F, #E04500)" }}>
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            Save changes
          </button>
        </div>
      </form>

      <section className="rounded-2xl border bg-white p-5 sm:p-7" style={{ borderColor: COLORS.border }}>
        <div className="mb-5 flex items-center gap-3">
          <div className="rounded-xl p-2.5" style={{ color: COLORS.accent, background: "rgba(250,81,15,0.08)" }}><FileText size={20} /></div>
          <div>
            <h3 className="font-semibold" style={{ color: COLORS.textDark }}>Saved CV</h3>
            <p className="text-xs" style={{ color: COLORS.textMuted }}>Your document stays linked to your account when you sign out.</p>
          </div>
        </div>
        {resume ? (
          <div className="flex flex-col justify-between gap-4 rounded-xl border p-4 sm:flex-row sm:items-center" style={{ borderColor: COLORS.border }}>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold" style={{ color: COLORS.textDark }}>{resume.original_filename}</p>
              <p className="mt-1 text-xs capitalize" style={{ color: COLORS.textSecondary }}>
                {resume.status.toLowerCase().replaceAll("_", " ")} · Uploaded {new Date(resume.uploaded_at).toLocaleDateString()}
              </p>
            </div>
            {resume.available ? (
              <button type="button" onClick={handleDownload} disabled={downloading} className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-semibold disabled:opacity-60" style={{ color: COLORS.textDark, borderColor: COLORS.border }}>
                {downloading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                Download CV
              </button>
            ) : (
              <span className="text-xs" style={{ color: COLORS.error }}>File unavailable</span>
            )}
          </div>
        ) : (
          <p className="rounded-xl border border-dashed p-5 text-sm" style={{ color: COLORS.textSecondary, borderColor: COLORS.border }}>
            You have not uploaded a CV yet. Upload one in CV Analyzer and it will be available here next time you sign in.
          </p>
        )}
      </section>
    </div>
  );
}
