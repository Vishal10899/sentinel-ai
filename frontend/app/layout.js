import "./globals.css";
import { AuthProvider } from "../providers/AuthProvider";

export const metadata = {
  title: "Sentinel AI — Intelligent model routing",
  description: "Route every AI workload with confidence.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-[#080b12] text-slate-100 antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}