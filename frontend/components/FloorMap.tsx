"use client";

import type { Bed, Unit } from "@/lib/types";

// The backend lays the hospital out on a 1000 x 600 canvas (see seed_hospital).
const MAP_WIDTH = 1000;
const MAP_HEIGHT = 600;
const BED_WIDTH = 54;
const BED_HEIGHT = 34;

type BedLook = { fill: string; stroke: string; text: string; label: string };

/** How a bed looks on the map. Occupied beds are coloured by the patient's risk level. */
export function bedLook(bed: Bed): BedLook {
  if (!bed.is_active) return { fill: "#e2e8f0", stroke: "#cbd5e1", text: "#94a3b8", label: "Closed" };
  if (bed.status === "FREE") return { fill: "#ffffff", stroke: "#94a3b8", text: "#64748b", label: "Free" };
  if (bed.status === "CLEANING") return { fill: "#e0f2fe", stroke: "#7dd3fc", text: "#0369a1", label: "Cleaning" };
  switch (bed.current_admission?.risk_level) {
    case "HIGH":
      return { fill: "#ef4444", stroke: "#b91c1c", text: "#ffffff", label: "High risk" };
    case "MEDIUM":
      return { fill: "#f59e0b", stroke: "#b45309", text: "#ffffff", label: "Watch" };
    default:
      return { fill: "#10b981", stroke: "#047857", text: "#ffffff", label: "Stable" };
  }
}

const LEGEND: { label: string; fill: string; stroke: string }[] = [
  { label: "Stable", fill: "#10b981", stroke: "#047857" },
  { label: "Watch", fill: "#f59e0b", stroke: "#b45309" },
  { label: "High risk", fill: "#ef4444", stroke: "#b91c1c" },
  { label: "Free", fill: "#ffffff", stroke: "#94a3b8" },
  { label: "Cleaning", fill: "#e0f2fe", stroke: "#7dd3fc" },
  { label: "Closed", fill: "#e2e8f0", stroke: "#cbd5e1" },
];

type Props = {
  units: Unit[];
  beds: Bed[];
  selectedBedId?: number | null;
  onSelectBed?: (bed: Bed) => void;
};

export function FloorMap({ units, beds, selectedBedId, onSelectBed }: Props) {
  return (
    <div className="flex flex-col gap-3">
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-slate-50">
        <svg
          viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
          className="block h-auto w-full min-w-[640px]"
          role="img"
          aria-label="Hospital floor map"
        >
          {units.map((unit) => {
            const unitBeds = beds.filter((bed) => bed.unit === unit.id && bed.is_active);
            const occupied = unitBeds.filter((bed) => bed.status === "OCCUPIED").length;
            return (
              <g key={unit.id}>
                <rect
                  x={unit.map_x}
                  y={unit.map_y}
                  width={unit.map_width}
                  height={unit.map_height}
                  rx={12}
                  fill="#ffffff"
                  stroke="#cbd5e1"
                />
                <text x={unit.map_x + 16} y={unit.map_y + 26} fontSize={15} fontWeight={600} fill="#1e293b">
                  {unit.name}
                </text>
                <text
                  x={unit.map_x + unit.map_width - 16}
                  y={unit.map_y + 26}
                  fontSize={13}
                  textAnchor="end"
                  fill="#64748b"
                >
                  {occupied} / {unitBeds.length} beds
                </text>
              </g>
            );
          })}

          {beds.map((bed) => {
            const look = bedLook(bed);
            const selected = bed.id === selectedBedId;
            const patient = bed.current_admission?.patient_name;
            return (
              <g
                key={bed.id}
                onClick={onSelectBed ? () => onSelectBed(bed) : undefined}
                className={onSelectBed ? "cursor-pointer" : undefined}
              >
                <title>{`${bed.code} · ${look.label}${patient ? ` · ${patient}` : ""}`}</title>
                <rect
                  x={bed.map_x - BED_WIDTH / 2}
                  y={bed.map_y - BED_HEIGHT / 2}
                  width={BED_WIDTH}
                  height={BED_HEIGHT}
                  rx={6}
                  fill={look.fill}
                  stroke={selected ? "#0284c7" : look.stroke}
                  strokeWidth={selected ? 3 : 1.5}
                  strokeDasharray={bed.is_active ? undefined : "4 3"}
                />
                <text
                  x={bed.map_x}
                  y={bed.map_y + 4}
                  fontSize={12}
                  fontWeight={600}
                  textAnchor="middle"
                  fill={look.text}
                  pointerEvents="none"
                >
                  {bed.code.split("-").pop()}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <ul className="flex flex-wrap gap-4 text-sm text-slate-600">
        {LEGEND.map((item) => (
          <li key={item.label} className="flex items-center gap-1.5">
            <span className="h-3.5 w-5 rounded border" style={{ background: item.fill, borderColor: item.stroke }} />
            {item.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
