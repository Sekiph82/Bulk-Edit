import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/theme/ThemeProvider";
import StagingBanner from "@/components/StagingBanner";

export const metadata: Metadata = {
  title: "Bulk-Edit | Etsy Seller Tools",
  description:
    "Bulk edit your Etsy listings at scale with AI-powered optimization tools.",
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
