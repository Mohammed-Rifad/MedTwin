"use client";

import { useState } from "react";

import { ErrorMessage } from "@/components/States";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ROLE_LABELS } from "@/lib/types";

const inputClass =
  "rounded-lg border border-slate-300 px-3 py-2 font-normal outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100";

export default function ProfilePage() {
  const { user } = useAuth();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!user) return null;

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setDone(false);
    if (newPassword !== repeat) {
      setError("The two new passwords don't match.");
      return;
    }
    setBusy(true);
    try {
      await api("/api/auth/me/password/", {
        method: "POST",
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
      });
      setDone(true);
      setOldPassword("");
      setNewPassword("");
      setRepeat("");
    } catch (err) {
      // Django explains what's wrong, e.g. "This password is too common."
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  const details: [string, string][] = [
    ["Username", user.username],
    ["Name", [user.first_name, user.last_name].filter(Boolean).join(" ") || "—"],
    ["Email", user.email || "—"],
    ["Role", ROLE_LABELS[user.role]],
  ];

  return (
    <div className="flex max-w-xl flex-col gap-6">
      <h1 className="text-2xl font-semibold text-slate-800">My profile</h1>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <dl className="grid grid-cols-[8rem_1fr] gap-y-2 text-sm">
          {details.map(([label, value]) => (
            <div key={label} className="contents">
              <dt className="text-slate-500">{label}</dt>
              <dd className="text-slate-800">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-slate-800">Change password</h2>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          {error && <ErrorMessage message={error} />}
          {done && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              Password changed.
            </div>
          )}
          <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
            Current password
            <input type="password" className={inputClass} value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} autoComplete="current-password" required />
          </label>
          <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
            New password
            <input type="password" className={inputClass} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} autoComplete="new-password" required />
          </label>
          <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
            New password again
            <input type="password" className={inputClass} value={repeat} onChange={(e) => setRepeat(e.target.value)} autoComplete="new-password" required />
          </label>
          <button
            type="submit"
            disabled={busy}
            className="self-start rounded-lg bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-700 disabled:opacity-60"
          >
            {busy ? "Saving…" : "Change password"}
          </button>
        </form>
      </section>
    </div>
  );
}
