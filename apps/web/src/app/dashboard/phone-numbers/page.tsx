'use client'

import { useEffect, useState } from 'react'
import { PhoneCall, Plus, Loader2, AlertCircle, Search, Trash2 } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function PhoneNumbersPage() {
  const [numbers, setNumbers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showProvisionModal, setShowProvisionModal] = useState(false)
  const [areaCode, setAreaCode] = useState('')
  const [availableNumbers, setAvailableNumbers] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  const [provisioning, setProvisioning] = useState<string | null>(null)

  useEffect(() => { loadNumbers() }, [])

  async function loadNumbers() {
    setLoading(true)
    setError('')
    try {
      const data = await ApiClient.getPhoneNumbers()
      setNumbers(Array.isArray(data) ? data : data.items || [])
    } catch (e: any) {
      setError(e.message || 'Failed to load phone numbers')
    } finally {
      setLoading(false)
    }
  }

  async function searchNumbers(e: React.FormEvent) {
    e.preventDefault()
    setSearching(true)
    try {
      const data = await ApiClient.searchPhoneNumbers(areaCode)
      setAvailableNumbers(data || [])
    } catch (e: any) {
      setError(e.message || 'Failed to search numbers')
    } finally {
      setSearching(false)
    }
  }

  async function provisionNumber(phoneNumber: string) {
    setProvisioning(phoneNumber)
    try {
      await ApiClient.provisionPhoneNumber(phoneNumber)
      setShowProvisionModal(false)
      loadNumbers()
    } catch (e: any) {
      setError(e.message || 'Failed to provision number')
    } finally {
      setProvisioning(null)
    }
  }

  async function releaseNumber(id: string) {
    if (!confirm('Are you sure you want to release this phone number?')) return
    try {
      await ApiClient.releasePhoneNumber(id)
      loadNumbers()
    } catch (e: any) {
      setError(e.message || 'Failed to release number')
    }
  }

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Phone Numbers</h2>
          <p className="text-sm text-slate-500">Manage your virtual phone numbers for inbound and outbound calling</p>
        </div>
        <button
          onClick={() => { setShowProvisionModal(true); setAvailableNumbers([]); setAreaCode('') }}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm"
        >
          <Plus className="h-4 w-4" /> Provision Number
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </div>
      )}

      {numbers.length === 0 && !error ? (
        <div className="text-center py-16 text-slate-500">
          <PhoneCall className="h-12 w-12 mx-auto mb-4 text-slate-300" />
          <p className="text-lg font-medium">No phone numbers yet</p>
          <p className="text-sm">Provision a new virtual number to start making AI calls.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {numbers.map((num) => (
            <div key={num.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
                    <PhoneCall className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold font-mono text-slate-900">{num.phone_number}</h3>
                    <p className="text-xs text-slate-500 capitalize">{num.capabilities?.join(', ') || 'Voice, SMS'}</p>
                  </div>
                </div>
              </div>
              <div className="pt-4 border-t border-slate-100 flex justify-between items-center text-sm">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${num.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                  {num.status}
                </span>
                <button onClick={() => releaseNumber(num.id)} className="text-rose-500 hover:text-rose-600 font-semibold text-xs flex items-center gap-1">
                  <Trash2 className="h-3.5 w-3.5" /> Release
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Provision Modal */}
      {showProvisionModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-8 max-w-lg w-full shadow-2xl space-y-6">
            <h3 className="text-xl font-bold text-slate-900">Provision Phone Number</h3>
            <form onSubmit={searchNumbers} className="flex gap-2">
              <input type="text" value={areaCode} onChange={(e) => setAreaCode(e.target.value)} placeholder="Area code (e.g. 415)" className="flex-1 px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
              <button type="submit" disabled={searching} className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm disabled:opacity-50">
                {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              </button>
            </form>

            <div className="space-y-3 max-h-60 overflow-y-auto">
              {availableNumbers.map((num: any) => (
                <div key={num.phone_number} className="flex items-center justify-between p-4 border border-slate-200 rounded-xl">
                  <span className="font-mono font-medium">{num.phone_number}</span>
                  <button onClick={() => provisionNumber(num.phone_number)} disabled={!!provisioning} className="px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 disabled:opacity-50">
                    {provisioning === num.phone_number ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Claim Number'}
                  </button>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-4 border-t border-slate-100">
              <button onClick={() => setShowProvisionModal(false)} className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
