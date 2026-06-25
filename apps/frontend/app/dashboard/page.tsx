import Link from "next/link";

const placeholderFeatures = [
  {
    title: "Connect Etsy Shop",
    description: "OAuth connection — Sprint 4",
    icon: "🔗",
  },
  {
    title: "Sync Listings",
    description: "Full & incremental sync — Sprint 5",
    icon: "🔄",
  },
  {
    title: "Bulk Edit",
    description: "Titles, tags, prices & more — Sprint 7",
    icon: "✏️",
  },
  {
    title: "AI Tools",
    description: "Title optimizer, tag generator — Sprint 13",
    icon: "🤖",
  },
  {
    title: "Magic Revert",
    description: "Undo bulk changes — Sprint 9",
    icon: "↩️",
  },
  {
    title: "Media Library",
    description: "Photo & video management — Sprint 10",
    icon: "🖼️",
  },
];

export default function DashboardPage() {
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8100";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <nav className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <Link
          href="/"
          className="text-xl font-extrabold text-gray-900 hover:text-indigo-600 transition-colors"
        >
          Bulk-Edit
        </Link>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">Sprint 1 Skeleton</span>
          <span className="inline-flex items-center gap-1.5 bg-indigo-50 text-indigo-700 text-xs font-semibold px-3 py-1 rounded-full border border-indigo-100">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
            No Auth Yet
          </span>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-8 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Placeholder — authentication and real data arrive in Sprint 2+
          </p>
        </div>

        {/* Feature grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-10">
          {placeholderFeatures.map((feature) => (
            <div
              key={feature.title}
              className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 flex flex-col gap-2"
            >
              <span className="text-2xl">{feature.icon}</span>
              <h3 className="font-semibold text-gray-800">{feature.title}</h3>
              <p className="text-sm text-gray-400">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Backend health endpoints */}
        <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-6">
          <p className="text-sm font-semibold text-indigo-800 mb-2">
            Backend Health Endpoints
          </p>
          <div className="space-y-1">
            {["/api/v1/health", "/api/v1/health/db", "/api/v1/health/redis"].map(
              (path) => (
                <div key={path} className="flex items-center gap-2">
                  <code className="text-xs text-indigo-600">
                    {backendUrl}
                    {path}
                  </code>
                </div>
              )
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
