'use client'

import { useState } from 'react'
import { Database, Upload, FileText, Globe, Plus, CheckCircle2, ArrowRight } from 'lucide-react'

export default function KnowledgePage() {
  const [kbs] = useState([
    {
      id: '1',
      name: 'Product Documentation & Pricing',
      description: 'Contains FAQs, refund policy, tiered pricing sheet, and technical specs.',
      docs_count: 8,
      chunks_count: 142,
      last_updated: '2 days ago',
    },
    {
      id: '2',
      name: 'Company Office Policies & Hours',
      description: 'Holiday schedules, doctor provider bios, and emergency contact procedures.',
      docs_count: 3,
      chunks_count: 48,
      last_updated: '1 week ago',
    },
  ])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Knowledge Bases & RAG</h2>
          <p className="text-sm text-slate-500">Provide real business information for your AI voice agents to consult</p>
        </div>
        <button
          onClick={() => alert('Create Knowledge Base modal')}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm"
        >
          <Plus className="h-4 w-4" /> Create Knowledge Base
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {kbs.map((kb) => (
          <div key={kb.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600">
                  <Database className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{kb.name}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Updated {kb.last_updated}</p>
                </div>
              </div>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="h-3 w-3" /> Ready
              </span>
            </div>

            <p className="text-sm text-slate-600 leading-relaxed">{kb.description}</p>

            <div className="flex items-center gap-6 text-xs text-slate-500 pt-3 border-t border-slate-100">
              <span className="flex items-center gap-1.5 font-medium text-slate-700">
                <FileText className="h-4 w-4 text-slate-400" /> {kb.docs_count} Documents
              </span>
              <span className="font-medium text-slate-700">{kb.chunks_count} Vector Chunks</span>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => alert('Upload Document dialog')}
                className="flex-1 py-2 px-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 font-semibold text-xs flex items-center justify-center gap-1.5"
              >
                <Upload className="h-3.5 w-3.5" /> Upload File (PDF/DOCX)
              </button>
              <button
                onClick={() => alert('Test semantic search')}
                className="py-2 px-4 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs"
              >
                Query RAG
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
