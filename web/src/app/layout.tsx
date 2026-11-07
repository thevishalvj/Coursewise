import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Coursewise",
  description: "Ask questions about UT Austin CS courses.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="h-full">{children}</body>
    </html>
  );
}
