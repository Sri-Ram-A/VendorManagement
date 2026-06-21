import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Cormorant_Garamond, DM_Sans, Geist } from "next/font/google";
import { cn } from "@/lib/utils";

// Display / heading font — editorial, refined, high contrast
const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

// Body font — geometric, clean, highly legible
const geist = Geist({ subsets: ['latin'], variable: '--font-sans' });


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
    <html lang="en" suppressHydrationWarning className={cn(cormorant.variable, "font-sans", geist.variable)}>
      <body className="font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}