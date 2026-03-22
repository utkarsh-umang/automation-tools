import { createContext } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import type { Batch } from '@/types/batch'

export interface YouTubeScriptContextValue {
  batches: Batch[]
  setBatches: Dispatch<SetStateAction<Batch[]>>
  addBatch: (input: { name: string; keyword: string; searchTerms: string[] }) => void
  dailyCreditsUsed: number
  todaysBatchId: string | null
  dailyCreditLimit: number
  creditsPerTerm: number
  creditsRemaining: number
  creditUsagePercent: number
  isDailyLocked: boolean
  todaysBatchName: string | null
}

export const YouTubeScriptContext = createContext<YouTubeScriptContextValue | null>(null)
