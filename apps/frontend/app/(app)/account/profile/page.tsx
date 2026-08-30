"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, getMe, updateProfile, ApiError, type CurrentUser } from "@/lib/api";

export default function AccountProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    getMe()
      .then((data) => {
        setUser(data.user);
        setFirstName(data.user.first_name ?? "");
        setLastName(data.user.last_name ?? "");
      })
      .catch((e) => setLoadError(e instanceof ApiError ? e.message : "Failed to load profile."))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setSaving(true);
    setSaveError(null);
    setSaved(false);
    try {
      const updated = await updateProfile({ first_name: firstName, last_name: lastName });
      setUser(updated);
      setFirstName(updated.first_name ?? "");
      setLastName(updated.last_name ?? "");
      setSaved(true);
    } catch (e) {
      setSaveError(e instanceof ApiError ? e.message : "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="flex justify-center py-16"><div className="w-6 h-6 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" /></div>;
  }

  if (loadError || !user) {
    return <p className="text-red-600 text-sm">{loadError ?? "Profile is unavailable right now."}</p>;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 max-w-md space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-gray-900 mb-1">Profile</h2>
        <p className="text-xs text-gray-500">Used for greetings and user-facing text across the app.</p>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
        <p className="text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">{user.email}</p>
      </div>

      <div>
        <label htmlFor="first_name" className="block text-xs font-medium text-gray-600 mb-1">First name</label>
        <input
          id="first_name"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          placeholder="First name"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
      </div>

      <div>
        <label htmlFor="last_name" className="block text-xs font-medium text-gray-600 mb-1">Last name</label>
        <input
          id="last_name"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          placeholder="Last name"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
      </div>

      {saveError && <p className="text-red-600 text-xs">{saveError}</p>}
      {saved && <p className="text-green-600 text-xs">Profile saved.</p>}

      <button
        type="button"
        onClick={handleSave}
        disabled={saving}
        className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
      >
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  );
}
