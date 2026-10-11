"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatDateTime, formatTime } from "@/lib/format";
import type { VitalReading } from "@/lib/types";

type Metric = {
  key: keyof VitalReading;
  label: string;
  unit: string;
  color: string;
  second?: { key: keyof VitalReading; color: string }; // e.g. diastolic shown with systolic
};

const METRICS: Metric[] = [
  { key: "heart_rate", label: "Heart rate", unit: "/min", color: "#ef4444" },
  { key: "spo2", label: "SpO₂", unit: "%", color: "#0284c7" },
  { key: "respiratory_rate", label: "Breathing", unit: "/min", color: "#7c3aed" },
  { key: "systolic_bp", label: "Blood pressure", unit: "mmHg", color: "#d97706", second: { key: "diastolic_bp", color: "#f59e0b" } },
  { key: "temperature", label: "Temperature", unit: "°C", color: "#059669" },
];

function latest(readings: VitalReading[], key: keyof VitalReading): number | null {
  for (let index = readings.length - 1; index >= 0; index -= 1) {
    const value = readings[index][key];
    if (typeof value === "number") return value;
  }
  return null;
}

/** Latest values as tiles, plus a small chart per vital sign over the readings given. */
export function VitalsChart({ readings }: { readings: VitalReading[] }) {
  if (readings.length === 0) {
    return <p className="text-sm text-slate-500">No vital signs recorded yet.</p>;
  }

  const data = readings.map((reading) => ({ ...reading, time: new Date(reading.recorded_at).getTime() }));
  const last = readings[readings.length - 1];

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-slate-500">
        Latest reading {formatDateTime(last.recorded_at)} · {readings.length} readings shown
      </p>
      {METRICS.map((metric) => {
        const value = latest(readings, metric.key);
        const secondValue = metric.second ? latest(readings, metric.second.key) : null;
        return (
          <div key={metric.key} className="rounded-lg border border-slate-200 p-3">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-slate-500">{metric.label}</span>
              <span className="text-lg font-semibold" style={{ color: metric.color }}>
                {value ?? "—"}
                {secondValue !== null && `/${secondValue}`}
                <span className="ml-1 text-xs font-normal text-slate-400">{metric.unit}</span>
              </span>
            </div>
            <div className="h-16">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                  <XAxis dataKey="time" type="number" scale="time" domain={["dataMin", "dataMax"]} hide />
                  <YAxis domain={["auto", "auto"]} hide />
                  <Tooltip
                    labelFormatter={(time) => formatTime(new Date(Number(time)).toISOString())}
                    formatter={(reading) => [`${reading} ${metric.unit}`, metric.label]}
                    contentStyle={{ fontSize: 12 }}
                  />
                  <Line
                    type="monotone"
                    dataKey={metric.key}
                    stroke={metric.color}
                    strokeWidth={2}
                    dot={false}
                    connectNulls
                    isAnimationActive={false}
                  />
                  {metric.second && (
                    <Line
                      type="monotone"
                      dataKey={metric.second.key}
                      stroke={metric.second.color}
                      strokeWidth={1.5}
                      strokeDasharray="4 3"
                      dot={false}
                      connectNulls
                      isAnimationActive={false}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      })}
    </div>
  );
}
