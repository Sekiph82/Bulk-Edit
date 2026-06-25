import Link from "next/link";
import AnimatedProductDemo from "../components/AnimatedProductDemo";

const TRUST_ITEMS = [
  "Preview every change",
  "Backup snapshots",
  "Magic Revert",
  "Built for Etsy sellers",
];

const WORKFLOW_STEPS = ["Connect", "Sync", "Edit", "Preview", "Apply", "Revert"];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gray-50">
      {/* Nav */}
      <nav className="max-w-7xl mx-auto px-6 sm:px-8 py-5 flex items-center justify-between">
        <span className="text-xl font-extrabold text-gray-900 tracking-tight">Bulk-Edit</span>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-gray-200 rounded"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="text-sm bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 sm:px-8 pt-10 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left column */}
          <div className="space-y-8 max-w-xl">
            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-gray-900 leading-tight">
                Bulk editing for Etsy sellers, without the spreadsheet chaos.
              </h1>
              <p className="text-lg text-gray-500 leading-relaxed">
                Connect your Etsy shop, update listings in bulk, preview every change, publish safely, and revert when needed.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                href="/register"
                className="inline-flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-8 py-3 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300"
              >
                Get Started Free
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center justify-center border border-gray-300 text-gray-700 font-medium px-8 py-3 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-200"
              >
                Sign In
              </Link>
            </div>

            {/* Trust strip */}
            <div className="grid grid-cols-2 gap-x-4 gap-y-2">
              {TRUST_ITEMS.map((item) => (
                <div key={item} className="flex items-center gap-2 text-sm text-gray-600">
                  <svg
                    className="w-4 h-4 text-green-500 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {item}
                </div>
              ))}
            </div>
          </div>

          {/* Right column — animated demo */}
          <div className="w-full lg:max-w-lg lg:justify-self-end">
            <AnimatedProductDemo />
          </div>
        </div>
      </section>

      {/* Workflow strip */}
      <section className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 py-8">
          <div className="flex items-center justify-center gap-2 flex-wrap">
            {WORKFLOW_STEPS.map((step, i) => (
              <div key={step} className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700 px-3 py-1.5 bg-gray-50 rounded-lg border border-gray-200">
                  {step}
                </span>
                {i < WORKFLOW_STEPS.length - 1 && (
                  <svg
                    className="w-4 h-4 text-gray-400 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
