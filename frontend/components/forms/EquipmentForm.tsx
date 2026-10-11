"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { EQUIPMENT_KIND_LABELS, type Bed, type Equipment, type EquipmentKind, type Paginated, type Unit } from "@/lib/types";

import { errorText, Field, FormFooter, inputClass } from "./fields";

/** Register a new device, or edit an existing one (Admin only). */
export function EquipmentForm({
  device,
  onDone,
  onCancel,
}: {
  device?: Equipment; // given when editing
  onDone: (device: Equipment) => void;
  onCancel: () => void;
}) {
  const [code, setCode] = useState(device?.code ?? "");
  const [kind, setKind] = useState<EquipmentKind>(device?.kind ?? "MONITOR");
  const [modelName, setModelName] = useState(device?.model_name ?? "");
  const [unitId, setUnitId] = useState(device?.unit ? String(device.unit) : "");
  const [bedId, setBedId] = useState(device?.bed ? String(device.bed) : "");
  const [installedOn, setInstalledOn] = useState(device?.installed_on ?? "");
  const [units, setUnits] = useState<Unit[]>([]);
  const [beds, setBeds] = useState<Bed[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<Paginated<Unit>>("/api/hospital/units/?page_size=100")
      .then((page) => setUnits(page.results))
      .catch(() => undefined);
  }, []);

  // A device can be attached to a bed in the chosen unit.
  useEffect(() => {
    if (!unitId) return;
    api<Paginated<Bed>>(`/api/hospital/beds/?unit=${unitId}&page_size=500`)
      .then((page) => setBeds(page.results))
      .catch(() => setBeds([]));
  }, [unitId]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const body = JSON.stringify({
      code,
      kind,
      model_name: modelName,
      unit: unitId ? Number(unitId) : null,
      bed: unitId && bedId ? Number(bedId) : null,
      installed_on: installedOn || null,
    });
    try {
      const saved = device
        ? await api<Equipment>(`/api/equipment/${device.id}/`, { method: "PATCH", body })
        : await api<Equipment>("/api/equipment/", { method: "POST", body });
      onDone(saved);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3">
        <Field label="Code" hint="e.g. VENT-09">
          <input className={inputClass} value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} required autoFocus />
        </Field>
        <Field label="Kind">
          <select className={inputClass} value={kind} onChange={(e) => setKind(e.target.value as EquipmentKind)}>
            {Object.entries(EQUIPMENT_KIND_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label="Model">
        <input className={inputClass} value={modelName} onChange={(e) => setModelName(e.target.value)} placeholder="e.g. Hamilton C6" />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Unit">
          <select
            className={inputClass}
            value={unitId}
            onChange={(e) => {
              setUnitId(e.target.value);
              setBedId("");
            }}
          >
            <option value="">Not assigned</option>
            {units.map((unit) => (
              <option key={unit.id} value={unit.id}>
                {unit.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Bed" hint="optional">
          <select className={inputClass} value={bedId} onChange={(e) => setBedId(e.target.value)} disabled={!unitId}>
            <option value="">Not attached to a bed</option>
            {beds.map((bed) => (
              <option key={bed.id} value={bed.id}>
                {bed.code}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label="Installed on" hint="optional">
        <input type="date" className={inputClass} value={installedOn} onChange={(e) => setInstalledOn(e.target.value)} />
      </Field>
      <FormFooter error={error} busy={busy} submitLabel={device ? "Save changes" : "Add device"} onCancel={onCancel} />
    </form>
  );
}
