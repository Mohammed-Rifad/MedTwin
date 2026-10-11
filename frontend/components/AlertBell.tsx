"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useLiveEvent } from "@/lib/live";
import { isSoundOn, setSoundOn } from "@/lib/sound";
import type { Alert, Paginated } from "@/lib/types";

/** The bell in the header: how many alerts nobody has responded to yet (status "open"). */
export function AlertBell() {
  const [openIds, setOpenIds] = useState<Set<number> | null>(null);

  const load = useCallback(() => {
    api<Paginated<Alert>>("/api/alerts/?status=OPEN&page_size=500")
      .then((page) => setOpenIds(new Set(page.results.map((alert) => alert.id))))
      .catch(() => undefined);
  }, []);

  useEffect(load, [load]);
  useLiveEvent("reload", load);

  useLiveEvent<Alert>("alert_update", (alert) => {
    setOpenIds((current) => {
      if (!current) return current;
      const next = new Set(current);
      if (alert.status === "OPEN") next.add(alert.id);
      else next.delete(alert.id);
      return next;
    });
  });

  const count = openIds?.size ?? 0;
  return (
    <Link
      href="/alerts"
      className="relative rounded-lg p-2 text-slate-600 hover:bg-slate-100"
      aria-label={`${count} open alerts`}
      title={`${count} open alerts`}
    >
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={2}>
        <path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
      </svg>
      {count > 0 && (
        <span className="absolute -right-0.5 -top-0.5 min-w-5 rounded-full bg-red-600 px-1.5 text-center text-[11px] font-semibold leading-5 text-white">
          {count > 99 ? "99+" : count}
        </span>
      )}
    </Link>
  );
}

/** A speaker button to turn the critical-alert sound on or off (remembered in this browser). */
export function SoundToggle() {
  const [on, setOn] = useState(() => isSoundOn());
  return (
    <button
      onClick={() => {
        setSoundOn(!on);
        setOn(!on);
      }}
      className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"
      aria-label={on ? "Mute alert sound" : "Turn alert sound on"}
      title={on ? "Alert sound on" : "Alert sound off"}
    >
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={2}>
        <path d="M11 5 6 9H2v6h4l5 4V5z" />
        {on ? <path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14" /> : <path d="m22 9-6 6M16 9l6 6" />}
      </svg>
    </button>
  );
}
