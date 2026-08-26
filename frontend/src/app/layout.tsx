import "./globals.css";
import Navigation from "../components/Navigation";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AWS Bedrock AI Gateway | OpenRouter-Equivalent Platform",
  description: "Enterprise multi-tenant API Gateway and Playground for AWS Bedrock models with zero AWS credential exposure, OpenAI-compatible APIs, and metered billing.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-gray-100 flex flex-col min-h-screen">
        <Navigation />
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
