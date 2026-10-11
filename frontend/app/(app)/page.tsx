"use client";

import { useEffect, useState } from "react";

import { EmptyState, ErrorMessage, Loading } from "@/components/States";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Paginated, Unit } from "@/lib/types";

/** Home screen. Shows unit occupancy for now; the live floor map replaces this on Day 17. */
export default function HomePage() {
  const { user } = useAuth();
  const [units, setUnits] = useState<Unit[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Paginated<Unit>>("/api/hospital/units/")
      .then((page) => setUnits(page.results))
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">Welcome, {user?.first_name || user?.username}</h1>
        <p className="text-slate-500">The live hospital floor map arrives on Day 17. For now, here is each unit&apos;s occupancy.</p>
      </div>

      {error && <ErrorMessage message={error} />}
      {!error && units === null && <Loading message="Loading units…" />}
      {units?.length === 0 && (
        <EmptyState title="No units yet" message="Run seed_hospital or generate_history on the backend." />
      )}
      {units && units.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {units.map((unit) => {
            const percent = unit.capacity ? Math.round((100 * unit.occupied) / unit.capacity) : 0;
            return (
              <div key={unit.id} className="rounded-xl border border-slate-200 bg-white p-5">
                <p className="text-sm text-slate-500">{unit.name}</p>
                <p className="mt-1 text-3xl font-semibold text-slate-800">
                  {unit.occupied}
                  <span className="text-lg font-normal text-slate-400"> / {unit.capacity} beds</span>
                </p>
                <div className="mt-3 h-2 rounded-full bg-slate-100">
                  <div
                    className={`h-2 rounded-full ${percent >= 100 ? "bg-red-500" : percent >= 85 ? "bg-amber-500" : "bg-emerald-500"}`}
                    style={{ width: `${Math.min(percent, 100)}%` }}
                  />
                </div>
                <p className="mt-1 text-xs text-slate-500">{percent}% full</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
