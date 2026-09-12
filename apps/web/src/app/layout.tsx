import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AI Voice Calling SaaS Platform',
  description: 'Enterprise Multi-Tenant AI Voice Calling & Telephony Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased bg-slate-50 text-slate-900">{children}</body>
    </html>
  )
}
