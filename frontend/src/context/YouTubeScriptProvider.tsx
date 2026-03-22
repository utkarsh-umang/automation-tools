import { useCallback, useMemo, useState, type ReactNode } from 'react'
import {
  creditsPerTerm,
  dailyCreditLimit,
  dailyCreditsUsed as initialDailyCreditsUsed,
  seedBatches,
  todaysBatchId as initialTodaysBatchId,
} from '@/data/mockData'
import { YouTubeScriptContext } from '@/context/youtubeScriptContext'
import type { Batch } from '@/types/batch'

function newId(): string {
  return `batch-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function YouTubeScriptProvider({ children }: { children: ReactNode }) {
  const [batches, setBatches] = useState<Batch[]>(() => seedBatches.map((b) => ({ ...b })))
  const [dailyCreditsUsed] = useState(initialDailyCreditsUsed)
  const [todaysBatchId] = useState<string | null>(initialTodaysBatchId)

  const derived = useMemo(() => {
    const creditsRemaining = dailyCreditLimit - dailyCreditsUsed
    const creditUsagePercent = (dailyCreditsUsed / dailyCreditLimit) * 100
    const isDailyLocked = todaysBatchId !== null
    const todaysBatchName =
      todaysBatchId === null ? null : batches.find((b) => b.id === todaysBatchId)?.name ?? null
    return {
      creditsRemaining,
      creditUsagePercent,
      isDailyLocked,
      todaysBatchName,
    }
  }, [batches, dailyCreditsUsed, todaysBatchId])

  const addBatch = useCallback(
    (input: { name: string; keyword: string; searchTerms: string[] }) => {
      const totalTerms = input.searchTerms.length
      const now = new Date().toISOString()
      const batch: Batch = {
        id: newId(),
        name: input.name.trim(),
        keyword: input.keyword.trim(),
        searchTerms: input.searchTerms,
        totalTerms,
        processedTerms: 0,
        status: 'queued',
        createdAt: now,
      }
      setBatches((prev) => [...prev, batch])
    },
    [],
  )

  const value = {
    batches,
    setBatches,
    addBatch,
    dailyCreditsUsed,
    todaysBatchId,
    dailyCreditLimit,
    creditsPerTerm,
    creditsRemaining: derived.creditsRemaining,
    creditUsagePercent: derived.creditUsagePercent,
    isDailyLocked: derived.isDailyLocked,
    todaysBatchName: derived.todaysBatchName,
  }

  return <YouTubeScriptContext.Provider value={value}>{children}</YouTubeScriptContext.Provider>
}
