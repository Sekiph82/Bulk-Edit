import type { Metadata } from "next";
import ForgotPasswordContent from "@/components/auth/ForgotPasswordContent";

export const metadata: Metadata = {
  title: "Forgot Password — Bulk-Edit",
  robots: { index: false, follow: false },
};

export default function ForgotPasswordPage() {
  return <ForgotPasswordContent />;
}
