'use client'

import { useEffect, useState } from 'react'
import { Users, UserPlus, Shield, Loader2, AlertCircle, X, Trash2 } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function UsersPage() {
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('AGENT')
  const [inviting, setInviting] = useState(false)

  useEffect(() => { loadUsers() }, [])

  async function loadUsers() {
    setLoading(true)
    setError('')
    try {
      const data = await ApiClient.getUsers()
      setUsers(Array.isArray(data) ? data : data.items || [])
    } catch (e: any) {
      setError(e.message || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault()
    setInviting(true)
    try {
      await ApiClient.inviteUser({ email: inviteEmail, role: inviteRole })
      setShowInviteModal(false)
      setInviteEmail('')
      loadUsers()
    } catch (e: any) {
      setError(e.message || 'Failed to invite user')
    } finally {
      setInviting(false)
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to remove this user?')) return
    try {
      await ApiClient.deleteUser(id)
      loadUsers()
    } catch (e: any) {
      setError(e.message || 'Failed to remove user')
    }
  }

  async function handleUpdateRole(id: string, newRole: string) {
    try {
      await ApiClient.updateUserRole(id, newRole)
      loadUsers()
    } catch (e: any) {
      setError(e.message || 'Failed to update user role')
    }
  }

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-indigo-600" /></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Team Members</h2>
          <p className="text-sm text-slate-500">Manage workspace users and their access roles</p>
        </div>
        <button
          onClick={() => setShowInviteModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm"
        >
          <UserPlus className="h-4 w-4" /> Invite Member
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </div>
      )}

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <table className="w-full text-left text-sm text-slate-600">
          <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <tr>
              <th className="py-3.5 px-6">User</th>
              <th className="py-3.5 px-6">Role</th>
              <th className="py-3.5 px-6">Status</th>
              <th className="py-3.5 px-6">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                <td className="py-4 px-6">
                  <div className="font-medium text-slate-900">{u.first_name} {u.last_name}</div>
                  <div className="text-xs text-slate-500">{u.email}</div>
                </td>
                <td className="py-4 px-6">
                  <select 
                    value={u.role} 
                    onChange={(e) => handleUpdateRole(u.id, e.target.value)}
                    className="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 focus:ring-2 focus:ring-indigo-600"
                  >
                    <option value="TENANT_ADMIN">Admin</option>
                    <option value="CAMPAIGN_MANAGER">Campaign Manager</option>
                    <option value="AGENT">Agent</option>
                  </select>
                </td>
                <td className="py-4 px-6">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${u.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="py-4 px-6">
                  <button onClick={() => handleDelete(u.id)} className="text-slate-400 hover:text-rose-500 transition-colors">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-900">Invite Team Member</h3>
              <button onClick={() => setShowInviteModal(false)} className="text-slate-400 hover:text-slate-600"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
                <input type="email" required value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
                <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600">
                  <option value="TENANT_ADMIN">Admin</option>
                  <option value="CAMPAIGN_MANAGER">Campaign Manager</option>
                  <option value="AGENT">Agent</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowInviteModal(false)} className="px-4 py-2 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100">Cancel</button>
                <button type="submit" disabled={inviting} className="px-4 py-2 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50">
                  {inviting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Send Invite'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
