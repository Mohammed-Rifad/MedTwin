"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Bed, Paginated } from "@/lib/types";

import { inputClass } from "./fields";

/** A dropdown of free, open beds, grouped by unit. */
export function BedSelect({
  value,
  onChange,
  exclude,
}: {
  value: string;
  onChange: (bedId: string) => void;
  exclude?: string; // a bed code to leave out, e.g. the patient's current bed
}) {
  const [beds, setBeds] = useState<Bed[] | null>(null);

  useEffect(() => {
    api<Paginated<Bed>>("/api/hospital/beds/?status=FREE&is_active=true&page_size=500")
      .then((page) => setBeds(page.results.filter((bed) => bed.code !== exclude)))
      .catch(() => setBeds([]));
  }, [exclude]);

  if (beds === null) return <p className="text-sm text-slate-500">Loading free beds…</p>;
  if (beds.length === 0) return <p className="text-sm text-amber-700">There are no free beds right now.</p>;

  const units = [...new Set(beds.map((bed) => bed.unit_code))];
  return (
    <select className={inputClass} value={value} onChange={(event) => onChange(event.target.value)} required>
      <option value="">Choose a free bed…</option>
      {units.map((unit) => (
        <optgroup key={unit} label={unit}>
          {beds
            .filter((bed) => bed.unit_code === unit)
            .map((bed) => (
              <option key={bed.id} value={bed.id}>
                {bed.code}
              </option>
            ))}
        </optgroup>
      ))}
    </select>
  );
}
