"use client";

import { useEffect, useState } from "react";

import { api } from "./api";
import { useLiveEvent } from "./live";
import type { Paginated, VitalReading } from "./types";

const HISTORY = 200; // enough for 2 days in the ICU (a reading every 15 minutes)

/** The latest vital signs for one admission, oldest first (ready for a chart), updating live. */
export function useVitals(admissionId: number | null) {
  const [readings, setReadings] = useState<VitalReading[] | null>(null);
  const [error, setError] = useState("");
  const [loadedFor, setLoadedFor] = useState<number | null>(null);

  useEffect(() => {
    if (admissionId === null) return;
    let cancelled = false;
    api<Paginated<VitalReading>>(`/api/hospital/admissions/${admissionId}/vitals/?page_size=${HISTORY}`)
      .then((page) => {
        if (cancelled) return;
        setReadings([...page.results].reverse()); // the API sends newest first
        setLoadedFor(admissionId);
        setError("");
      })
      .catch((err: Error) => !cancelled && setError(err.message));
    return () => {
      cancelled = true;
    };
  }, [admissionId]);

  // New readings arrive live: add the ones for this admission to the end.
  useLiveEvent<VitalReading & { admission: number }>("vitals", (reading) => {
    if (reading.admission !== admissionId) return;
    setReadings((current) => current && [...current, reading].slice(-HISTORY));
  });

  // While a different admission is still loading, don't show the previous patient's readings.
  const current = loadedFor === admissionId ? readings : null;
  return { readings: admissionId === null ? null : current, error };
}
