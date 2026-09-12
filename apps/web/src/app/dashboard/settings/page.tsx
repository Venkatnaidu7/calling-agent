'use client'

import { useState } from 'react'
import { Settings, Key, Globe, Shield, Check, Copy } from 'lucide-react'

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState('vca_live_8f7b2a9e3c1d40567890abcdef123456')
  const [copied, setCopied] = useState(false)
  const [webhookUrl, setWebhookUrl] = useState('https://api.mycompany.com/voice-events')

  const copyKey = () => {
    navigator.clipboard.writeText(apiKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Workspace Settings</h2>
        <p className="text-sm text-slate-500">Manage tenant credentials, API keys, and outbound webhooks</p>
      </div>

      {/* API Keys Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
            <Key className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900">Developer API Key</h3>
            <p className="text-xs text-slate-500">Authenticate REST requests to the Voice Calling Engine</p>
          </div>
        </div>

        <div className="flex gap-3">
          <input
            type="text"
            readOnly
            value={apiKey}
            className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl font-mono text-xs text-slate-700 select-all"
          />
          <button
            onClick={copyKey}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition-colors"
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Webhook Configuration Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600">
            <Globe className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900">Outgoing Webhooks</h3>
            <p className="text-xs text-slate-500">Receive live events for call completions, recordings, and lead captures</p>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Destination Webhook URL</label>
            <input
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
            />
          </div>
          <button
            onClick={() => alert('Webhook destination saved successfully!')}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition-colors"
          >
            Save Webhook Destination
          </button>
        </div>
      </div>
    </div>
  )
}
