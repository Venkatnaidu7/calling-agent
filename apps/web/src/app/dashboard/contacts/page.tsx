'use client'

import { useState } from 'react'
import { Users, Upload, ShieldAlert, Check, Search, Plus } from 'lucide-react'

export default function ContactsPage() {
  const [contacts] = useState([
    {
      id: '1',
      name: 'Sarah Connor',
      phone: '+1 (555) 234-5678',
      email: 'sarah@cyberdyne.com',
      company: 'Cyberdyne Systems',
      dnc: false,
      last_call: 'Yesterday',
    },
    {
      id: '2',
      name: 'John Miller',
      phone: '+1 (555) 876-5432',
      email: 'jmiller@techcorp.io',
      company: 'TechCorp',
      dnc: true,
      last_call: '3 days ago',
    },
    {
      id: '3',
      name: 'Elena Rostova',
      phone: '+1 (555) 345-6789',
      email: 'elena@novapharma.com',
      company: 'Nova Pharma',
      dnc: false,
      last_call: '1 week ago',
    },
  ])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Contacts & Audience</h2>
          <p className="text-sm text-slate-500">Manage phone contacts, lists, and Do-Not-Call (DNC) compliance</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => alert('CSV Import Dialog')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-sm shadow-sm"
          >
            <Upload className="h-4 w-4" /> Import CSV
          </button>
          <button
            onClick={() => alert('Add Contact')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm"
          >
            <Plus className="h-4 w-4" /> Add Contact
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <table className="w-full text-left text-sm text-slate-600">
          <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <tr>
              <th className="py-3.5 px-6">Name</th>
              <th className="py-3.5 px-6">Phone Number</th>
              <th className="py-3.5 px-6">Company</th>
              <th className="py-3.5 px-6">DNC Status</th>
              <th className="py-3.5 px-6">Last Contacted</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {contacts.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                <td className="py-4 px-6 font-medium text-slate-900">{c.name}</td>
                <td className="py-4 px-6 font-mono text-xs text-slate-700">{c.phone}</td>
                <td className="py-4 px-6">{c.company}</td>
                <td className="py-4 px-6">
                  {c.dnc ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                      <ShieldAlert className="h-3 w-3" /> Do Not Call
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <Check className="h-3 w-3" /> Eligible
                    </span>
                  )}
                </td>
                <td className="py-4 px-6 text-slate-500 text-xs">{c.last_call}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
