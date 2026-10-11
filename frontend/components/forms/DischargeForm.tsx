"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import type { Admission } from "@/lib/types";

import { errorText, Field, FormFooter, inputClass } from "./fields";

/** A doctor ends the stay. Asks for confirmation, because this can't be undone. */
export function DischargeForm({
  admissionId,
  patientName,
  onDone,
  onCancel,
}: {
  admissionId: number;
  patientName: string;
  onDone: (admission: Admission) => void;
  onCancel: () => void;
}) {
  const [outcome, setOutcome] = useState("HOME");
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!confirmed) {
      setError("Please tick the box to confirm.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      const admission = await api<Admission>(`/api/hospital/admissions/${admissionId}/discharge/`, {
        method: "POST",
        body: JSON.stringify({ outcome }),
      });
      onDone(admission);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <Field label="Outcome">
        <select className={inputClass} value={outcome} onChange={(event) => setOutcome(event.target.value)}>
          <option value="HOME">Discharged home</option>
          <option value="TRANSFERRED">Transferred to another facility</option>
          <option value="DECEASED">Deceased</option>
        </select>
      </Field>
      <label className="flex items-start gap-2 text-sm text-slate-700">
        <input type="checkbox" className="mt-0.5" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
        <span>
          I confirm that <span className="font-medium">{patientName}</span> is leaving. This ends the stay and can&apos;t be undone.
        </span>
      </label>
      <FormFooter error={error} busy={busy} submitLabel="Discharge" onCancel={onCancel} danger />
    </form>
  );
}
