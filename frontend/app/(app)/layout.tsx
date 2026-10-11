"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Sidebar } from "@/components/Sidebar";
import { Loading } from "@/components/States";
import { useAuth } from "@/lib/auth";
import { ROLE_LABELS } from "@/lib/types";

/** The shell around every logged-in screen: login check, sidebar menu and header. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, status, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "signed-out") router.replace("/login");
  }, [status, router]);

  if (status !== "signed-in" || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loading message="Checking your login…" />
      </div>
    );
  }

  const name = [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-end gap-4 border-b border-slate-200 bg-white px-6 py-3">
          <Link href="/profile" className="text-right hover:opacity-80">
            <p className="text-sm font-medium text-slate-800">{name}</p>
            <p className="text-xs text-slate-500">{ROLE_LABELS[user.role]}</p>
          </Link>
          <button
            onClick={logout}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
          >
            Log out
          </button>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
