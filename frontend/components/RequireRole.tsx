"use client";

import { useAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";

import { Forbidden } from "./States";

/** Wrap a page in this to allow only some roles; everyone else sees the 403 page. */
export function RequireRole({ roles, children }: { roles: Role[]; children: React.ReactNode }) {
  const { hasRole } = useAuth();
  return hasRole(...roles) ? <>{children}</> : <Forbidden />;
}
