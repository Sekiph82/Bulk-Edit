"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function ShopsRedirect() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Preserves the Etsy OAuth callback's ?connected=true / ?error=... query
    // string, since the backend redirect target still points here.
    const qs = searchParams.toString();
    router.replace(`/account/connected-shops${qs ? `?${qs}` : ""}`);
  }, []);

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <p className="text-gray-500 text-sm">Redirecting to Account…</p>
    </main>
  );
}

export default function ShopsPage() {
  return (
    <Suspense fallback={<main className="min-h-screen flex items-center justify-center bg-gray-50"><p className="text-gray-500 text-sm">Redirecting to Account…</p></main>}>
      <ShopsRedirect />
    </Suspense>
  );
}
