"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function BillingRedirect() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const qs = searchParams.toString();
    router.replace(`/account/billing${qs ? `?${qs}` : ""}`);
  }, []);

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <p className="text-gray-500 text-sm">Redirecting to Account…</p>
    </main>
  );
}

export default function BillingPage() {
  return (
    <Suspense fallback={<main className="min-h-screen flex items-center justify-center bg-gray-50"><p className="text-gray-500 text-sm">Redirecting to Account…</p></main>}>
      <BillingRedirect />
    </Suspense>
  );
}
