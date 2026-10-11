"use client";

import { useCallback, useEffect, useState } from "react";

import { FloorMap } from "@/components/FloorMap";
import { EmptyState, ErrorMessage, Loading } from "@/components/States";
import { api } from "@/lib/api";
import { useLiveEvent } from "@/lib/live";
import type { Bed, Paginated, Unit } from "@/lib/types";

/** The hospital floor map: every bed, coloured by status, updating live. */
export default function MapPage() {
  const [units, setUnits] = useState<Unit[] | null>(null);
  const [beds, setBeds] = useState<Bed[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    Promise.all([
      api<Paginated<Unit>>("/api/hospital/units/?page_size=100"),
      api<Paginated<Bed>>("/api/hospital/beds/?page_size=500"),
    ])
      .then(([unitPage, bedPage]) => {
        setUnits(unitPage.results);
        setBeds(bedPage.results);
        setError("");
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(load, [load]);

  // A bed changed somewhere in the hospital: swap in its new version.
  useLiveEvent<Bed>("bed_update", (changed) => {
    setBeds((current) => current && current.map((bed) => (bed.id === changed.id ? changed : bed)));
  });

  // After a history rebuild, lots has changed: fetch everything again.
  useLiveEvent("reload", load);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">Hospital map</h1>
        <p className="text-slate-500">Every bed, updating live. Hover over a bed to see who is in it.</p>
      </div>

      {error && <ErrorMessage message={error} />}
      {!error && (units === null || beds === null) && <Loading message="Loading the hospital…" />}
      {units?.length === 0 && (
        <EmptyState title="No units yet" message="Run seed_hospital or generate_history on the backend." />
      )}
      {units && beds && units.length > 0 && <FloorMap units={units} beds={beds} />}
    </div>
  );
}
