import Link from "next/link";

/** A spinner with a short message, shown while data is loading. */
export function Loading({ message = "Loading…" }: { message?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-slate-500" role="status">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-sky-600" />
      <span>{message}</span>
    </div>
  );
}

/** Shown when a list has nothing in it, so the screen never looks broken. */
export function EmptyState({ title, message }: { title: string; message?: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
      <p className="font-medium text-slate-700">{title}</p>
      {message && <p className="mt-1 text-sm text-slate-500">{message}</p>}
    </div>
  );
}

/** Shown when a user opens a screen their role isn't allowed to use (403). */
export function Forbidden() {
  return (
    <div className="mx-auto max-w-md py-16 text-center">
      <p className="text-5xl font-semibold text-slate-300">403</p>
      <h1 className="mt-3 text-xl font-semibold text-slate-800">You don&apos;t have access to this page</h1>
      <p className="mt-2 text-slate-500">This screen is for a different role. Ask an admin if you think you need it.</p>
      <Link href="/" className="mt-6 inline-block rounded-lg bg-sky-600 px-4 py-2 text-white hover:bg-sky-700">
        Back to the hospital
      </Link>
    </div>
  );
}

/** A red box for error messages from the API. */
export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
      {message}
    </div>
  );
}
