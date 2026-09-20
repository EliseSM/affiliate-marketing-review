import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { QueryProvider } from "@/providers/QueryProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Affiliate Marketing Review",
  description: "Compliance review tool for affiliate marketing content",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-50 text-zinc-900">
        <QueryProvider>
          <header className="border-b border-zinc-200 bg-white">
            <nav className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-4">
              <Link href="/submissions" className="text-lg font-semibold">
                Marketing Review Tool
              </Link>
              <Link
                href="/submissions"
                className="text-sm text-zinc-600 hover:text-zinc-900"
              >
                Submissions
              </Link>
              <Link
                href="/upload"
                className="text-sm text-zinc-600 hover:text-zinc-900"
              >
                Upload
              </Link>
            </nav>
          </header>
          <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
            {children}
          </main>
        </QueryProvider>
      </body>
    </html>
  );
}
