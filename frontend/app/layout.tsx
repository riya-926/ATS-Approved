import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ATS-Approved - Resume Optimizer',
  description: 'Optimize your resume for ATS systems while preserving your original layout',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
