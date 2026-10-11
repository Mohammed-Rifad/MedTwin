"use client";

import { useHospitalClock, useLiveStatus } from "@/lib/live";

const timeFormat = new Intl.DateTimeFormat(undefined, {
  weekday: "short",
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

/** Header badge: is the live connection up, and what time is it in the hospital? */
export function LiveIndicator() {
  const status = useLiveStatus();
  const clock = useHospitalClock();

  const dot = status === "live" ? "bg-emerald-500" : status === "reconnecting" ? "bg-amber-500" : "bg-slate-300";
  const label = status === "live" ? "Live" : status === "reconnecting" ? "Reconnecting" : "Connecting";

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="flex items-center gap-1.5 text-slate-600">
        <span className={`h-2.5 w-2.5 rounded-full ${dot} ${status === "live" ? "animate-pulse" : ""}`} />
        {label}
      </span>
      {clock && (
        <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-xs text-slate-700" title="Hospital time">
          {timeFormat.format(new Date(clock.hospital_time))}
          <span className="ml-2 text-slate-500">{clock.running ? `${clock.speed}×` : "paused"}</span>
        </span>
      )}
    </div>
  );
}

/** A banner across the top while the live connection is down. */
export function ConnectionBanner() {
  const status = useLiveStatus();
  if (status !== "reconnecting") return null;
  return (
    <div className="border-b border-amber-200 bg-amber-50 px-6 py-2 text-sm text-amber-800" role="status">
      Connection lost. Reconnecting… The screen will update again automatically.
    </div>
  );
}
