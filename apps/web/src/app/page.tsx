import Link from 'next/link'
import { PhoneCall, Zap, ShieldCheck, Database, BarChart3, Bot } from 'lucide-react'

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="px-6 lg:px-12 h-20 flex items-center justify-between border-b border-slate-200 bg-white">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-indigo-200">
            <PhoneCall className="h-5 w-5" />
          </div>
          <span className="font-bold text-xl tracking-tight text-slate-900">VoiceAgent.ai</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900">
            Log in
          </Link>
          <Link
            href="/register"
            className="px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-colors"
          >
            Start Free Trial
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="py-24 px-6 lg:px-12 text-center max-w-5xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold mb-6">
            <Zap className="h-3.5 w-3.5" /> Next-Gen Realtime Voice AI with Sub-500ms Latency
          </div>
          <h1 className="text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 mb-6 leading-tight">
            Autonomous AI Phone Agents <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
              For Inbound & Outbound Calling
            </span>
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-10 leading-relaxed">
            Deploy conversational voice agents that answer customer questions, book appointments, make outbound calls, and integrate seamlessly with your CRM and calendars.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              href="/register"
              className="px-8 py-3.5 text-base font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-200 transition-all hover:-translate-y-0.5"
            >
              Get Started in Minutes
            </Link>
            <Link
              href="/dashboard"
              className="px-8 py-3.5 text-base font-semibold rounded-xl bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 transition-all"
            >
              Live Demo Studio
            </Link>
          </div>
        </section>

        {/* Feature Grid */}
        <section className="py-20 bg-white border-t border-slate-200 px-6 lg:px-12">
          <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-8">
            <div className="p-8 rounded-2xl bg-slate-50 border border-slate-100">
              <div className="h-12 w-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-6">
                <Bot className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Zero-Transcode Voice</h3>
              <p className="text-slate-600 leading-relaxed">
                Direct Twilio G.711 μ-law audio passthrough to OpenAI Realtime API. Native barge-in detection and intelligent interruption handling.
              </p>
            </div>

            <div className="p-8 rounded-2xl bg-slate-50 border border-slate-100">
              <div className="h-12 w-12 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center mb-6">
                <Database className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Knowledge Base RAG</h3>
              <p className="text-slate-600 leading-relaxed">
                Upload PDFs, DOCX, CSVs, or websites. Semantic vector search powered by pgvector injects real business context mid-call.
              </p>
            </div>

            <div className="p-8 rounded-2xl bg-slate-50 border border-slate-100">
              <div className="h-12 w-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-6">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">TCPA & DNC Compliance</h3>
              <p className="text-slate-600 leading-relaxed">
                Automated calling windows based on customer timezone, multi-source DNC filtering, verbal consent tracking, and AI disclosures.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="py-8 border-t border-slate-200 text-center text-sm text-slate-500 bg-white">
        © {new Date().getFullYear()} VoiceAgent.ai Platform. Enterprise Production Architecture.
      </footer>
    </div>
  )
}
