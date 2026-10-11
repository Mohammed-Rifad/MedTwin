import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="text-center">
        <p className="text-5xl font-semibold text-slate-300">404</p>
        <h1 className="mt-3 text-xl font-semibold text-slate-800">Page not found</h1>
        <p className="mt-2 text-slate-500">This page doesn&apos;t exist in MedTwin.</p>
        <Link href="/" className="mt-6 inline-block rounded-lg bg-sky-600 px-4 py-2 text-white hover:bg-sky-700">
          Back to the hospital
        </Link>
      </div>
    </main>
  );
}
