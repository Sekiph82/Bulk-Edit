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
  // Favicon/apple-icon/OG image are static PNGs at app/icon.png,
  // app/apple-icon.png, app/opengraph-image.png — Next.js file-convention
  // metadata picks these up automatically. Deliberately static, not
  // next/og ImageResponse: ImageResponse generation was tried and reverted
  // because it breaks `next build` on Windows (a known @vercel/og
  // local-font-resolution bug with Windows file:// URLs).
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
