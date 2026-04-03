import "./globals.css";

export const metadata = {
  title: "Self-Healing Pipeline Agent | AI-Powered Data Pipeline Builder",
  description:
    "Upload your CSV, describe your pipeline in plain English, and let AI build, simulate, and auto-heal a production-ready data pipeline.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
