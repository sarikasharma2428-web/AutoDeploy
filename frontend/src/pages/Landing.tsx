import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, ShieldCheck, Sparkles, TerminalSquare } from 'lucide-react'

const features = [
  {
    title: 'Deep Code Intelligence',
    description: 'RAG-enhanced LLM insights over every file, chunk, and dependency.',
    icon: <Sparkles className="w-6 h-6 text-purple-400" />,
  },
  {
    title: 'Security-First Auditing',
    description: 'Deterministic findings with source references ready for compliance reports.',
    icon: <ShieldCheck className="w-6 h-6 text-emerald-400" />,
  },
  {
    title: 'Developer Friendly Output',
    description: 'Actionable recommendations, code samples, and CI/CD checklists.',
    icon: <TerminalSquare className="w-6 h-6 text-sky-400" />,
  },
]

export default function Landing() {
  const navigate = useNavigate()
  const [repoUrl, setRepoUrl] = useState('https://github.com/octocat/Hello-World')
  const [showModal, setShowModal] = useState(false)

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault()
    if (!repoUrl) return
    setShowModal(false)
    navigate(`/analyze?repo=${encodeURIComponent(repoUrl)}`)
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-hidden relative">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.25),_transparent_40%),_radial-gradient(circle_at_top_right,_rgba(147,51,234,0.25),_transparent_35%)] pointer-events-none" />

      <header className="relative z-10 mx-auto max-w-6xl px-6 py-12">
        <motion.nav
          className="flex items-center justify-between mb-16"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="text-2xl font-semibold tracking-tight">
            Auto<span className="text-sky-400">DeployX</span>
          </div>
          <button
            className="hidden md:inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20 hover:bg-white/20 transition"
            onClick={() => navigate('/analyze')}
          >
            Open Analyzer
            <ArrowRight className="w-4 h-4" />
          </button>
        </motion.nav>

        <div className="grid lg:grid-cols-[1.05fr_0.95fr] gap-12 items-center">
          <motion.section
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 border border-white/20 text-xs uppercase tracking-[0.3em] mb-6 text-gray-300">
              RAG powered · Deterministic
            </p>
            <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6">
              Audit any repository with{' '}
              <span className="bg-gradient-to-r from-sky-400 via-purple-400 to-rose-400 bg-clip-text text-transparent">
                production-ready AI
              </span>
            </h1>
            <p className="text-lg md:text-xl text-gray-300 mb-10 max-w-2xl">
              AutoDeployX clones, chunks, embeds, and interrogates your Git repos with Qdrant-backed RAG pipelines.
              Every finding ships with a source reference and deployment-ready DevOps plan.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                className="inline-flex items-center justify-center gap-3 px-6 py-4 rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 font-semibold text-lg shadow-lg shadow-sky-500/30 hover:scale-[1.01] transition"
                onClick={() => setShowModal(true)}
              >
                Start Analysis
                <ArrowRight className="w-5 h-5" />
              </button>
              <button
                className="px-6 py-4 rounded-2xl border border-white/20 hover:border-white/60 transition bg-white/5 font-semibold"
                onClick={() => navigate('/analyze')}
              >
                Live Demo
              </button>
            </div>
            <div className="mt-10 flex flex-wrap gap-6 text-sm text-gray-400">
              <div>
                <p className="text-2xl font-bold text-white">40+</p>
                Coverage checks
              </div>
              <div>
                <p className="text-2xl font-bold text-white">10s</p>
                Avg. discovery
              </div>
              <div>
                <p className="text-2xl font-bold text-white">100%</p>
                Referenced claims
              </div>
            </div>
          </motion.section>

          <motion.section
            className="relative p-6 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-xl shadow-2xl"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="absolute -top-3 right-8 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/40 text-emerald-200 text-xs font-semibold">
              Live pipeline view
            </div>
            <div className="space-y-6">
              {['Clone & parse', 'Chunk & embed', 'RAG prompt', 'LLM verdict'].map((step, idx) => (
                <motion.div
                  key={step}
                  className="flex items-center gap-4 p-4 rounded-2xl bg-white/3 border border-white/10"
                  initial={{ opacity: 0, x: 30 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15 * idx }}
                >
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-sky-500/40 to-purple-500/40 flex items-center justify-center text-white font-semibold">
                    {idx + 1}
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Stage {idx + 1}</p>
                    <p className="font-medium text-white">{step}</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-white/40 ml-auto" />
                </motion.div>
              ))}
            </div>
          </motion.section>
        </div>

        <motion.section
          className="grid md:grid-cols-3 gap-6 mt-20"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0, y: 40 },
            visible: { opacity: 1, y: 0, transition: { staggerChildren: 0.1 } },
          }}
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-lg hover:border-white/40 transition"
            >
              <div className="mb-4 p-3 rounded-xl bg-white/10 inline-flex">{feature.icon}</div>
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </motion.section>
      </header>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
          <div className="bg-gray-900 border border-white/15 rounded-3xl w-full max-w-lg p-8 relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-white"
            >
              ×
            </button>
            <h2 className="text-2xl font-semibold mb-2">Analyze a repository</h2>
            <p className="text-sm text-gray-400 mb-6">We will clone, chunk, embed, and audit in one click.</p>
            <form className="space-y-4" onSubmit={handleStart}>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Repository URL</label>
                <input
                  type="url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="w-full rounded-2xl bg-white/5 border border-white/20 px-4 py-3 focus:outline-none focus:border-sky-400"
                  placeholder="https://github.com/org/project"
                  required
                />
              </div>
              <button
                type="submit"
                className="w-full px-6 py-4 rounded-2xl font-semibold bg-gradient-to-r from-emerald-500 to-sky-500 hover:opacity-90 transition flex items-center justify-center gap-3"
              >
                Launch analyzer
                <ArrowRight className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
