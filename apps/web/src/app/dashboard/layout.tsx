'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  PhoneCall,
  LayoutDashboard,
  Bot,
  History,
  Megaphone,
  Users,
  Database,
  CreditCard,
  Settings,
  LogOut,
  Shield,
} from 'lucide-react'
import { ApiClient } from '@/lib/api'

const navItems = [
  { label: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { label: 'AI Agents', href: '/dashboard/agents', icon: Bot },
  { label: 'Phone Numbers', href: '/dashboard/phone-numbers', icon: PhoneCall },
  { label: 'Call Logs', href: '/dashboard/calls', icon: History },
  { label: 'Campaigns', href: '/dashboard/campaigns', icon: Megaphone },
  { label: 'Contacts', href: '/dashboard/contacts', icon: Users },
  { label: 'Knowledge Base', href: '/dashboard/knowledge', icon: Database },
  { label: 'Compliance', href: '/dashboard/compliance', icon: Shield }, 
  { label: 'Users', href: '/dashboard/users', icon: Users },
  { label: 'Billing', href: '/dashboard/billing', icon: CreditCard },
  { label: 'Settings', href: '/dashboard/settings', icon: Settings },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = () => {
    ApiClient.clearToken()
    router.push('/login')
  }

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0">
        <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-800">
          <div className="h-9 w-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white">
            <PhoneCall className="h-5 w-5" />
          </div>
          <span className="font-bold text-lg text-white tracking-tight">VoiceAgent.ai</span>
        </div>

        <nav className="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  active
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8">
          <h1 className="text-lg font-semibold text-slate-900">Platform Management Console</h1>
          <div className="flex items-center gap-3">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-xs font-medium text-slate-500">Realtime Engine Connected</span>
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  )
}
