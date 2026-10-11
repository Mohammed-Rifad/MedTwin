"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import type { VitalReading } from "@/lib/types";

import { errorText, Field, FormFooter, inputClass } from "./fields";

// Allowed ranges match the backend's validators (hospital/models.py VitalReading).
const FIELDS = [
  { key: "heart_rate", label: "Heart rate", unit: "/min", min: 20, max: 250, step: 1 },
  { key: "spo2", label: "SpO₂", unit: "%", min: 50, max: 100, step: 1 },
  { key: "systolic_bp", label: "Systolic BP", unit: "mmHg", min: 40, max: 250, step: 1 },
  { key: "diastolic_bp", label: "Diastolic BP", unit: "mmHg", min: 20, max: 150, step: 1 },
  { key: "respiratory_rate", label: "Breathing rate", unit: "/min", min: 4, max: 60, step: 1 },
  { key: "temperature", label: "Temperature", unit: "°C", min: 30, max: 45, step: 0.1 },
] as const;

type Key = (typeof FIELDS)[number]["key"];

/** A nurse enters vital signs by hand. Leave a box empty if it wasn't measured. */
export function VitalsForm({
  admissionId,
  onDone,
  onCancel,
}: {
  admissionId: number;
  onDone: (reading: VitalReading) => void;
  onCancel: () => void;
}) {
  const [values, setValues] = useState<Record<Key, string>>({
    heart_rate: "",
    spo2: "",
    systolic_bp: "",
    diastolic_bp: "",
    respiratory_rate: "",
    temperature: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    const filled = Object.fromEntries(
      Object.entries(values)
        .filter(([, value]) => value !== "")
        .map(([key, value]) => [key, Number(value)]),
    );
    if (Object.keys(filled).length === 0) {
      setError("Enter at least one vital sign.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      const reading = await api<VitalReading>(`/api/hospital/admissions/${admissionId}/vitals/`, {
        method: "POST",
        body: JSON.stringify(filled),
      });
      onDone(reading);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3">
        {FIELDS.map((field, index) => (
          <Field key={field.key} label={field.label} hint={`${field.unit}, ${field.min}–${field.max}`}>
            <input
              type="number"
              inputMode="decimal"
              min={field.min}
              max={field.max}
              step={field.step}
              className={inputClass}
              value={values[field.key]}
              onChange={(event) => setValues({ ...values, [field.key]: event.target.value })}
              autoFocus={index === 0}
            />
          </Field>
        ))}
      </div>
      <p className="text-xs text-slate-500">Leave a box empty if it wasn&apos;t measured. Alerts are checked straight away.</p>
      <FormFooter error={error} busy={busy} submitLabel="Save vital signs" onCancel={onCancel} />
    </form>
  );
}
