import Script from "next/script";
import "./globals.css";
import { AuthProvider } from "../providers/AuthProvider";
import { ThemeProvider } from "../providers/ThemeProvider";

export const metadata = {
  title: "Sentinel AI — High-Availability AI Control Plane & Reverse Proxy",
  description: "Reverse proxy for LLM traffic. Intercept, scan, route, and cache model calls in real time.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <Script
          id="theme-initializer"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('sentinel_theme');
                  var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                  if (theme === 'light' || (!theme && !prefersDark)) {
                    document.documentElement.classList.add('light');
                  } else {
                    document.documentElement.classList.remove('light');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="bg-[var(--bg-primary)] text-[var(--text-primary)] antialiased min-h-screen selection:bg-indigo-500 selection:text-white" suppressHydrationWarning>
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}