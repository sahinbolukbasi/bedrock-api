import "./globals.css";
import Navigation from "../components/Navigation";
import { ThemeProvider } from "../components/ThemeProvider";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AWS Bedrock AI Gateway | Enterprise Platform",
  description: "Enterprise multi-tenant API Gateway and Playground for AWS Bedrock models with zero AWS credential exposure, OpenAI-compatible APIs, and metered billing.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="flex flex-col min-h-screen bg-slate-950 text-slate-100 dark:bg-[#0b0f17] dark:text-gray-100 light:bg-[#f8fafc] light:text-slate-900 transition-colors">
        <ThemeProvider>
          <Navigation />
          <main className="flex-1 flex flex-col">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
