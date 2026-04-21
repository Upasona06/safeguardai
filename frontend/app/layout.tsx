import type { Metadata } from "next";
import { Bricolage_Grotesque, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import { Providers } from "./providers";

const syne = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-syne",
  weight: ["400", "500", "600", "700", "800"],
});

const spaceMono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "SafeGuard AI — Next-Gen Cyber Safety Platform",
  description:
    "AI-powered platform to detect harmful content, protect children, and generate legally valid FIR reports instantly.",
  keywords: ["cybersafety", "AI", "FIR", "child protection", "toxicity detection"],
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const theme = localStorage.getItem('theme');
                if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark');
                }
              } catch (e) {}
            `,
          }}
        />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const extensionMessage = 'Could not establish connection. Receiving end does not exist.';
                window.addEventListener('unhandledrejection', function (event) {
                  const reason = event && event.reason;
                  const message =
                    typeof reason === 'string'
                      ? reason
                      : (reason && reason.message) || '';
                  const stack =
                    reason && typeof reason === 'object'
                      ? String(reason.stack || '')
                      : '';

                  if (message.includes(extensionMessage) || stack.includes('contentscript')) {
                    event.preventDefault();
                  }
                });
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body className={`${syne.variable} ${spaceMono.variable} font-syne antialiased`}>
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: "rgba(255, 252, 245, 0.95)",
                color: "#1e293b",
                border: "1px solid rgba(148, 163, 184, 0.35)",
                fontFamily: "var(--font-syne)",
                boxShadow: "0 14px 40px rgba(15, 23, 42, 0.16)",
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
