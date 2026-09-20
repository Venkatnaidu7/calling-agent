'use client'

import { useEffect, useState } from 'react'
import { Users, Upload, ShieldAlert, Check, Plus, Loader2, AlertCircle, X, Trash2 } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function ContactsPage() {
  const [contacts, setContacts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [showImport, setShowImport] = useState(false)
  const [creating, setCreating] = useState(false)
  const [formData, setFormData] = useState({ first_name: '', last_name: '', phone_number: '', email: '', company: '' })
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => { loadContacts() }, [page])

  async function loadContacts() {
    setLoading(true)
    setError('')
    try {
      const data = await ApiClient.getContacts({ page: String(page), per_page: '20' })
      setContacts(Array.isArray(data) ? data : data.items || [])
      setTotal(data.total || 0)
    } catch (e: any) {
      setError(e.message || 'Failed to load contacts')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    try {
      await ApiClient.createContact(formData)
      setShowModal(false)
      setFormData({ first_name: '', last_name: '', phone_number: '', email: '', company: '' })
      loadContacts()
    } catch (e: any) {
      setError(e.message || 'Failed to create contact')
    } finally {
      setCreating(false)
    }
  }

  async function handleCsvImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      await ApiClient.importContactsCsv(formData)
      setShowImport(false)
      loadContacts()
    } catch (err: any) {
      setError(err.message || 'CSV import failed')
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this contact?')) return
    try {
      await ApiClient.deleteContact(id)
      loadContacts()
    } catch (e: any) {
      setError(e.message || 'Failed to delete contact')
    }
  }

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Contacts &amp; Audience</h2>
          <p className="text-sm text-slate-500">Manage phone contacts, lists, and Do-Not-Call (DNC) compliance</p>
        </div>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-sm shadow-sm cursor-pointer">
            <Upload className="h-4 w-4" /> Import CSV
            <input type="file" accept=".csv" className="hidden" onChange={handleCsvImport} />
          </label>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add Contact
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </div>
      )}

      {contacts.length === 0 && !error ? (
        <div className="text-center py-16 text-slate-500">
          <Users className="h-12 w-12 mx-auto mb-4 text-slate-300" />
          <p className="text-lg font-medium">No contacts yet</p>
          <p className="text-sm">Add contacts or import a CSV file to get started.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-6">Name</th>
                <th className="py-3.5 px-6">Phone Number</th>
                <th className="py-3.5 px-6">Company</th>
                <th className="py-3.5 px-6">DNC Status</th>
                <th className="py-3.5 px-6">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {contacts.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-4 px-6 font-medium text-slate-900">{c.first_name} {c.last_name}</td>
                  <td className="py-4 px-6 font-mono text-xs text-slate-700">{c.phone_number}</td>
                  <td className="py-4 px-6">{c.company || '—'}</td>
                  <td className="py-4 px-6">
                    {c.dnc_status ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                        <ShieldAlert className="h-3 w-3" /> Do Not Call
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <Check className="h-3 w-3" /> Eligible
                      </span>
                    )}
                  </td>
                  <td className="py-4 px-6">
                    <button onClick={() => handleDelete(c.id)} className="text-slate-400 hover:text-rose-500 transition-colors">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {total > 20 && (
            <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-sm">
              <span className="text-slate-500">Showing {contacts.length} of {total} contacts</span>
              <div className="flex gap-2">
                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 rounded-lg border border-slate-300 text-slate-700 font-semibold text-xs disabled:opacity-50">Previous</button>
                <button onClick={() => setPage(p => p + 1)} className="px-3 py-1 rounded-lg border border-slate-300 text-slate-700 font-semibold text-xs">Next</button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add Contact Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-900">Add Contact</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">First Name</label>
                  <input type="text" required value={formData.first_name} onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                    className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Last Name</label>
                  <input type="text" value={formData.last_name} onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                    className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number</label>
                <input type="tel" required value={formData.phone_number} onChange={(e) => setFormData({...formData, phone_number: e.target.value})}
                  placeholder="+1 (555) 000-0000"
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                <input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Company</label>
                <input type="text" value={formData.company} onChange={(e) => setFormData({...formData, company: e.target.value})}
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100">Cancel</button>
                <button type="submit" disabled={creating} className="px-4 py-2 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50">
                  {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Add Contact'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
