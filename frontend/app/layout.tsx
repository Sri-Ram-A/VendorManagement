import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

// Provider & Layout Core Component Imports
import { ThemeProvider } from "@/components/theme-provider";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

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
          <SidebarProvider defaultOpen={true}>
            <div className="flex h-screen w-screen overflow-hidden">
              {/* Refactored App Sidebar Wrapper Hook */}
              <AppSidebar />
              
              {/* Content Panel Control Frame */}
              <div className="flex-1 flex flex-col min-w-0 bg-background relative">
                {/* Floating sidebar collapse/expand trigger handles */}
                <div className="absolute top-4.5 left-3 z-50 pointer-events-auto">
                  <SidebarTrigger className="h-7 w-7 rounded-sm border border-border bg-background shadow-none" />
                </div>
                
                <main className="flex-1 overflow-y-auto outline-none">
                  {children}
                </main>
              </div>
            </div>
          </SidebarProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}