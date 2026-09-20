'use client'

import { useEffect, useState } from 'react'
import { Shield, ShieldAlert, Check, Plus, Loader2, AlertCircle, X, Trash2, Upload } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function CompliancePage() {
  const [dncList, setDncList] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [phoneNumber, setPhoneNumber] = useState('')
  const [reason, setReason] = useState('')
  const [adding, setAdding] = useState(false)

  useEffect(() => { loadDnc() }, [])

  async function loadDnc() {
    setLoading(true)
    setError('')
    try {
      const data = await ApiClient.getDncList()
      setDncList(Array.isArray(data) ? data : data.items || [])
    } catch (e: any) {
      setError(e.message || 'Failed to load DNC list')
    } finally {
      setLoading(false)
    }
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    setAdding(true)
    try {
      await ApiClient.addToDnc({ phone_number: phoneNumber, reason })
      setShowAddModal(false)
      setPhoneNumber('')
      setReason('')
      loadDnc()
    } catch (e: any) {
      setError(e.message || 'Failed to add to DNC list')
    } finally {
      setAdding(false)
    }
  }

  async function handleRemove(num: string) {
    if (!confirm('Remove this number from the DNC list? It will be eligible for calls again.')) return
    try {
      await ApiClient.removeFromDnc(num)
      loadDnc()
    } catch (e: any) {
      setError(e.message || 'Failed to remove from DNC list')
    }
  }
  
  async function handleCsvImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      await ApiClient.importDncCsv(formData)
      loadDnc()
    } catch (err: any) {
      setError(err.message || 'CSV import failed')
    }
  }

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Compliance &amp; DNC</h2>
          <p className="text-sm text-slate-500">Manage your Do-Not-Call registry and TCPA calling windows</p>
        </div>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-sm shadow-sm cursor-pointer">
            <Upload className="h-4 w-4" /> Import CSV
            <input type="file" accept=".csv" className="hidden" onChange={handleCsvImport} />
          </label>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add to DNC
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </div>
      )}

      {dncList.length === 0 && !error ? (
        <div className="text-center py-16 text-slate-500">
          <ShieldAlert className="h-12 w-12 mx-auto mb-4 text-slate-300" />
          <p className="text-lg font-medium">DNC list is empty</p>
          <p className="text-sm">Add numbers to prevent them from being called.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-6">Phone Number</th>
                <th className="py-3.5 px-6">Reason</th>
                <th className="py-3.5 px-6">Added At</th>
                <th className="py-3.5 px-6">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {dncList.map((entry, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-4 px-6 font-mono font-medium text-slate-900">{entry.phone_number}</td>
                  <td className="py-4 px-6">{entry.reason || 'Requested'}</td>
                  <td className="py-4 px-6">{entry.created_at ? new Date(entry.created_at).toLocaleDateString() : '—'}</td>
                  <td className="py-4 px-6">
                    <button onClick={() => handleRemove(entry.phone_number)} className="text-slate-400 hover:text-emerald-500 transition-colors" title="Remove from DNC">
                      <Check className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-900">Add to DNC</h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleAdd} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number</label>
                <input type="tel" required value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} placeholder="+1 (555) 000-0000"
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Reason</label>
                <input type="text" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Customer request"
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowAddModal(false)} className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100">Cancel</button>
                <button type="submit" disabled={adding} className="px-4 py-2 rounded-xl text-sm font-semibold bg-rose-600 hover:bg-rose-700 text-white disabled:opacity-50">
                  {adding ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Block Number'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
