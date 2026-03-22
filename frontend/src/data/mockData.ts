import type { Batch } from '@/types/batch'

export const dailyCreditLimit = 10_000
export const creditsPerTerm = 100

/** Edit these to demo the credit meter and daily lock banner. */
export const dailyCreditsUsed = 8_200

/** Batch that was triggered today — set to `null` to hide the daily lock banner. */
export const todaysBatchId: string | null = 'batch-running-1'

function buildRunningTermRows(): NonNullable<Batch['termRows']> {
  const terms = [
    'podcast host',
    'content creator',
    'youtube coaching',
    'video marketing',
    'brand storytelling',
    'interview format',
    'solo creator',
    'educational channel',
    'news commentary',
    'comedy shorts',
    'fitness vlog',
    'tech reviews',
    'cooking show',
    'travel vlog',
    'music reaction',
    'currently running term',
    'pending one',
    'pending two',
    'pending three',
  ]
  const rows = terms.map((term, i) => {
    if (i < 14) {
      return { term, creditsUsed: 100, status: 'done' as const }
    }
    if (i === 14) {
      return { term, creditsUsed: null as number | null, status: 'running' as const }
    }
    return { term, creditsUsed: null, status: 'pending' as const }
  })
  const order = (s: (typeof rows)[0]) => (s.status === 'done' ? 0 : s.status === 'running' ? 1 : 2)
  return [...rows].sort((a, b) => order(a) - order(b))
}

export const seedBatches: Batch[] = [
  {
    id: 'batch-running-1',
    name: 'Q1 Podcast Outreach',
    keyword: 'Podcasts',
    searchTerms: [],
    totalTerms: 18,
    processedTerms: 14,
    status: 'running',
    createdAt: '2025-03-18T09:00:00.000Z',
    termRows: buildRunningTermRows(),
  },
  {
    id: 'batch-paused-1',
    name: 'Creator Niches — Wave 2',
    keyword: 'Creators',
    searchTerms: [],
    totalTerms: 220,
    processedTerms: 100,
    status: 'paused',
    createdAt: '2025-03-15T14:20:00.000Z',
  },
  {
    id: 'batch-completed-1',
    name: 'Agency Partners Scan',
    keyword: 'Agencies',
    searchTerms: [],
    totalTerms: 45,
    processedTerms: 45,
    status: 'completed',
    createdAt: '2025-03-01T11:00:00.000Z',
    channelsFound: 128,
    emailsExtracted: 36,
  },
]
