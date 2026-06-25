import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bulk-Edit | Etsy Seller Tools",
  description:
    "Bulk edit your Etsy listings at scale with AI-powered optimization tools.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
