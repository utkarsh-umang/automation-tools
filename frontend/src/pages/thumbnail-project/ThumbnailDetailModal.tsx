import {
  X,
  CheckCircle2,
  Sparkles,
  Download,
  Loader2,
  ChevronDown,
  Images,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { ThumbnailFeedbackRequest } from '@/client'
import {
  getApiErrorMessage,
  isThumbnailJobTerminal,
  useSelectThumbnailCandidateMutation,
  useThumbnailFeedbackMutation,
  useThumbnailHistoryQuery,
  useThumbnailJobQuery,
} from '@/hooks/api/useThumbnailApi'

type ThumbnailDetailModalProps = {
  jobId: string
  onClose: () => void
}

function modelLabel(model: string | null | undefined) {
  if (model === 'gptimage') return 'GPT Image'
  if (model === 'nanobanana') return 'Nano Banana'
  if (model === 'fluxkontext') return 'Flux Kontext'
  return model ?? '—'
}

export function ThumbnailDetailModal({ jobId, onClose }: ThumbnailDetailModalProps) {
  // Iteration history entries are clickable — clicking one re-points this same
  // modal at that job instead of the one it was opened with.
  const [viewedJobId, setViewedJobId] = useState(jobId)
  useEffect(() => {
    setViewedJobId(jobId)
  }, [jobId])

  const { data: job, isLoading, isError, error, refetch } = useThumbnailJobQuery(viewedJobId)
  const { data: historyData } = useThumbnailHistoryQuery(viewedJobId)
  const feedbackMutation = useThumbnailFeedbackMutation()
  const selectMutation = useSelectThumbnailCandidateMutation()

  const [feedbackText, setFeedbackText] = useState('')
  const [feedbackModel, setFeedbackModel] = useState<ThumbnailFeedbackRequest.model>(
    ThumbnailFeedbackRequest.model.FLUXKONTEXT,
  )
  const [feedbackError, setFeedbackError] = useState<string | null>(null)
  const [feedbackDone, setFeedbackDone] = useState(false)
  const [selectError, setSelectError] = useState<string | null>(null)

  const canRequestRevision =
    job && isThumbnailJobTerminal(job.status) && job.status === 'completed' && Boolean(job.result_url)
  const isAwaitingSelection = job?.status === 'awaiting_selection' && Boolean(job.candidate_urls?.length)

  async function handleFeedbackSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFeedbackError(null)
    setFeedbackDone(false)
    if (!feedbackText.trim()) {
      setFeedbackError('Enter feedback for the revision.')
      return
    }
    try {
      await feedbackMutation.mutateAsync({
        jobId: viewedJobId,
        body: {
          feedback: feedbackText.trim(),
          model: feedbackModel,
        },
      })
      setFeedbackText('')
      setFeedbackDone(true)
    } catch (err) {
      setFeedbackError(getApiErrorMessage(err))
    }
  }

  async function handleSelectCandidate(url: string) {
    setSelectError(null)
    try {
      await selectMutation.mutateAsync({ jobId: viewedJobId, body: { selected_url: url } })
    } catch (err) {
      setSelectError(getApiErrorMessage(err))
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0f1f4a]/60 backdrop-blur-md p-4 sm:p-8 animate-in fade-in duration-200">
      <div className="bg-white rounded-[2rem] shadow-2xl max-w-5xl w-full flex min-h-0 flex-col md:flex-row overflow-hidden max-h-[90vh] ring-1 ring-white/20">
        {/* Left panel — fixed-height thumbnail + scrollable accordion below */}
        <div className="relative flex w-full flex-col bg-[#0a0f1e] md:w-[60%] md:overflow-y-auto">
          <div
            className="pointer-events-none absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_center,rgba(37,99,235,0.8)_0%,transparent_100%)]"
            aria-hidden
          />

          {/* Generated image(s) — fixed height, never shrinks */}
          <div className="relative z-10 flex min-h-[min(46vh,400px)] shrink-0 items-center justify-center px-8 py-8">
            {isLoading && (
              <Loader2 className="w-10 h-10 text-blue-400 animate-spin" aria-label="Loading" />
            )}
            {isError && (
              <p className="text-white text-sm text-center px-4">
                {getApiErrorMessage(error)}{' '}
                <button type="button" className="underline" onClick={() => void refetch()}>
                  Retry
                </button>
              </p>
            )}
            {!isLoading && !isError && isAwaitingSelection && (
              <div className="w-full">
                <p className="mb-3 text-center text-sm font-semibold text-white">
                  Pick the version you want to keep
                </p>
                <div className="grid grid-cols-2 gap-4">
                  {job?.candidate_urls?.map((url, i) => (
                    <div key={url} className="flex flex-col items-center gap-2">
                      <img
                        src={url}
                        alt={`Candidate ${i + 1}`}
                        className="h-56 w-full rounded-2xl object-contain shadow-2xl ring-1 ring-white/10"
                      />
                      <button
                        type="button"
                        onClick={() => void handleSelectCandidate(url)}
                        disabled={selectMutation.isPending}
                        className="rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold px-4 py-2"
                      >
                        {selectMutation.isPending ? 'Saving…' : `Use this one`}
                      </button>
                    </div>
                  ))}
                </div>
                {selectError && (
                  <p className="mt-3 text-center text-xs text-red-300">{selectError}</p>
                )}
              </div>
            )}
            {!isLoading && !isError && !isAwaitingSelection && job?.result_url && (
              <img
                src={job.result_url}
                alt="Generated thumbnail"
                className="h-full w-full rounded-2xl object-contain shadow-2xl ring-1 ring-white/10"
              />
            )}
            {!isLoading && !isError && !isAwaitingSelection && job && !job.result_url && (
              <div className="text-center text-gray-300 text-sm px-6">
                <p className="font-semibold text-white mb-1">{job.status}</p>
                {job.error && <p className="text-red-300">{job.error}</p>}
                {!job.error && <p>No image yet. This job may still be processing.</p>}
              </div>
            )}
          </div>

          {/* Source images accordion — lives below the thumbnail, column scrolls to reveal */}
          {!isLoading && !isError && job && (job.reference_image_url || (job.base_image_urls?.length ?? 0) > 0) && (
            <div className="relative z-10 shrink-0 border-t border-white/10 px-6 pb-6 pt-0 sm:px-8 sm:pb-8">
              <details className="group rounded-2xl border border-white/15 bg-white/6 backdrop-blur-sm">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3.5 text-left text-sm font-semibold text-gray-100 transition-colors hover:bg-white/6 [&::-webkit-details-marker]:hidden">
                  <span className="flex items-center gap-2.5">
                    <Images className="h-4 w-4 shrink-0 text-blue-300" aria-hidden />
                    Source images
                    <span className="text-xs font-normal text-gray-500">(reference &amp; base)</span>
                  </span>
                  <ChevronDown
                    className="h-5 w-5 shrink-0 text-gray-400 transition-transform duration-200 group-open:rotate-180"
                    aria-hidden
                  />
                </summary>
                <div className="space-y-6 border-t border-white/10 px-4 pb-5 pt-4 sm:px-5 sm:pb-6">
                  {job.reference_image_url && (
                    <div>
                      <p className="mb-2.5 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                        Reference
                      </p>
                      <img
                        src={job.reference_image_url}
                        alt="Reference"
                        className="max-h-52 w-auto max-w-full rounded-xl object-contain ring-1 ring-white/10"
                        loading="lazy"
                      />
                    </div>
                  )}
                  {job.base_image_urls && job.base_image_urls.length > 0 && (
                    <div>
                      <p className="mb-2.5 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                        Base images
                      </p>
                      <div className="flex flex-wrap gap-3">
                        {job.base_image_urls.map((url, i) => (
                          <img
                            key={`${url}-${i}`}
                            src={url}
                            alt={`Base ${i + 1}`}
                            className="h-32 w-auto max-w-[calc(50%-0.375rem)] rounded-lg object-cover ring-1 ring-white/10 sm:max-w-[calc(33.333%-0.5rem)]"
                            loading="lazy"
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </details>
            </div>
          )}
        </div>

        <div className="flex min-h-0 w-full flex-col overflow-y-auto p-8 md:w-[40%] md:max-h-[90vh] md:p-10">
          <div className="flex justify-between items-start mb-8">
            <div>
              <div className="text-blue-600 text-xs font-black tracking-widest mb-1.5 uppercase">Job details</div>
              <h2 className="text-[22px] font-bold text-gray-900 leading-tight pr-4">
                {job?.title ?? 'Thumbnail'}
              </h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2.5 bg-gray-50 hover:bg-gray-100 rounded-full text-gray-500 transition-colors shrink-0"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-6 flex-1">
            <div>
              <label className="block text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2.5">
                Status
              </label>
              <div className="bg-[#f8faff] text-[#0f1f4a] p-4 rounded-2xl font-semibold border border-blue-100/50 leading-relaxed text-[15px]">
                {job?.status ?? '—'}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2.5">
                  Title in image
                </label>
                <div className="bg-[#f8faff] text-[#0f1f4a] p-3.5 rounded-2xl font-bold border border-blue-100/50 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-blue-600" />
                  {job?.include_title === true ? 'Yes' : job?.include_title === false ? 'No' : '—'}
                </div>
              </div>
              <div>
                <label className="block text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2.5">
                  Model
                </label>
                <div className="bg-[#f8faff] text-[#0f1f4a] p-3.5 rounded-2xl font-bold border border-blue-100/50 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  {modelLabel(job?.model)}
                </div>
              </div>
            </div>

            {job?.creative_comments && (
              <div>
                <label className="block text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2.5">
                  Creative notes
                </label>
                <div className="bg-[#f8faff] p-4 rounded-2xl border border-blue-100/50 text-sm text-gray-800 leading-relaxed">
                  {job.creative_comments}
                </div>
              </div>
            )}

            {historyData && historyData.jobs.length > 0 && (
              <div>
                <label className="block text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2.5">
                  Iteration history
                </label>
                <ul className="space-y-2 max-h-40 overflow-y-auto">
                  {historyData.jobs.map((h) => (
                    <li key={h.id}>
                      <button
                        type="button"
                        onClick={() => setViewedJobId(h.id)}
                        className="flex w-full items-center gap-2 text-xs rounded-lg px-3 py-2 border transition-colors"
                        style={
                          h.id === viewedJobId
                            ? { backgroundColor: '#eff6ff', borderColor: '#bfdbfe' }
                            : { backgroundColor: '#f9fafb', borderColor: '#f3f4f6' }
                        }
                      >
                        <span className="font-semibold text-gray-700">#{h.iteration}</span>
                        <span className="text-gray-500 uppercase">{h.status}</span>
                        {h.id === viewedJobId && (
                          <span className="text-blue-600 font-medium ml-auto">viewing</span>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <form className="space-y-3 border-t border-gray-100 pt-6" onSubmit={handleFeedbackSubmit}>
              <label className="block text-[11px] font-black text-gray-400 uppercase tracking-widest">
                Request revision
              </label>
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                disabled={!canRequestRevision || feedbackMutation.isPending}
                rows={3}
                placeholder={
                  canRequestRevision
                    ? 'Describe what to change in the next version…'
                    : 'Available when the job completes successfully.'
                }
                className="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm text-gray-900 disabled:bg-gray-100 disabled:text-gray-500"
              />
              <div className="flex flex-wrap gap-2 items-center">
                <select
                  value={feedbackModel}
                  onChange={(e) =>
                    setFeedbackModel(e.target.value as ThumbnailFeedbackRequest.model)
                  }
                  disabled={!canRequestRevision || feedbackMutation.isPending}
                  className="rounded-lg border border-gray-200 px-2 py-1.5 text-xs font-medium"
                >
                  <option value={ThumbnailFeedbackRequest.model.FLUXKONTEXT}>Flux Kontext</option>
                  <option value={ThumbnailFeedbackRequest.model.GPTIMAGE}>GPT Image</option>
                  <option value={ThumbnailFeedbackRequest.model.NANOBANANA}>Nano Banana</option>
                </select>
                <button
                  type="submit"
                  disabled={!canRequestRevision || feedbackMutation.isPending}
                  className="rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold px-4 py-2"
                >
                  {feedbackMutation.isPending ? 'Sending…' : 'Submit feedback'}
                </button>
              </div>
              {feedbackError && <p className="text-xs text-red-600">{feedbackError}</p>}
              {feedbackDone && (
                <p className="text-xs text-green-700">Revision queued. Check the list for the new job.</p>
              )}
            </form>
          </div>

          <div className="mt-8 pt-8 border-t border-gray-100 flex gap-4">
            {job?.result_url && (
              <a
                href={job.result_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-4 rounded-2xl shadow-[0_8px_20px_-4px_rgba(37,99,235,0.4)] transition-all flex items-center justify-center gap-2.5 active:scale-[0.98]"
              >
                <Download className="w-5 h-5" /> Open image
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
