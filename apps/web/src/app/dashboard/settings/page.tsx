'use client'

import { useEffect, useState } from 'react'
import { Settings, Key, Globe, Shield, Check, Copy, Loader2, AlertCircle, Plus, Trash2 } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function SettingsPage() {
  const [webhooks, setWebhooks] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookEvents, setWebhookEvents] = useState('call.completed,call.started')
  const [saving, setSaving] = useState(false)

  useEffect(() => { loadSettings() }, [])

  async function loadSettings() {
    setLoading(true)
    try {
      const data = await ApiClient.getWebhookEndpoints()
      setWebhooks(Array.isArray(data) ? data : data.items || [])
    } catch (e: any) {
      // Webhooks may not be configured yet — that's OK
      setWebhooks([])
    } finally {
      setLoading(false)
    }
  }

  async function handleSaveWebhook(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      await ApiClient.createWebhookEndpoint({
        url: webhookUrl,
        events: webhookEvents.split(',').map(s => s.trim()).filter(Boolean),
      })
      setSuccess('Webhook endpoint saved successfully!')
      setWebhookUrl('')
      loadSettings()
    } catch (e: any) {
      setError(e.message || 'Failed to save webhook')
    } finally {
      setSaving(false)
    }
  }

  async function handleDeleteWebhook(id: string) {
    try {
      await ApiClient.deleteWebhookEndpoint(id)
      loadSettings()
    } catch (e: any) {
      setError(e.message || 'Failed to delete webhook')
    }
  }

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Workspace Settings</h2>
        <p className="text-sm text-slate-500">Manage tenant credentials, API keys, and outbound webhooks</p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </div>
      )}
      {success && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-medium flex items-center gap-2">
          <Check className="h-4 w-4 shrink-0" /> {success}
        </div>
      )}

      {/* Existing Webhooks */}
      {webhooks.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-600"><Shield className="h-5 w-5" /></div>
            <div>
              <h3 className="font-bold text-slate-900">Active Webhook Endpoints</h3>
              <p className="text-xs text-slate-500">Currently configured webhook destinations</p>
            </div>
          </div>
          <div className="space-y-2">
            {webhooks.map((wh) => (
              <div key={wh.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div>
                  <p className="text-sm font-mono text-slate-700">{wh.url}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{(wh.events || []).join(', ')}</p>
                </div>
                <button onClick={() => handleDeleteWebhook(wh.id)} className="text-slate-400 hover:text-rose-500"><Trash2 className="h-4 w-4" /></button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Webhook Configuration Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600"><Globe className="h-5 w-5" /></div>
          <div>
            <h3 className="font-bold text-slate-900">Add Webhook Endpoint</h3>
            <p className="text-xs text-slate-500">Receive live events for call completions, recordings, and lead captures</p>
          </div>
        </div>

        <form onSubmit={handleSaveWebhook} className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Destination Webhook URL</label>
            <input
              type="url" required value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://api.yourcompany.com/voice-events"
              className="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Events (comma-separated)</label>
            <input
              type="text" value={webhookEvents} onChange={(e) => setWebhookEvents(e.target.value)}
              placeholder="call.completed, call.started"
              className="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
          </div>
          <button type="submit" disabled={saving}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition-colors disabled:opacity-50">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Webhook Endpoint'}
          </button>
        </form>
      </div>
    </div>
  )
}
