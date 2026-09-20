'use client'

import Link from 'next/link'
import { AlertCircle } from 'lucide-react'

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-6">
      <div className="h-16 w-16 bg-rose-100 rounded-full flex items-center justify-center text-rose-600 mb-2">
        <AlertCircle className="h-8 w-8" />
      </div>
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-slate-900">Something went wrong</h2>
        <p className="text-slate-500 max-w-md mx-auto">
          {error.message || 'An unexpected error occurred while loading this page.'}
        </p>
      </div>
      <div className="flex gap-4">
        <button
          onClick={() => reset()}
          className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors shadow-sm"
        >
          Try again
        </button>
        <Link
          href="/dashboard"
          className="px-6 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm transition-colors"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  )
}
