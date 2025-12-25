import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
//import { motion } from 'framer-motion'
import {
  AlertCircle,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  Code2,
  GitBranch,
  Info,
  Link2,
  Loader2,
  Shield,
} from 'lucide-react'

import { apiService } from '../services/api'
import { AnalysisResponse, SourceReference } from '../types'

const PROGRESS_STEPS = [
  { label: 'Cloning repository', description: 'Fetching Git metadata & commits' },
  { label: 'Parsing files', description: 'Reading & filtering source files' },
  { label: 'Chunking & embeddings', description: 'Semantic chunking + MiniLM embeddings' },
  { label: 'Vector search', description: 'Retrieving context from Qdrant' },
  { label: 'LLM reasoning', description: 'Structured JSON response with citations' },
]

const severityColor = (severity?: string) => {
  switch (severity) {
    case 'critical':
      return 'text-red-400 bg-red-400/10'
    case 'high':
      return 'text-orange-400 bg-orange-400/10'
    case 'medium':
      return 'text-yellow-400 bg-yellow-400/10'
    default:
      return 'text-emerald-400 bg-emerald-400/10'
  }
}

const impactChip = (impact?: string) => {
  switch (impact) {
    case 'high':
      return 'bg-red-500/10 text-red-300 border-red-400/30'
    case 'medium':
      return 'bg-yellow-500/10 text-yellow-300 border-yellow-400/30'
    default:
      return 'bg-sky-500/10 text-sky-300 border-sky-400/30'
  }
}

const getReferenceById = (references: SourceReference[], id: string) =>
  references.find((ref) => ref.id === id)

