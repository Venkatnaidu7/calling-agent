'use client'

import { useEffect, useState } from 'react'
import { CreditCard, Check, Zap, ExternalLink, ShieldCheck } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function BillingPage() {
  const [sub, setSub] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await ApiClient.getSubscription()
        setSub(res)
      } catch (e: any) {
        console.error('Failed to load subscription:', e)
        setSub(null)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="space-y-8 max-w-5xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Billing & Subscriptions</h2>
        <p className="text-sm text-slate-500">Monitor voice calling minutes, manage subscription tiers, and download invoices</p>
      </div>

      {/* Usage Meter Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
              <CreditCard className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900">Current Plan: <span className="uppercase text-indigo-600">{sub?.plan_tier || 'Starter'}</span></h3>
              <p className="text-xs text-slate-500">Includes {sub?.concurrency_limit || 2} concurrent voice lines</p>
            </div>
          </div>
          <button
            onClick={() => alert('Redirecting to Stripe Billing Portal...')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-xs transition-colors"
          >
            Manage Billing <ExternalLink className="h-3.5 w-3.5" />
          </button>
        </div>

        <div>
          <div className="flex justify-between text-xs font-semibold text-slate-700 mb-2">
            <span>Monthly Minute Usage</span>
            <span>{sub?.minutes_used_this_period || 0} / {sub?.monthly_minute_limit || 500} mins used</span>
          </div>
          <div className="w-full h-3 rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"
              style={{
                width: `${Math.min(
                  100,
                  ((sub?.minutes_used_this_period || 0) / (sub?.monthly_minute_limit || 500)) * 100
                )}%`,
              }}
            ></div>
          </div>
        </div>
      </div>

      {/* Pricing Tiers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col justify-between space-y-6">
          <div>
            <h4 className="font-bold text-lg text-slate-900">Starter</h4>
            <p className="text-xs text-slate-500 mt-1">For single location businesses</p>
            <div className="mt-4 text-3xl font-extrabold text-slate-900">$49 <span className="text-sm font-medium text-slate-400">/mo</span></div>
            <ul className="mt-6 space-y-3 text-sm text-slate-600">
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> 300 Included Minutes</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> 1 Phone Number</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> 2 Concurrent Lines</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> Standard AI Voice</li>
            </ul>
          </div>
          <button className="w-full py-2.5 rounded-xl border border-slate-200 text-slate-700 font-semibold text-sm">
            Current Plan
          </button>
        </div>

        <div className="bg-white rounded-2xl border-2 border-indigo-600 p-6 flex flex-col justify-between space-y-6 shadow-md shadow-indigo-100 relative">
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-indigo-600 text-white text-[10px] font-bold uppercase tracking-wider">
            Most Popular
          </div>
          <div>
            <h4 className="font-bold text-lg text-slate-900">Professional</h4>
            <p className="text-xs text-slate-500 mt-1">For growing sales & support teams</p>
            <div className="mt-4 text-3xl font-extrabold text-slate-900">$199 <span className="text-sm font-medium text-slate-400">/mo</span></div>
            <ul className="mt-6 space-y-3 text-sm text-slate-600">
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> 1,500 Included Minutes</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> 5 Phone Numbers</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> 5 Concurrent Lines</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> Knowledge Base RAG</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> Custom CRM Webhooks</li>
            </ul>
          </div>
          <button
            onClick={() => alert('Upgrading to Professional plan...')}
            className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm"
          >
            Upgrade to Pro
          </button>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col justify-between space-y-6">
          <div>
            <h4 className="font-bold text-lg text-slate-900">Enterprise</h4>
            <p className="text-xs text-slate-500 mt-1">For enterprise call centers & BPOs</p>
            <div className="mt-4 text-3xl font-extrabold text-slate-900">$599 <span className="text-sm font-medium text-slate-400">/mo</span></div>
            <ul className="mt-6 space-y-3 text-sm text-slate-600">
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> 5,000 Included Minutes</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> Unlimited Phone Numbers</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> 20 Concurrent Lines</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> Custom LLM Fine-Tuning</li>
              <li className="flex items-center gap-2"><Check className="h-4 w-4 text-indigo-600" /> Dedicated Account Manager</li>
            </ul>
          </div>
          <button
            onClick={() => alert('Contacting sales...')}
            className="w-full py-2.5 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-sm"
          >
            Contact Sales
          </button>
        </div>
      </div>
    </div>
  )
}
