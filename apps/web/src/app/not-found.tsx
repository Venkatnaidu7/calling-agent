import Link from 'next/link'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 space-y-6">
      <div className="text-center space-y-4">
        <h1 className="text-9xl font-extrabold text-slate-200">404</h1>
        <h2 className="text-2xl font-bold text-slate-900">Page not found</h2>
        <p className="text-slate-500 max-w-sm mx-auto">
          The page you are looking for doesn't exist or has been moved.
        </p>
      </div>
      <Link
        href="/dashboard"
        className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors shadow-sm"
      >
        Return to Dashboard
      </Link>
    </div>
  )
}
