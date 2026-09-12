'use client'

import { useState } from 'react'
import { Megaphone, Play, Pause, Plus, CheckCircle2, Clock, Users } from 'lucide-react'

export default function CampaignsPage() {
  const [campaigns] = useState([
    {
      id: '1',
      name: 'September Customer Outreach',
      agent: 'Product Specialist AI',
      status: 'running',
      total_contacts: 450,
      contacted: 280,
      completed: 210,
      scheduled_hours: '9:00 AM - 5:00 PM (Local)',
    },
    {
      id: '2',
      name: 'Appointment Confirmations Q3',
      agent: 'Reminder Bot',
      status: 'paused',
      total_contacts: 120,
      contacted: 85,
      completed: 82,
      scheduled_hours: '10:00 AM - 6:00 PM (Local)',
    },
  ])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Outbound Campaigns</h2>
          <p className="text-sm text-slate-500">Automate high-volume outbound calling with compliance safeguards</p>
        </div>
        <button
          onClick={() => alert('Opening campaign wizard...')}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm transition-all"
        >
          <Plus className="h-4 w-4" /> New Campaign
        </button>
      </div>

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
                  <p className="text-xs text-slate-500">Agent: {camp.agent}</p>
                </div>
              </div>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  camp.status === 'running'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                }`}
              >
                {camp.status}
              </span>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-600 mb-2">
                <span>Progress: {camp.completed} / {camp.total_contacts} completed</span>
                <span>{Math.round((camp.completed / camp.total_contacts) * 100)}%</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full bg-indigo-600 rounded-full transition-all"
                  style={{ width: `${(camp.completed / camp.total_contacts) * 100}%` }}
                ></div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5 text-slate-400" /> {camp.scheduled_hours}
              </span>
              <button
                onClick={() => alert(`Toggled campaign: ${camp.name}`)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold"
              >
                {camp.status === 'running' ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                {camp.status === 'running' ? 'Pause' : 'Resume'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
