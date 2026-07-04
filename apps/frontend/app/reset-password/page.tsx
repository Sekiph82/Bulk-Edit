import type { Metadata } from "next";
import { Suspense } from "react";
import ResetPasswordContent from "@/components/auth/ResetPasswordContent";

export const metadata: Metadata = {
  title: "Reset Password — Bulk-Edit",
  robots: { index: false, follow: false },
};

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">Loading…</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
