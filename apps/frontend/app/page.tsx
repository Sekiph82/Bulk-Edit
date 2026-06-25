import Link from "next/link";

export default function HomePage() {
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl w-full text-center space-y-8">
        {/* Logo / Brand */}
        <div>
          <h1 className="text-6xl font-extrabold tracking-tight text-gray-900">
            Bulk-Edit
          </h1>
          <p className="mt-3 text-xl text-gray-500">
            The fastest way to bulk edit your Etsy listings.
          </p>
        </div>

        {/* Phase badge */}
        <div className="inline-flex items-center gap-2 bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm font-medium px-4 py-2 rounded-full">
          <span className="w-2 h-2 rounded-full bg-yellow-400" />
          Sprint 1 — Monorepo Skeleton
        </div>

        {/* Info cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
              Backend API
            </p>
            <code className="text-sm text-indigo-600 break-all">
              {backendUrl}/api/v1/health
            </code>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
              Status
            </p>
            <p className="text-sm font-semibold text-gray-700">
              Auth coming in Sprint 2
            </p>
          </div>
        </div>

        {/* CTA */}
        <Link
          href="/dashboard"
          className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-8 py-3 rounded-lg transition-colors"
        >
          Go to Dashboard →
        </Link>
      </div>
    </main>
  );
}
