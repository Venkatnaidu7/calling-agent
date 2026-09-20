'use client'

import { useEffect, useState } from 'react'
import { PhoneIncoming, PhoneOutgoing, Clock, FileText, CheckCircle, XCircle, Search } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function CallsPage() {
  const [calls, setCalls] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCall, setSelectedCall] = useState<any>(null)
  const [transcriptLoading, setTranscriptLoading] = useState(false)

  useEffect(() => {
    loadCalls()
  }, [])

  async function loadCalls() {
    setError('')
    try {
      const data = await ApiClient.getCalls()
      setCalls(data.items || [])
    } catch (e: any) {
      setError(e.message || 'Failed to load call logs')
      setCalls([])
    } finally {
      setLoading(false)
    }
  }

  async function viewTranscript(call: any) {
    setSelectedCall({ ...call, transcript: null })
    setTranscriptLoading(true)
    try {
      const transcript = await ApiClient.getCallTranscript(call.call_id || call.id)
      setSelectedCall({ ...call, transcript: Array.isArray(transcript) ? transcript : transcript.turns || transcript.segments || [] })
    } catch {
      setSelectedCall({ ...call, transcript: [] })
    } finally {
      setTranscriptLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Call History &amp; Transcripts</h2>
        <p className="text-sm text-slate-500">Live call recordings, transcripts, and AI-generated sentiment summaries</p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium">
          {error}
        </div>
      )}

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-6">Direction</th>
                <th className="py-3.5 px-6">Caller / Destination</th>
                <th className="py-3.5 px-6">Status</th>
                <th className="py-3.5 px-6">Duration</th>
                <th className="py-3.5 px-6">Sentiment</th>
                <th className="py-3.5 px-6">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {calls.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-4 px-6 flex items-center gap-2">
                    {c.direction === 'inbound' ? (
                      <span className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
                        <PhoneIncoming className="h-4 w-4" />
                      </span>
                    ) : (
                      <span className="p-1.5 rounded-lg bg-purple-50 text-purple-600">
                        <PhoneOutgoing className="h-4 w-4" />
                      </span>
                    )}
                    <span className="capitalize font-medium text-slate-900">{c.direction}</span>
                  </td>
                  <td className="py-4 px-6">
                    <div className="font-medium text-slate-900">{c.from_number}</div>
                    <div className="text-xs text-slate-400">to {c.to_number}</div>
                  </td>
                  <td className="py-4 px-6">
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <CheckCircle className="h-3 w-3" /> {c.status}
                    </span>
                  </td>
                  <td className="py-4 px-6 font-medium text-slate-700">
                    {Math.floor(c.duration_seconds / 60)}m {c.duration_seconds % 60}s
                  </td>
                  <td className="py-4 px-6">
                    <span
                      className={`px-2 py-0.5 rounded-md text-xs font-semibold uppercase ${
                        c.sentiment === 'positive'
                          ? 'bg-emerald-100 text-emerald-800'
                          : c.sentiment === 'negative'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {c.sentiment || 'neutral'}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <button
                      onClick={() => viewTranscript(c)}
                      className="px-3 py-1 rounded-lg text-xs font-semibold text-indigo-600 hover:bg-indigo-50 transition-colors"
                    >
                      View Transcript
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transcript Drawer Modal */}
      {selectedCall && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex justify-end z-50">
          <div className="w-full max-w-lg bg-white h-full shadow-2xl p-8 overflow-y-auto flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <h3 className="text-xl font-bold text-slate-900">Call Transcript</h3>
                <button
                  onClick={() => setSelectedCall(null)}
                  className="text-slate-400 hover:text-slate-600 text-xl font-bold"
                >
                  ✕
                </button>
              </div>

              {selectedCall.summary && (
                <div className="my-6 p-4 rounded-xl bg-indigo-50/60 border border-indigo-100 text-sm">
                  <div className="font-semibold text-indigo-900 mb-1">AI Call Summary</div>
                  <p className="text-indigo-800 leading-relaxed">{selectedCall.summary}</p>
                </div>
              )}

              <div className="space-y-4 my-6">
                {selectedCall.transcript?.map((t: any, idx: number) => (
                  <div
                    key={idx}
                    className={`flex flex-col ${
                      t.speaker === 'agent' ? 'items-start' : 'items-end'
                    }`}
                  >
                    <span className="text-xs font-semibold text-slate-400 mb-1 uppercase">
                      {t.speaker === 'agent' ? 'AI Voice Agent' : 'Caller'}
                    </span>
                    <div
                      className={`p-3.5 rounded-2xl text-sm max-w-[85%] leading-relaxed ${
                        t.speaker === 'agent'
                          ? 'bg-slate-100 text-slate-800 rounded-tl-sm'
                          : 'bg-indigo-600 text-white rounded-tr-sm shadow-sm'
                      }`}
                    >
                      {t.text}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => setSelectedCall(null)}
              className="w-full py-2.5 rounded-xl border border-slate-300 text-slate-700 font-semibold text-sm hover:bg-slate-50 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
