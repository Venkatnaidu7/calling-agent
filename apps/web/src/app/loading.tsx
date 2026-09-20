import { Loader2 } from 'lucide-react'

export default function Loading() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 space-y-4">
      <Loader2 className="h-10 w-10 animate-spin text-indigo-600" />
      <p className="text-sm font-medium text-slate-500 animate-pulse">Loading Platform...</p>
    </div>
  )
}