export default function Analyze() {
  const [searchParams] = useSearchParams()
  const [formState, setFormState] = useState({
    repoUrl: '',
    branch: 'main',
    includeTests: false,
  })
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [status, setStatus] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [error, setError] = useState('')
  const [stepIndex, setStepIndex] = useState(0)
  const [selectedReference, setSelectedReference] = useState<SourceReference | null>(null)

  const canAnalyze = formState.repoUrl.trim().length > 0

  const startAnalysis = useCallback(
    async (overrideRepo?: string) => {
      const repoToAnalyze = overrideRepo ?? formState.repoUrl
      if (!repoToAnalyze) return
      setStatus('running')
      setError('')
      setAnalysis(null)
      setSelectedReference(null)
      try {
        const response = await apiService.analyzeRepository({
          repo_url: repoToAnalyze,
          branch: formState.branch,
          include_tests: formState.includeTests,
        })
        setAnalysis(response)
        setSelectedReference(response.source_references[0] ?? null)
        setStatus('done')
      } catch (err: unknown) {
        const message =
          err instanceof Error
            ? err.message
            : (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
              'Unable to analyze repository'
        setError(message)
        setStatus('error')
      }
    },
    [formState.branch, formState.includeTests, formState.repoUrl],
  )

  useEffect(() => {
    const repo = searchParams.get('repo')
    if (repo) {
      setFormState((prev) => ({ ...prev, repoUrl: repo }))
      startAnalysis(repo)
    }
  }, [searchParams, startAnalysis])

  useEffect(() => {
    if (status !== 'running') return
    const timer = window.setInterval(() => {
      setStepIndex((prev) => (prev + 1) % PROGRESS_STEPS.length)
    }, 2200)
    return () => window.clearInterval(timer)
  }, [status])

  const summaryReferences = useMemo(() => {
    if (!analysis) return []
    return analysis.summary_references
      .map((id) => getReferenceById(analysis.source_references, id))
      .filter(Boolean) as SourceReference[]
  }, [analysis])

  return (
    <div className="min-h-screen bg-gray-950 text-white px-4 pb-16 pt-10">
      <div className="mx-auto max-w-6xl space-y-10">
        <section className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm text-gray-400 uppercase tracking-[0.3em]">AutoDeployX</p>
              <h1 className="text-3xl font-bold mt-2">Repository Analyzer</h1>
              <p className="text-gray-400 mt-2">
                Clone, chunk, embed, analyze. Deterministic JSON with references in minutes.
              </p>
            </div>
            <form
              className="w-full lg:w-auto flex flex-col gap-3"
              onSubmit={(e) => {
                e.preventDefault()
                startAnalysis()
              }}
            >
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  value={formState.repoUrl}
                  onChange={(e) => setFormState((prev) => ({ ...prev, repoUrl: e.target.value }))}
                  type="url"
                  required
                  placeholder="https://github.com/org/project"
                  className="flex-1 rounded-2xl border border-white/15 bg-white/5 px-4 py-3 focus:outline-none focus:border-sky-400"
                />
                <input
                  value={formState.branch}
                  onChange={(e) => setFormState((prev) => ({ ...prev, branch: e.target.value }))}
                  placeholder="main"
                  className="w-32 rounded-2xl border border-white/15 bg-white/5 px-4 py-3 focus:outline-none focus:border-sky-400"
                />
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-400">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formState.includeTests}
                    onChange={(e) =>
                      setFormState((prev) => ({ ...prev, includeTests: e.target.checked }))
                    }
                    className="rounded border-white/20 bg-transparent"
                  />
                  Include test directories
                </label>
                <button
                  type="submit"
                  disabled={!canAnalyze || status === 'running'}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 px-6 py-3 font-semibold disabled:opacity-40"
                >
                  {status === 'running' ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Analyzing…
                    </>
                  ) : (
                    <>
                      Run analysis <CheckCircle2 className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
          {status === 'running' && (
            <div className="mt-6 grid gap-4 sm:grid-cols-5">
              {PROGRESS_STEPS.map((step, idx) => (
                <div
                  key={step.label}
                  className={`rounded-2xl border p-4 text-sm transition ${
                    idx <= stepIndex
                      ? 'border-emerald-400/40 bg-emerald-500/5'
                      : 'border-white/10 bg-white/5 text-gray-400'
                  }`}
                >
                  <p className="font-semibold">{step.label}</p>
                  <p className="mt-1 text-xs text-gray-400">{step.description}</p>
                </div>
              ))}
            </div>
          )}
          {status === 'error' && (
            <div className="mt-4 flex items-start gap-3 rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <div>
                <p className="font-semibold">Analysis failed</p>
                <p className="text-red-100">{error}</p>
              </div>
            </div>
          )}
        </section>

        {analysis && (
          <>
            <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm text-gray-400">Repository</p>
                  <div className="flex items-center gap-3 mt-1">
                    <a
                      href={analysis.metadata.repo_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-lg font-semibold text-sky-300 hover:underline break-all"
                    >
                      {analysis.metadata.repo_url}
                    </a>
                    <Link2 className="w-4 h-4 text-gray-400" />
                  </div>
                  <div className="flex flex-wrap gap-4 mt-4 text-sm text-gray-400">
                    <span className="inline-flex items-center gap-2">
                      <GitBranch className="w-4 h-4" /> {analysis.metadata.branch}
                    </span>
                    {analysis.metadata.commit?.sha && (
                      <span className="inline-flex items-center gap-2">
                        <Code2 className="w-4 h-4" /> {analysis.metadata.commit.sha}
                      </span>
                    )}
                    <span className="inline-flex items-center gap-2">
                      <ClipboardCheck className="w-4 h-4" /> {analysis.metadata.total_files} files
                    </span>
                  </div>
                </div>
                <div className="rounded-2xl border border-white/15 bg-white/5 p-4 w-full md:w-72">
                  <p className="text-xs uppercase tracking-widest text-gray-400">Summary</p>
                  <p className="mt-2 text-gray-100">{analysis.summary}</p>
                  {summaryReferences.length > 0 && (
                    <div className="mt-3 text-xs text-gray-400">
                      Sources:{' '}
                      {summaryReferences.map((ref) => (
                        <span key={ref.id} className="mr-2 font-mono text-gray-300">
                          {ref.id}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </section>

            <section className="grid gap-6 md:grid-cols-2">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Shield className="w-6 h-6 text-purple-300" />
                  <div>
                    <p className="text-sm text-gray-400">Tech stack</p>
                    <p className="text-lg font-semibold">Languages & tooling</p>
                  </div>
                </div>
                <div className="space-y-3">
                  {['languages', 'frameworks', 'databases', 'tools'].map((key) => (
                    <div key={key}>
                      <p className="text-xs uppercase tracking-widest text-gray-500">{key}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {analysis.tech_stack[key as keyof typeof analysis.tech_stack]?.length ? (
                          analysis.tech_stack[key as keyof typeof analysis.tech_stack].map(
                            (value) => (
                              <span
                                key={value}
                                className="rounded-full border border-white/15 px-3 py-1 text-sm text-gray-200"
                              >
                                {value}
                              </span>
                            ),
                          )
                        ) : (
                          <span className="text-sm text-gray-500">No data</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Info className="w-6 h-6 text-sky-300" />
                  <div>
                    <p className="text-sm text-gray-400">Languages</p>
                    <p className="text-lg font-semibold">Lines of code</p>
                  </div>
                </div>
                <div className="space-y-3">
                  {Object.entries(analysis.metadata.languages).map(([lang, lines]) => (
                    <div key={lang}>
                      <div className="flex items-center justify-between text-sm text-gray-300">
                        <span>{lang}</span>
                        <span>{lines.toLocaleString()} LOC</span>
                      </div>
                      <div className="mt-2 h-2 rounded-full bg-white/10">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-sky-500 to-purple-500"
                          style={{
                            width: `${Math.min(
                              100,
                              (lines / analysis.metadata.total_lines) * 100 || 5,
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <div className="flex items-center gap-3 mb-6">
                <Shield className="w-6 h-6 text-red-300" />
                <div>
                  <p className="text-sm text-gray-400">Security & quality</p>
                  <p className="text-lg font-semibold">Findings</p>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {[analysis.security_findings, analysis.code_smells].map((group, idx) => (
                  <div key={idx} className="space-y-4">
                    {group.length === 0 && (
                      <p className="text-sm text-gray-500">No findings reported.</p>
                    )}
                    {group.map((finding) => (
                      <div
                        key={`${finding.title}-${finding.reference_id}`}
                        className="rounded-2xl border border-white/15 bg-white/5 p-4"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-semibold">{finding.title}</p>
                          <span
                            className={`rounded-full px-2 py-0.5 text-xs font-semibold ${severityColor(
                              finding.severity || finding.impact,
                            )}`}
                          >
                            {finding.severity || finding.impact || 'info'}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-gray-400">{finding.description}</p>
                        <p className="mt-3 text-xs text-gray-500">
                          Reference:{' '}
                          <span className="font-mono text-gray-300">{finding.reference_id}</span>
                        </p>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Code2 className="w-6 h-6 text-emerald-300" />
                  <div>
                    <p className="text-sm text-gray-400">Code samples</p>
                    <p className="text-lg font-semibold">Referenced snippets</p>
                  </div>
                </div>
                <div className="flex gap-3 overflow-x-auto pb-2">
                  {analysis.source_references.map((ref) => (
                    <button
                      key={ref.id}
                      onClick={() => setSelectedReference(ref)}
                      className={`rounded-2xl border px-3 py-2 text-sm font-mono transition ${
                        selectedReference?.id === ref.id
                          ? 'border-emerald-400/40 bg-emerald-400/10 text-emerald-100'
                          : 'border-white/10 bg-white/5 text-gray-400 hover:border-white/30'
                      }`}
                    >
                      {ref.id}
                    </button>
                  ))}
                </div>
                {selectedReference ? (
                  <div className="mt-4 rounded-2xl border border-white/10 bg-black/40 p-4 font-mono text-sm text-gray-200 max-h-96 overflow-auto">
                    <div className="mb-2 flex items-center justify-between text-xs text-gray-400">
                      <span>{selectedReference.file_path}</span>
                      <span>
                        L{selectedReference.start_line} - L{selectedReference.end_line}
                      </span>
                    </div>
                    <pre className="whitespace-pre-wrap text-xs leading-relaxed">
                      {selectedReference.snippet}
                    </pre>
                  </div>
                ) : (
                  <p className="mt-4 text-sm text-gray-500">Select a reference to view code.</p>
                )}
              </div>

              <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <ClipboardCheck className="w-6 h-6 text-yellow-300" />
                  <div>
                    <p className="text-sm text-gray-400">DevOps readiness</p>
                    <p className="text-lg font-semibold">CI/CD checklist</p>
                  </div>
                </div>
                <div className="space-y-3">
                  {analysis.devops_recommendations.map((rec) => (
                    <div
                      key={`${rec.title}-${rec.reference_id}`}
                      className="rounded-2xl border border-white/10 bg-white/5 p-4"
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-1">
                          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-semibold">{rec.title}</p>
                            <span className={`rounded-full border px-2 text-xs ${impactChip(rec.impact)}`}>
                              {rec.impact ?? 'info'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-400 mt-1">{rec.details || rec.description}</p>
                          <p className="mt-2 text-xs text-gray-500">
                            Evidence:{' '}
                            <span className="font-mono text-gray-300">{rec.reference_id}</span>
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <div className="flex items-center gap-3 mb-4">
                <Clock className="w-6 h-6 text-rose-300" />
                <div>
                  <p className="text-sm text-gray-400">Improvement plan</p>
                  <p className="text-lg font-semibold">Prioritized recommendations</p>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {analysis.improvement_plan.map((item) => (
                  <div
                    key={`${item.title}-${item.reference_id}`}
                    className="rounded-2xl border border-white/15 bg-white/5 p-4"
                  >
                    <div className="flex items-center justify-between text-sm">
                      <p className="font-semibold text-gray-100">{item.title}</p>
                      <span className={`rounded-full border px-2 text-xs ${impactChip(item.impact)}`}>
                        {item.impact ?? 'info'}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-gray-400">{item.details || item.description}</p>
                    <div className="mt-3 flex items-center gap-3 text-xs text-gray-500">
                      <span>Effort: {item.effort ?? 'n/a'}</span>
                      <span>Reference: {item.reference_id}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  )
}

