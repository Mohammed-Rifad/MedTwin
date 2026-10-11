"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";

type NavItem = {
  label: string;
  href: string;
  roles: Role[]; // who can see it
  ready: boolean; // false until the screen is built (the plan day is shown instead)
  day?: number;
};

const ALL: Role[] = ["ADMIN", "DOCTOR", "NURSE"];

// Matches the screen list in docs/MedTwin-42-Day-Plan.md.
const NAV: { section: string; items: NavItem[] }[] = [
  {
    section: "Hospital",
    items: [
      { label: "Hospital map", href: "/", roles: ALL, ready: true },
      { label: "Dashboard", href: "/dashboard", roles: ALL, ready: false, day: 21 },
      { label: "Patients", href: "/patients", roles: ALL, ready: true },
      { label: "Emergency", href: "/emergency", roles: ALL, ready: true },
      { label: "Alerts", href: "/alerts", roles: ALL, ready: true },
      { label: "Equipment", href: "/equipment", roles: ALL, ready: false, day: 21 },
    ],
  },
  {
    section: "Planning",
    items: [
      { label: "What-if", href: "/what-if", roles: ["ADMIN"], ready: false, day: 33 },
      { label: "Analytics", href: "/analytics", roles: ["ADMIN", "DOCTOR"], ready: false, day: 34 },
    ],
  },
  {
    section: "Administration",
    items: [
      { label: "Hospital setup", href: "/settings/hospital", roles: ["ADMIN"], ready: false, day: 22 },
      { label: "Staff accounts", href: "/settings/staff", roles: ["ADMIN"], ready: false, day: 34 },
      { label: "Alert limits", href: "/settings/alert-limits", roles: ["ADMIN"], ready: false, day: 34 },
      { label: "Simulator", href: "/settings/simulator", roles: ["ADMIN"], ready: false, day: 33 },
      { label: "Audit log", href: "/settings/audit-log", roles: ["ADMIN"], ready: false, day: 34 },
    ],
  },
];

export function Sidebar() {
  const { hasRole } = useAuth();
  const pathname = usePathname();

  return (
    <nav className="flex w-60 shrink-0 flex-col gap-6 border-r border-slate-200 bg-white px-3 py-5">
      <Link href="/" className="px-3 text-xl font-semibold text-sky-700">
        MedTwin
      </Link>
      {NAV.map(({ section, items }) => {
        const visible = items.filter((item) => hasRole(...item.roles));
        if (visible.length === 0) return null; // e.g. nurses see no Administration section
        return (
          <div key={section}>
            <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{section}</p>
            <ul className="flex flex-col gap-0.5">
              {visible.map((item) => (
                <li key={item.href}>
                  {item.ready ? (
                    <Link
                      href={item.href}
                      className={`block rounded-lg px-3 py-2 text-sm ${
                        pathname === item.href || (item.href !== "/" && pathname.startsWith(`${item.href}/`))
                          ?"bg-sky-50 font-medium text-sky-700"
                          : "text-slate-700 hover:bg-slate-100"
                      }`}
                    >
                      {item.label}
                    </Link>
                  ) : (
                    <span
                      className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-slate-400"
                      title={`Coming on Day ${item.day}`}
                    >
                      {item.label}
                      <span className="text-[10px] uppercase">Day {item.day}</span>
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </nav>
  );
}
