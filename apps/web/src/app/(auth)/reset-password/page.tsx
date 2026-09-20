'use client'

import { useState, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { ApiClient } from '@/lib/api'
import { Loader2, Lock, AlertCircle } from 'lucide-react'

function ResetPasswordForm() {
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')
  
  const searchParams = useSearchParams()
  const token = searchParams.get('token')
  const router = useRouter()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    
    if (!token) {
      setStatus('error')
      setMessage('Invalid or missing reset token.')
      return
    }
    
    if (password !== confirmPassword) {
      setStatus('error')
      setMessage('Passwords do not match.')
      return
    }

    setStatus('loading')
    try {
      await ApiClient.resetPassword(token, password)
      setStatus('success')
      setMessage('Password successfully reset. You can now log in.')
      setTimeout(() => router.push('/login'), 2000)
    } catch (err: any) {
      setStatus('error')
      setMessage(err.message || 'Failed to reset password.')
    }
  }

  return (
    <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
      {status === 'success' ? (
        <div className="text-center space-y-4">
          <p className="text-sm font-medium text-emerald-600">{message}</p>
          <Loader2 className="h-5 w-5 animate-spin mx-auto text-emerald-600" />
        </div>
      ) : (
        <form className="space-y-6" onSubmit={handleSubmit}>
          {status === 'error' && (
            <div className="p-3 bg-rose-50 text-rose-700 rounded-lg text-sm flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" /> {message}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-slate-700">New Password</label>
            <div className="mt-1 relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-slate-400" />
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full pl-10 sm:text-sm border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 h-10 border"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Confirm Password</label>
            <div className="mt-1 relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-slate-400" />
              </div>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="block w-full pl-10 sm:text-sm border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 h-10 border"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={status === 'loading'}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {status === 'loading' ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Reset Password'}
          </button>
        </form>
      )}
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md mb-8">
        <h2 className="text-center text-3xl font-extrabold text-slate-900">Set new password</h2>
      </div>
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Suspense fallback={<div className="flex justify-center"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  )
}
