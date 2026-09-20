'use client'

import { useEffect, useState } from 'react'
import { Megaphone, Play, Pause, Plus, Clock, Loader2, AlertCircle, X } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({ name: '', description: '', agent_id: '' })
  const [creating, setCreating] = useState(false)

  useEffect(() => { loadCampaigns() }, [])

  async function loadCampaigns() {
    setLoading(true)
    setError('')
    try {
      const data = await ApiClient.getCampaigns()
      setCampaigns(Array.isArray(data) ? data : data.items || [])
    } catch (e: any) {
      setError(e.message || 'Failed to load campaigns')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    try {
      await ApiClient.createCampaign(formData)
      setShowModal(false)
      setFormData({ name: '', description: '', agent_id: '' })
      loadCampaigns()
    } catch (e: any) {
      setError(e.message || 'Failed to create campaign')
    } finally {
      setCreating(false)
    }
  }

  async function toggleCampaign(camp: any) {
    const newStatus = camp.status === 'running' ? 'paused' : 'running'
    try {
      await ApiClient.updateCampaign(camp.id, { status: newStatus })
      loadCampaigns()
    } catch (e: any) {
      setError(e.message || 'Failed to update campaign')
    }
  }

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Outbound Campaigns</h2>
          <p className="text-sm text-slate-500">Automate high-volume outbound calling with compliance safeguards</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm transition-all"
        >
          <Plus className="h-4 w-4" /> New Campaign
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </div>
      )}

      {campaigns.length === 0 && !error ? (
        <div className="text-center py-16 text-slate-500">
          <Megaphone className="h-12 w-12 mx-auto mb-4 text-slate-300" />
          <p className="text-lg font-medium">No campaigns yet</p>
          <p className="text-sm">Create your first outbound campaign to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {campaigns.map((camp) => (
            <div key={camp.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
                    <Megaphone className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">{camp.name}</h3>
                    <p className="text-xs text-slate-500">{camp.description || 'No description'}</p>
                  </div>
                </div>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    camp.status === 'running'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : camp.status === 'completed'
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'bg-amber-50 text-amber-700 border border-amber-200'
                  }`}
                >
                  {camp.status}
                </span>
              </div>

              {camp.total_contacts > 0 && (
                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-600 mb-2">
                    <span>Progress: {camp.completed_contacts || 0} / {camp.total_contacts} completed</span>
                    <span>{Math.round(((camp.completed_contacts || 0) / camp.total_contacts) * 100)}%</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-full bg-indigo-600 rounded-full transition-all"
                      style={{ width: `${((camp.completed_contacts || 0) / camp.total_contacts) * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5 text-slate-400" />
                  {camp.created_at ? new Date(camp.created_at).toLocaleDateString() : 'N/A'}
                </span>
                {camp.status !== 'completed' && (
                  <button
                    onClick={() => toggleCampaign(camp)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold"
                  >
                    {camp.status === 'running' ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                    {camp.status === 'running' ? 'Pause' : 'Resume'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Campaign Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-900">Create Campaign</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Campaign Name</label>
                <input
                  type="text" required value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Q4 Customer Outreach"
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <textarea
                  rows={2} value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Campaign objective"
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100">Cancel</button>
                <button type="submit" disabled={creating} className="px-4 py-2 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50">
                  {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Campaign'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
