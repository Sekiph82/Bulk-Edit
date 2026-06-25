import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 bg-gray-50">
      <div className="max-w-2xl w-full text-center space-y-8">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900">
            Bulk-Edit
          </h1>
          <p className="mt-3 text-lg text-gray-500">
            The fastest way to bulk edit your Etsy listings — safely, with preview and one-click revert.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/register"
            className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-8 py-3 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            Get Started Free
          </Link>
          <Link
            href="/login"
            className="inline-block border border-gray-300 text-gray-700 font-medium px-8 py-3 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-200"
          >
            Sign In
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left pt-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm font-semibold text-gray-800">Bulk edit at scale</p>
            <p className="text-xs text-gray-500 mt-1">Update titles, prices, tags, and more across hundreds of listings at once.</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm font-semibold text-gray-800">Preview before publish</p>
            <p className="text-xs text-gray-500 mt-1">See every change before it goes live. No surprises on your Etsy shop.</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm font-semibold text-gray-800">Revert any change</p>
            <p className="text-xs text-gray-500 mt-1">Automatic backup snapshots let you undo any bulk operation instantly.</p>
          </div>
        </div>
      </div>
    </main>
  );
}
