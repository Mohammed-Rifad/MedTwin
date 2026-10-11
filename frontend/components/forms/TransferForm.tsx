"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import type { Admission } from "@/lib/types";

import { BedSelect } from "./BedSelect";
import { errorText, Field, FormFooter } from "./fields";

/** Move a patient to another free bed, e.g. from the ED to the ICU. */
export function TransferForm({
  admissionId,
  currentBed,
  onDone,
  onCancel,
}: {
  admissionId: number;
  currentBed: string;
  onDone: (admission: Admission) => void;
  onCancel: () => void;
}) {
  const [bedId, setBedId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const admission = await api<Admission>(`/api/hospital/admissions/${admissionId}/transfer/`, {
        method: "POST",
        body: JSON.stringify({ to_bed: Number(bedId) }),
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
      <p className="text-sm text-slate-600">
        Currently in <span className="font-medium text-slate-800">{currentBed}</span>. The old bed will be marked for cleaning.
      </p>
      <Field label="Move to">
        <BedSelect value={bedId} onChange={setBedId} exclude={currentBed} />
      </Field>
      <FormFooter error={error} busy={busy} submitLabel="Transfer patient" onCancel={onCancel} />
    </form>
  );
}
