import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/theme/ThemeProvider";
import StagingBanner from "@/components/StagingBanner";

export const metadata: Metadata = {
  metadataBase: new URL("https://bulkeditapp.com"),
  title: {
    default: "Bulk Edit App | Etsy Bulk Edit Tool",
    template: "%s",
  },
  description:
    "Bulk edit your Etsy listings at scale with AI-powered optimization tools.",
  openGraph: {
    siteName: "Bulk Edit App",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
  },
  // No favicon/OG image asset yet — next/og ImageResponse generation was
  // tried and reverted because it breaks `next build` on Windows (a known
  // @vercel/og local-font-resolution bug with Windows file:// URLs). See
  // docs/operations/PRODUCTION_LAUNCH_FOLLOWUPS.md for the follow-up plan.
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Anti-flash: resolve theme before React hydrates */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var p=localStorage.getItem('bulk-edit-theme')||'system';var t=p==='dark'?'dark':p==='light'?'light':(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.setAttribute('data-theme',t);}catch(e){}})();`,
          }}
        />
      </head>
      <body className="antialiased">
        <StagingBanner />
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
