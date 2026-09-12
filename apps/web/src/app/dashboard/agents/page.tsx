'use client'

import { useEffect, useState } from 'react'
import { Bot, Plus, Mic, Settings2, Play, CheckCircle2, AlertCircle } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  useEffect(() => {
    loadAgents()
  }, [])

  async function loadAgents() {
    try {
      const data = await ApiClient.getAgents()
      setAgents(Array.isArray(data) ? data : data.items || [])
    } catch (e) {
      // Demo agent fallback
      setAgents([
        {
          id: '1',
          name: 'Receptionist AI',
          description: 'Answers incoming calls, qualifies leads, and schedules appointments.',
          status: 'published',
          is_active: true,
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          name: 'Outbound Appointment Reminder',
          description: 'Calls customers 24h before their booked slot to confirm or reschedule.',
          status: 'published',
          is_active: true,
          created_at: new Date().toISOString(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateAgent(e: React.FormEvent) {
    e.preventDefault()
    try {
      await ApiClient.createAgent({ name, description })
      setShowModal(false)
      setName('')
      setDescription('')
      loadAgents()
    } catch (err: any) {
      alert(err.message || 'Failed to create agent')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">AI Voice Agents</h2>
          <p className="text-sm text-slate-500">Configure personas, prompt instructions, voices, and tool access</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm transition-all"
        >
          <Plus className="h-4 w-4" /> Create Agent
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <div key={agent.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="h-10 w-10 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center">
                  <Bot className="h-5 w-5" />
                </div>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    agent.status === 'published'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-amber-50 text-amber-700 border border-amber-200'
                  }`}
                >
                  {agent.status}
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-900">{agent.name}</h3>
              <p className="text-sm text-slate-600 mt-1 line-clamp-2">{agent.description || 'No description provided.'}</p>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs font-medium">
              <span className="text-slate-400">Voice: OpenAI Ash (Natural)</span>
              <button
                onClick={() => alert(`Simulating live call with ${agent.name}... Connected via WebRTC!`)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition-colors"
              >
                <Play className="h-3.5 w-3.5" /> Test Voice
              </button>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl space-y-6">
            <h3 className="text-xl font-bold text-slate-900">Create AI Voice Agent</h3>
            <form onSubmit={handleCreateAgent} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Agent Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Inbound Support Assistant"
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description / Role</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What is the objective of this AI agent?"
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  Save Agent
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
