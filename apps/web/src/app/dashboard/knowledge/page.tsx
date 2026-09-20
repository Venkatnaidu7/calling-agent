'use client'

import { useEffect, useState, useRef } from 'react'
import { Database, Upload, FileText, Plus, CheckCircle2, Search, Loader2, AlertCircle, X, Trash2 } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function KnowledgePage() {
  const [kbs, setKbs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showSearchModal, setShowSearchModal] = useState<string | null>(null)
  const [createData, setCreateData] = useState({ name: '', description: '' })
  const [creating, setCreating] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)

  useEffect(() => { loadKbs() }, [])

  async function loadKbs() {
    setLoading(true)
    setError('')
    try {
      const data = await ApiClient.getKnowledgeBases()
      setKbs(Array.isArray(data) ? data : data.items || [])
    } catch (e: any) {
      setError(e.message || 'Failed to load knowledge bases')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    try {
      await ApiClient.createKnowledgeBase(createData)
      setShowCreateModal(false)
      setCreateData({ name: '', description: '' })
      loadKbs()
    } catch (e: any) {
      setError(e.message || 'Failed to create knowledge base')
    } finally {
      setCreating(false)
    }
  }

  async function handleUpload(kbId: string, e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      await ApiClient.uploadDocument(kbId, formData)
      loadKbs()
    } catch (err: any) {
      setError(err.message || 'Upload failed')
    }
  }

  async function handleSearch(kbId: string) {
    if (!searchQuery.trim()) return
    setSearching(true)
    try {
      const results = await ApiClient.searchKnowledgeBase(kbId, searchQuery)
      setSearchResults(Array.isArray(results) ? results : results.results || [])
    } catch (e: any) {
      setError(e.message || 'Search failed')
    } finally {
      setSearching(false)
    }
  }

  async function handleDeleteKb(id: string) {
    if (!confirm('Delete this knowledge base and all its documents?')) return
    try {
      await ApiClient.deleteKnowledgeBase(id)
      loadKbs()
    } catch (e: any) {
      setError(e.message || 'Failed to delete knowledge base')
    }
  }

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Knowledge Bases &amp; RAG</h2>
          <p className="text-sm text-slate-500">Provide real business information for your AI voice agents to consult</p>
        </div>
        <button onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm">
          <Plus className="h-4 w-4" /> Create Knowledge Base
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </div>
      )}

      {kbs.length === 0 && !error ? (
        <div className="text-center py-16 text-slate-500">
          <Database className="h-12 w-12 mx-auto mb-4 text-slate-300" />
          <p className="text-lg font-medium">No knowledge bases yet</p>
          <p className="text-sm">Create a knowledge base and upload documents for your AI agents.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {kbs.map((kb) => (
            <div key={kb.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600"><Database className="h-5 w-5" /></div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">{kb.name}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">{kb.description || 'No description'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <CheckCircle2 className="h-3 w-3" /> Ready
                  </span>
                  <button onClick={() => handleDeleteKb(kb.id)} className="text-slate-400 hover:text-rose-500"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>

              <div className="flex items-center gap-6 text-xs text-slate-500 pt-3 border-t border-slate-100">
                <span className="flex items-center gap-1.5 font-medium text-slate-700">
                  <FileText className="h-4 w-4 text-slate-400" /> {kb.document_count || 0} Documents
                </span>
                <span className="font-medium text-slate-700">{kb.chunk_count || 0} Vector Chunks</span>
              </div>

              <div className="flex gap-3">
                <label className="flex-1 py-2 px-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 font-semibold text-xs flex items-center justify-center gap-1.5 cursor-pointer">
                  <Upload className="h-3.5 w-3.5" /> Upload File (PDF/DOCX)
                  <input type="file" accept=".pdf,.docx,.doc,.csv,.txt" className="hidden" onChange={(e) => handleUpload(kb.id, e)} />
                </label>
                <button onClick={() => { setShowSearchModal(kb.id); setSearchResults([]); setSearchQuery('') }}
                  className="py-2 px-4 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs">
                  Query RAG
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create KB Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-900">Create Knowledge Base</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
                <input type="text" required value={createData.name} onChange={(e) => setCreateData({...createData, name: e.target.value})}
                  placeholder="e.g. Product Documentation"
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <textarea rows={3} value={createData.description} onChange={(e) => setCreateData({...createData, description: e.target.value})}
                  placeholder="What information does this knowledge base contain?"
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100">Cancel</button>
                <button type="submit" disabled={creating} className="px-4 py-2 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50">
                  {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Search Modal */}
      {showSearchModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-8 max-w-lg w-full shadow-2xl space-y-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-900">Semantic Search</h3>
              <button onClick={() => setShowSearchModal(null)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button>
            </div>
            <div className="flex gap-2">
              <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Ask a question..."
                className="flex-1 px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
                onKeyDown={(e) => e.key === 'Enter' && handleSearch(showSearchModal)} />
              <button onClick={() => handleSearch(showSearchModal)} disabled={searching}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm disabled:opacity-50">
                {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              </button>
            </div>
            {searchResults.length > 0 && (
              <div className="space-y-3">
                {searchResults.map((r: any, i: number) => (
                  <div key={i} className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                    <p className="text-sm text-slate-700">{r.content || r.text}</p>
                    <p className="text-xs text-slate-400 mt-2">Score: {r.score?.toFixed(3) || 'N/A'}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
