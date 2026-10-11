"use client";

import { ErrorMessage } from "../States";

export const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-normal outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100";

/** A label with its input underneath, plus an optional hint like "20–250". */
export function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
      <span>
        {label}
        {hint && <span className="ml-1.5 text-xs font-normal text-slate-400">{hint}</span>}
      </span>
      {children}
    </label>
  );
}

/** Error message (if any) and the Cancel / submit buttons at the bottom of every form. */
export function FormFooter({
  error,
  busy,
  submitLabel,
  onCancel,
  danger = false,
}: {
  error: string;
  busy: boolean;
  submitLabel: string;
  onCancel: () => void;
  danger?: boolean;
}) {
  return (
    <div className="flex flex-col gap-3 pt-2">
      {error && <ErrorMessage message={error} />}
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onCancel} className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">
          Cancel
        </button>
        <button
          type="submit"
          disabled={busy}
          className={`rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-60 ${
            danger ? "bg-red-600 hover:bg-red-700" : "bg-sky-600 hover:bg-sky-700"
          }`}
        >
          {busy ? "Saving…" : submitLabel}
        </button>
      </div>
    </div>
  );
}

/** Turns any error into a message for the user. */
export function errorText(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong. Please try again.";
}
