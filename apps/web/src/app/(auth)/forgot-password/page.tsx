'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ApiClient } from '@/lib/api'
import { Loader2, Mail, CheckCircle, AlertCircle } from 'lucide-react'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setStatus('loading')
    try {
      await ApiClient.forgotPassword(email)
      setStatus('success')
      setMessage('If an account exists, a password reset link has been sent to your email.')
    } catch (err: any) {
      setStatus('error')
      setMessage(err.message || 'Failed to send reset email.')
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="text-center text-3xl font-extrabold text-slate-900">Reset your password</h2>
        <p className="mt-2 text-center text-sm text-slate-600">
          Or <Link href="/login" className="font-medium text-indigo-600 hover:text-indigo-500">return to login</Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {status === 'success' ? (
            <div className="text-center space-y-4">
              <CheckCircle className="h-12 w-12 text-emerald-500 mx-auto" />
              <p className="text-sm font-medium text-slate-700">{message}</p>
            </div>
          ) : (
            <form className="space-y-6" onSubmit={handleSubmit}>
              {status === 'error' && (
                <div className="p-3 bg-rose-50 text-rose-700 rounded-lg text-sm flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0" /> {message}
                </div>
              )}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-700">Email address</label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full pl-10 sm:text-sm border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 h-10 border"
                    placeholder="you@example.com"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={status === 'loading'}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {status === 'loading' ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Send reset link'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
