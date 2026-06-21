import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Vanguard Vendor Management Platform",
  description: "Automated machine learning third party risk compliance architecture.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning // Prevents minor next-themes hydration log warnings
    >
      <body className="h-full bg-background text-foreground antialiased selection:bg-sky-500/20">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex h-screen w-screen overflow-hidden">
            {/* Content Panel Control Frame */}
            <div className="flex-1 flex flex-col min-w-0 bg-background relative">
              {/* Floating sidebar collapse/expand trigger handles */}
              <main className="flex-1 overflow-y-auto outline-none">
                {children}
              </main>
            </div>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}