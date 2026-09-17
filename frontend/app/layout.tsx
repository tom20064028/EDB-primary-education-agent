import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "EDB Primary Education Agent",
  description:
    "An unofficial grounded Q&A and change-monitoring proof of concept for public EDB information.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-Hant">
      <body>{children}</body>
    </html>
  );
}

