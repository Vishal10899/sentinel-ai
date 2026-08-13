"use client";

import { useEffect, useState } from "react";
import { User, Settings, Save, Globe, Clock, ShieldCheck, RefreshCw } from "lucide-react";
import { AppShell, PageTitle } from "../../components/shell";
import { Button, ErrorCard, LoadingCard, Toast } from "../../components/ui";
import { api } from "../../lib/api";

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  const [formData, setFormData] = useState({
    display_name: "",
    avatar_url: "",
    timezone: "UTC",
    language: "en",
  });

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await api.getUserProfile();
      setProfile(data);
      if (data) {
        setFormData({
          display_name: data.display_name || "",
          avatar_url: data.avatar_url || "",
          timezone: data.timezone || "UTC",
          language: data.language || "en",
        });
      }
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      const updated = await api.updateUserProfile(formData);
      setProfile(updated);
      setToast({ type: "success", message: "User profile updated successfully!" });
    } catch (err) {
      setToast({ type: "error", message: `Failed: ${err.message}` });
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageTitle
          title="User Profile & Directory Preferences"
          subtitle="Manage your personal profile, avatar, timezone, and language preferences across organizations."
        />

        {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}

        {loading ? (
          <LoadingCard title="Loading User Directory Profile..." />
        ) : error ? (
          <ErrorCard title="Profile Load Error" message={error} onRetry={loadProfile} />
        ) : (
          <form onSubmit={handleSaveProfile} className="surface rounded-2xl border border-white/10 p-6 bg-[#111827] shadow-xl max-w-xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <User className="h-4 w-4 text-indigo-400" /> Account Directory Profile
            </h3>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Display Name</label>
              <input
                type="text"
                required
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Avatar Image URL</label>
              <input
                type="url"
                value={formData.avatar_url}
                onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
                placeholder="https://example.com/avatar.png"
                className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Timezone</label>
                <select
                  value={formData.timezone}
                  onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                >
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">America/New_York (EST)</option>
                  <option value="Europe/London">Europe/London (GMT)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Language</label>
                <select
                  value={formData.language}
                  onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-xs text-white outline-none focus:border-indigo-500"
                >
                  <option value="en">English (en)</option>
                  <option value="es">Spanish (es)</option>
                  <option value="fr">French (fr)</option>
                  <option value="de">German (de)</option>
                </select>
              </div>
            </div>

            <Button type="submit" className="w-full">
              <Save className="h-4 w-4" /> Save Profile Changes
            </Button>
          </form>
        )}
      </div>
    </AppShell>
  );
}
