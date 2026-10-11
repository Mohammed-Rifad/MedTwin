"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import type { Admission, EmergencyArrival } from "@/lib/types";

import { BedSelect } from "./BedSelect";
import { errorText, Field, FormFooter, inputClass } from "./fields";

/** Take a waiting emergency patient into a bed (an ED bay, the ICU or a ward). */
export function EmergencyAdmitForm({
  arrival,
  onDone,
  onCancel,
}: {
  arrival: EmergencyArrival;
  onDone: (admission: Admission) => void;
  onCancel: () => void;
}) {
  const [bedId, setBedId] = useState("");
  const [reason, setReason] = useState(arrival.complaint);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const admission = await api<Admission>(`/api/hospital/emergency/${arrival.id}/admit/`, {
        method: "POST",
        body: JSON.stringify({ bed: Number(bedId), reason }),
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
      <Field label="Bed">
        <BedSelect value={bedId} onChange={setBedId} />
      </Field>
      <Field label="Reason for admission">
        <input className={inputClass} value={reason} onChange={(e) => setReason(e.target.value)} required />
      </Field>
      <FormFooter error={error} busy={busy} submitLabel="Admit" onCancel={onCancel} />
    </form>
  );
}
