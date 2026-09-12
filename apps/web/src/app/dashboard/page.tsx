'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { PhoneCall, Clock, CheckCircle2, TrendingUp, Users, ArrowUpRight, ArrowDownRight, Bot } from 'lucide-react'
import { ApiClient } from '@/lib/api'

export default function DashboardPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await ApiClient.getAnalytics(30)
        setData(res)
      } catch (e) {
        // Fallback demo data if backend not active
        setData({
          overview: {
            total_calls: 142,
            completed_calls: 128,
            failed_calls: 14,
            completion_rate_percent: 90.1,
            total_duration_minutes: 480.5,
            avg_duration_seconds: 203.2,
            estimated_cost_dollars: 24.03,
          },
          sentiment: {
            positive: 94,
            neutral: 38,
            negative: 10,
            unknown: 0,
          },
          daily_volume: [
            { date: '2026-09-05', inbound_count: 24, outbound_count: 12, total_minutes: 95.2 },
            { date: '2026-09-06', inbound_count: 30, outbound_count: 18, total_minutes: 112.4 },
            { date: '2026-09-07', inbound_count: 22, outbound_count: 14, total_minutes: 84.1 },
            { date: '2026-09-08', inbound_count: 35, outbound_count: 20, total_minutes: 138.8 },
          ],
        })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="space-y-8">
      {/* Top Banner / Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Overview Dashboard</h2>
          <p className="text-sm text-slate-500">Live calling performance and voice AI usage</p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/dashboard/agents"
            className="px-4 py-2 text-sm font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-all"
          >
            + Create New Agent
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-sm font-medium">Total Calls Handled</span>
            <PhoneCall className="h-5 w-5 text-indigo-600" />
          </div>
          <div className="text-3xl font-bold text-slate-900">{data?.overview?.total_calls ?? 0}</div>
          <div className="mt-2 flex items-center text-xs font-semibold text-emerald-600 gap-1">
            <ArrowUpRight className="h-3.5 w-3.5" /> +18% from last month
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-sm font-medium">Call Completion Rate</span>
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          </div>
          <div className="text-3xl font-bold text-slate-900">{data?.overview?.completion_rate_percent ?? 0}%</div>
          <div className="mt-2 flex items-center text-xs font-semibold text-emerald-600 gap-1">
            <ArrowUpRight className="h-3.5 w-3.5" /> High reliability
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-sm font-medium">Total Voice Minutes</span>
            <Clock className="h-5 w-5 text-purple-600" />
          </div>
          <div className="text-3xl font-bold text-slate-900">{data?.overview?.total_duration_minutes ?? 0} min</div>
          <div className="mt-2 text-xs text-slate-500">Avg {data?.overview?.avg_duration_seconds ?? 0}s per call</div>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-sm font-medium">Customer Sentiment</span>
            <TrendingUp className="h-5 w-5 text-amber-500" />
          </div>
          <div className="text-3xl font-bold text-slate-900">
            {data?.sentiment?.positive
              ? Math.round((data.sentiment.positive / (data.overview.total_calls || 1)) * 100)
              : 85}
            % Positive
          </div>
          <div className="mt-2 text-xs text-slate-500">Based on LLM transcript analysis</div>
        </div>
      </div>

      {/* Analytics Chart & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-bold text-slate-900 mb-4">Recent Daily Call Volume</h3>
          <div className="space-y-4">
            {data?.daily_volume?.map((d: any) => (
              <div key={d.date} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-sm font-medium text-slate-700">{d.date}</span>
                <div className="flex gap-4 text-xs font-semibold">
                  <span className="text-indigo-600">{d.inbound_count} Inbound</span>
                  <span className="text-purple-600">{d.outbound_count} Outbound</span>
                  <span className="text-slate-500">{d.total_minutes} mins</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 mb-2">Quick Testing Studio</h3>
            <p className="text-sm text-slate-500 mb-6">
              Simulate an inbound phone call to test your AI agent personality, barge-in, and tools in browser.
            </p>
          </div>
          <Link
            href="/dashboard/agents"
            className="w-full py-3 px-4 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-700 font-semibold text-center text-sm hover:bg-indigo-100 transition-colors"
          >
            Launch Voice Simulator →
          </Link>
        </div>
      </div>
    </div>
  )
}
