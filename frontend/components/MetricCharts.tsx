"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatDateTime, formatTime } from "@/lib/format";

export type Metric<T> = {
  key: keyof T & string;
  label: string;
  unit: string;
  color: string;
  second?: { key: keyof T & string; color: string }; // e.g. diastolic shown with systolic
};

type Reading = { recorded_at: string };

function latest<T extends Reading>(readings: T[], key: keyof T): number | null {
  for (let index = readings.length - 1; index >= 0; index -= 1) {
    const value = readings[index][key];
    if (typeof value === "number") return value;
  }
  return null;
}

/** For each metric: its latest value in large type, plus a small chart over the readings given (oldest first). */
export function MetricCharts<T extends Reading>({ readings, metrics, empty }: { readings: T[]; metrics: Metric<T>[]; empty: string }) {
  if (readings.length === 0) return <p className="text-sm text-slate-500">{empty}</p>;

  const data = readings.map((reading) => ({ ...reading, time: new Date(reading.recorded_at).getTime() }));
  const last = readings[readings.length - 1];

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-slate-500">
        Latest reading {formatDateTime(last.recorded_at)} · {readings.length} readings shown
      </p>
      {metrics.map((metric) => {
        const value = latest(readings, metric.key);
        const secondValue = metric.second ? latest(readings, metric.second.key) : null;
        if (value === null) return null; // e.g. pressure on a device that doesn't measure it
        return (
          <div key={metric.key} className="rounded-lg border border-slate-200 p-3">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-slate-500">{metric.label}</span>
              <span className="text-lg font-semibold" style={{ color: metric.color }}>
                {value}
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
                  <Line type="monotone" dataKey={metric.key} stroke={metric.color} strokeWidth={2} dot={false} connectNulls isAnimationActive={false} />
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
