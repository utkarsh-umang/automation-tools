import { useState } from 'react'
import { Link2, Zap, Clock, PlusCircle, History, Clapperboard, Activity, CheckCircle2, ChevronRight, Play, ExternalLink, ArrowRight, ArrowLeft, Loader2, Edit3, SpellCheck } from 'lucide-react'

type ViewState = 'initial' | 'loading' | 'transcript' | 'transcript-view' | 'results'

export function HooksAnalyzer() {
  const [view, setView] = useState<ViewState>('initial')
  const [activeTab, setActiveTab] = useState<'new' | 'history'>('new')
  const [url, setUrl] = useState('')

  const handleAnalyze = () => {
    if (!url) return
    setView('loading')
    setTimeout(() => {
      setView('transcript')
    }, 5000)
  }

  const renderInitial = () => {
    return (
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main Analysis Card */}
        <div className="col-span-1 flex flex-col items-center justify-center rounded-xl bg-white p-8 shadow-sm border border-slate-200 lg:col-span-2">
          <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-50">
            <Clapperboard className="h-8 w-8 text-blue-600" />
          </div>
          
          <h2 className="mb-2 text-xl font-bold text-slate-900">Initialize Deep Analysis</h2>
          <p className="mb-8 text-center text-sm text-slate-500 max-w-md">
            Paste a YouTube or Social Media link below to extract hooks, patterns, and retention triggers.
          </p>

          <div className="w-full max-w-md">
            <label className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">
              Paste Video Link
            </label>
            <div className="relative mb-4">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <Link2 className="h-5 w-5 text-slate-400" />
              </div>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="block w-full rounded-lg border border-slate-200 bg-slate-50 p-3 pl-10 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                placeholder="https://youtube.com/watch?v=..."
              />
            </div>
            
            <button 
              onClick={handleAnalyze}
              disabled={!url}
              className="mb-4 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-700 p-3 text-sm font-bold text-white transition-colors hover:bg-blue-800 shadow-md shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Zap className="h-4 w-4" />
              Analyze
            </button>
            
          </div>
        </div>

        {/* Pipeline Sidebar */}
        <div className="col-span-1 rounded-xl bg-white p-6 shadow-sm border border-slate-200 h-fit">
          <div className="mb-6 flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-600" />
            <h3 className="font-bold text-slate-900">Analysis Pipeline</h3>
          </div>

          <div className="relative space-y-6">
            <div className="absolute left-[15px] top-[30px] bottom-[30px] w-px bg-slate-100"></div>
            
            {[
              {
                step: 1,
                title: 'Content Extraction',
                desc: 'Retrieving transcript and frame data',
                active: true,
              },
              {
                step: 2,
                title: 'Hook Identification',
                desc: 'Pinpointing the first 3-10 seconds',
                active: false,
              },
              {
                step: 3,
                title: 'Pattern Scoring',
                desc: 'A/B testing against viral database',
                active: false,
              },
              {
                step: 4,
                title: 'Final Report',
                desc: 'Generating actionable refinements',
                active: false,
              },
            ].map((item) => (
              <div key={item.step} className="relative flex items-start gap-4">
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                    item.active
                      ? 'bg-blue-600 text-white z-10'
                      : 'bg-slate-100 text-slate-500 z-10'
                  }`}
                >
                  {item.step}
                </div>
                <div className="pt-1.5">
                  <h4 className={`text-sm font-semibold ${item.active ? 'text-slate-900' : 'text-slate-500'}`}>
                    {item.title}
                  </h4>
                  <p className="text-xs text-slate-400">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const renderHistory = () => {
    const historyData = [
      {
        id: 1,
        title: 'The Future of AI in 2024',
        url: 'https://youtube.com/watch?v=Qx3...',
        date: 'Oct 24, 2023 • 14:32',
      },
      {
        id: 2,
        title: 'Extreme Minimalism House Tour',
        url: 'https://youtube.com/watch?v=Fj9...',
        date: 'Oct 23, 2023 • 09:15',
      },
      {
        id: 3,
        title: 'Why Coffee is Actually Good for You',
        url: 'https://youtube.com/watch?v=p4v...',
        date: 'Oct 22, 2023 • 18:04',
      }
    ]

    return (
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-bold text-slate-900">Recent Completed Batches</h3>
          <button className="text-sm font-semibold text-blue-600 hover:text-blue-700">
            View All History
          </button>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="border-b border-slate-200 px-6 py-4">Video Title</th>
                  <th className="border-b border-slate-200 px-6 py-4">Video URL</th>
                  <th className="border-b border-slate-200 px-6 py-4">Date Processed</th>
                  <th className="border-b border-slate-200 px-6 py-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {historyData.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      <div className="flex items-center gap-3">
                        <Clapperboard className="h-5 w-5 text-slate-400" />
                        {row.title}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-500 font-medium">
                      <a href="#" className="hover:text-blue-600 transition-colors">{row.url}</a>
                    </td>
                    <td className="px-6 py-4 text-slate-500 font-medium">{row.date}</td>
                    <td className="px-6 py-4">
                      <button 
                        onClick={() => setView('results')}
                        className="font-bold text-blue-700 hover:text-blue-800"
                      >
                        View Results
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }

  const renderLoading = () => {
    return (
      <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-slate-900/40 backdrop-blur-sm">
        <div className="flex flex-col items-center rounded-2xl bg-white p-10 shadow-2xl">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mb-6" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Analyzing Video</h2>
          <p className="text-sm text-slate-500">Extracting transcript and identifying hooks...</p>
        </div>
      </div>
    )
  }

  const renderTranscript = () => {
    return (
      <div>
        {/* Header with breadcrumbs */}
        <div className="mb-6 flex flex-col gap-2">
          <div className="text-sm text-slate-500 flex items-center gap-2">
            Analysis <ChevronRight className="h-4 w-4" /> <span className="font-semibold text-blue-600">Transcript Preview</span>
          </div>
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold text-slate-900">Processing Transcript...</h1>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold uppercase tracking-wider text-slate-600 border border-slate-200">
              STEP 2 OF 3
            </span>
          </div>
          <p className="text-sm text-slate-500">
            Review the raw text generation before identifying high-performing hooks.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Transcript Content */}
          <div className="col-span-1 flex flex-col rounded-xl bg-white shadow-sm border border-slate-200 lg:col-span-2 overflow-hidden h-fit">
            <div className="flex items-center justify-between border-b border-slate-100 p-4">
              <div className="flex items-center gap-6">
                <button className="flex items-center gap-2 text-sm font-semibold text-blue-600">
                  <Edit3 className="h-4 w-4" /> Edit Text
                </button>
                <button className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-700">
                  <SpellCheck className="h-4 w-4" /> Auto-Correct
                </button>
              </div>
              <div className="flex items-center gap-3 text-sm font-semibold text-slate-500">
                Confidence Score: 98%
                <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full w-[98%] bg-emerald-500"></div>
                </div>
              </div>
            </div>
            
            <div className="flex-1 p-6 text-sm text-slate-700 leading-relaxed overflow-y-auto max-h-[500px]">
              <div className="mb-6 flex gap-4">
                <span className="shrink-0 font-mono text-blue-400 font-semibold">[00:00:00]</span>
                <p>Welcome everyone to today's deep dive into the world of creative strategy. Today we're going to break down exactly how you can scale your personal brand using vertical video.</p>
              </div>
              <div className="mb-6 flex gap-4">
                <span className="shrink-0 font-mono text-blue-400 font-semibold">[00:00:15]</span>
                <p>The number one mistake I see people making is they focus way too much on the production quality and not enough on the hook itself. If your hook doesn't stop the scroll, the rest of your video literally doesn't matter.</p>
              </div>
              <div className="mb-6 flex gap-4">
                <span className="shrink-0 font-mono text-blue-400 font-semibold">[00:00:42]</span>
                <p>Think about it. You've got approximately 1.7 seconds to grab attention. That is shorter than the attention span of a goldfish, though that study has actually been debunked, the principle still holds true in the digital economy.</p>
              </div>
              <div className="mb-6 flex gap-4">
                <span className="shrink-0 font-mono text-blue-400 font-semibold">[00:01:10]</span>
                <p>Let's look at three specific frameworks for viral hooks. Framework number one: The Negative Constraint. 'Stop doing X and do Y instead' format that completely rewires how your audience thinks about a problem.</p>
              </div>
            </div>

            {view === 'transcript' && (
              <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Activity className="h-4 w-4" />
                  Review the transcript above for any critical transcription errors.
                </div>
                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => setView('initial')}
                    className="rounded-lg border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={() => setView('results')}
                    className="flex items-center gap-2 rounded-lg bg-blue-700 px-6 py-2.5 text-sm font-bold text-white hover:bg-blue-800"
                  >
                    Confirm and Find Clips <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="col-span-1 space-y-6">
            {/* Top right card - URL */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-200">
              <div className="relative mb-4 aspect-video w-full overflow-hidden rounded-lg bg-slate-900">
                <div className="absolute inset-0 flex items-center justify-center opacity-50">
                  <div className="grid w-full h-full grid-cols-3 gap-1 p-2">
                    <div className="col-span-3 rounded bg-blue-500/20"></div>
                    <div className="col-span-2 rounded bg-emerald-500/20"></div>
                    <div className="col-span-1 rounded bg-purple-500/20"></div>
                  </div>
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 shadow-lg cursor-pointer">
                    <Play className="h-5 w-5 fill-current text-white ml-1" />
                  </div>
                </div>
              </div>
              <h3 className="mb-1 font-bold text-slate-900">Mastering Content Strategy</h3>
              <p className="text-xs text-slate-500 mb-4">Source: YouTube</p>
              
              <div className="border-t border-slate-100 pt-4">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Original URL</p>
                <a 
                  href={url || "https://youtube.com/watch?v=Xj2kL90-Po"} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center justify-between gap-2 p-3 rounded-lg bg-slate-50 border border-slate-100 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700 group transition-colors"
                >
                  <span className="text-sm font-medium text-slate-600 group-hover:text-blue-700 truncate">
                    {url || "https://youtube.com/watch?v=Xj2kL90-Po"}
                  </span>
                  <ExternalLink className="h-4 w-4 text-slate-400 shrink-0 group-hover:text-blue-600" />
                </a>
              </div>
            </div>

            {/* Workflow Preview Card */}
            <div className="rounded-xl bg-slate-50 p-6 shadow-inner border border-slate-200/60">
              <h3 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-500">Workflow Preview</h3>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-white mt-0.5">
                    <CheckCircle2 className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">URL Processing</h4>
                    <p className="text-xs text-slate-500">Video downloaded and audio extracted</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white mt-0.5">
                    <span className="text-xs font-bold">2</span>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-blue-700">Transcript Preview</h4>
                    <p className="text-xs text-slate-500">Reviewing raw text content for accuracy</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 opacity-50">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-500 mt-0.5">
                    <span className="text-xs font-bold">3</span>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-700">Hook Analysis</h4>
                    <p className="text-xs text-slate-500">AI identifying 30-60s viral segments</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderResults = () => {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm text-slate-500">
              Projects <ChevronRight className="h-3 w-3" /> Hooks Analysis #829 <ChevronRight className="h-3 w-3" /> <span className="font-semibold text-blue-600">Viral Clips</span>
            </div>
            <h1 className="text-3xl font-bold text-slate-900">Viral Clip Recommendations</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-500">
              We found 5 high-performing hooks from this 1-hour podcast. AI-powered extraction based on emotional triggers, retention probability, and platform trends.
            </p>
          </div>
          <button 
            onClick={() => setView('transcript-view')}
            className="flex shrink-0 items-center gap-2 rounded-lg bg-white border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            <Activity className="h-4 w-4" /> Show the transcript
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-2 max-w-2xl">
          <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-50">
              <Clapperboard className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500">Clips Identified</p>
              <p className="text-lg font-bold text-slate-900">05 Results</p>
            </div>
          </div>
          <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-50">
              <Clock className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500">Avg. Clip Length</p>
              <p className="text-lg font-bold text-slate-900">01:12 Min</p>
            </div>
          </div>
        </div>

        {/* Identified Hooks List */}
        <div className="space-y-6">
          {[
            {
              id: 1,
              title: 'The "Success Myth" Debunk',
              probability: '94%',
              badge: 'LIVE READY',
              badgeColor: 'bg-emerald-100 text-emerald-700',
              duration: '04:12 - 05:45',
              why: 'Strong emotional hook and high retention potential. The speaker challenges a common industry belief within the first 5 seconds, creating an immediate cognitive itch that forces the viewer to stay for the resolution.',
            },
            {
              id: 2,
              title: 'The Revenue Breakdown Disclosure',
              probability: '89%',
              badge: 'HIGH CONVERSION',
              badgeColor: 'bg-emerald-100 text-emerald-700',
              duration: '12:20 - 13:18',
              why: 'Transparent data sharing is a high-performing content pillar. The visual representation of actual numbers during this segment makes it perfect for TikTok/Shorts overlays and educational reels.',
            },
            {
              id: 3,
              title: 'The "Golden Tool" Reveal',
              probability: '82%',
              badge: 'EDUCATIONAL',
              badgeColor: 'bg-slate-100 text-slate-600',
              duration: '21:05 - 22:20',
              why: 'Promises a specific actionable solution to a problem established earlier. This provides immense standalone value, ideal for saving/bookmarking behavior on social platforms.',
            },
            {
              id: 4,
              title: 'The Turning Point Story',
              probability: '88%',
              badge: 'STORYTELLING',
              badgeColor: 'bg-blue-100 text-blue-700',
              duration: '35:10 - 36:40',
              why: 'Highly relatable personal anecdote. Vulnerability early in the clip builds strong para-social connection, leading to a much higher completion rate and shares.',
            },
            {
              id: 5,
              title: 'The Controversial Opinion',
              probability: '91%',
              badge: 'HIGH ENGAGEMENT',
              badgeColor: 'bg-orange-100 text-orange-700',
              duration: '48:30 - 49:55',
              why: 'Polarizing statement that naturally drives comments and debate. This segment plays perfectly into algorithm metrics for boosting organic reach through user interaction.',
            }
          ].map((hook) => (
            <div key={hook.id} className="flex flex-col rounded-xl bg-white p-6 shadow-sm border border-slate-200 transition-all hover:border-blue-200 hover:shadow-md">
              
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="rounded bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-700">
                    Clip #{hook.id}
                  </span>
                  <span className="text-xs font-medium text-slate-500">
                    Viral Probability: {hook.probability}
                  </span>
                </div>
                <span className={`rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider ${hook.badgeColor}`}>
                  {hook.badge}
                </span>
              </div>

              <h3 className="mb-2 text-xl font-bold text-slate-900">{hook.title}</h3>
              
              <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-blue-600">
                <Clock className="h-4 w-4" /> {hook.duration}
              </div>

              <div className="rounded-lg bg-slate-50 p-4 border border-slate-100">
                <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">WHY IT WORKS</h4>
                <p className="text-sm text-slate-700 leading-relaxed">{hook.why}</p>
              </div>
              
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <>
      {view === 'loading' && renderLoading()}
      
      <div className="mx-auto max-w-6xl p-6 lg:p-8">
        {view === 'initial' && (
          <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Hooks Analyzer Dashboard</h1>
              <p className="mt-1 text-sm text-slate-500">
                Deploy high-performance analysis on video hooks to maximize retention.
              </p>
            </div>
          </div>
        )}
        
        {view === 'initial' && (
          <div className="mb-6 flex items-center gap-6 border-b border-slate-200">
            <button 
              onClick={() => setActiveTab('new')}
              className={`flex items-center gap-2 border-b-2 pb-3 text-sm font-semibold transition-colors ${activeTab === 'new' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
            >
              <PlusCircle className="h-4 w-4" />
              Analyze New Video
            </button>
            <button 
              onClick={() => setActiveTab('history')}
              className={`flex items-center gap-2 border-b-2 pb-3 text-sm font-semibold transition-colors ${activeTab === 'history' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
            >
              <History className="h-4 w-4" />
              Completed Batches
            </button>
          </div>
        )}

        {view === 'initial' && activeTab === 'new' && renderInitial()}
        {view === 'initial' && activeTab === 'history' && renderHistory()}
        {(view === 'transcript' || view === 'transcript-view') && renderTranscript()}
        {view === 'results' && renderResults()}

        {view !== 'initial' && (
          <div className="mt-8 border-t border-slate-200 pt-6">
            <button 
              onClick={() => setView(view === 'results' || view === 'transcript-view' ? 'results' : 'initial')}
              className="flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-slate-800"
            >
              {view === 'transcript-view' ? (
                <>
                  <ArrowLeft className="h-4 w-4" /> Back to Results
                </>
              ) : (
                <>
                  <ArrowLeft className="h-4 w-4" /> Back to Dashboard
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </>
  )
}
