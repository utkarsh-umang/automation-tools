export type BatchStatus = 'queued' | 'running' | 'paused' | 'completed'

export type TermRowStatus = 'done' | 'running' | 'pending'

export interface TermProgressRow {
  term: string
  creditsUsed: number | null
  status: TermRowStatus
}

export interface Batch {
  id: string
  name: string
  keyword: string
  searchTerms: string[]
  totalTerms: number
  processedTerms: number
  status: BatchStatus
  createdAt: string
  termRows?: TermProgressRow[]
  channelsFound?: number
  emailsExtracted?: number
}
