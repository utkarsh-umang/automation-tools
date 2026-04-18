export const MOCK_SHEET_URL =
  'https://docs.google.com/spreadsheets/d/mock_podcast_collab_list_2026/edit?usp=sharing'

export const MOCK_CHANNEL_SNIPPET =
  'Weekly conversations with founders and operators building in public — B2B SaaS, growth, and creator economy.'

export interface PodcastCollabRow {
  id: string
  podcastName: string
  host: string
  relevancePct: number
  podcastUrl: string
  notes: string
}

/** Shared row set used by every mock list (same data, two cards). */
export const MOCK_ROWS: PodcastCollabRow[] = [
  {
    id: '1',
    podcastName: 'Build in Public Weekly',
    host: 'Alex Rivera',
    relevancePct: 94,
    podcastUrl: 'https://podcasts.example.com/build-in-public',
    notes: 'Audience overlap on SaaS founders; strong guest-booking cadence.',
  },
  {
    id: '2',
    podcastName: 'Operator Radio',
    host: 'Jordan Kim',
    relevancePct: 89,
    podcastUrl: 'https://podcasts.example.com/operator-radio',
    notes: 'Focus on GTM and partnerships — good fit for collab episodes.',
  },
  {
    id: '3',
    podcastName: 'The Creator Ledger',
    host: 'Sam Patel',
    relevancePct: 86,
    podcastUrl: 'https://podcasts.example.com/creator-ledger',
    notes: 'Monetization + newsletter cross-promo mentioned in show notes.',
  },
  {
    id: '4',
    podcastName: 'B2B Unpacked',
    host: 'Morgan Lee',
    relevancePct: 82,
    podcastUrl: 'https://podcasts.example.com/b2b-unpacked',
    notes: 'Enterprise buyers; slightly narrower but high-intent listeners.',
  },
  {
    id: '5',
    podcastName: 'Growth Patterns',
    host: 'Casey Nguyen',
    relevancePct: 79,
    podcastUrl: 'https://podcasts.example.com/growth-patterns',
    notes: 'Experiment-heavy format; good for co-marketing with your channel.',
  },
]

export type PodcastListStatus = 'ready'

export interface MockPodcastList {
  id: string
  name: string
  channelUrl: string
  createdAt: string
  status: PodcastListStatus
  sheetUrl: string
  /** Same underlying rows for both mock cards. */
  rows: PodcastCollabRow[]
}

export const MOCK_PODCAST_LISTS: MockPodcastList[] = [
  {
    id: 'mock-list-1',
    name: 'Scale Brands — Collab outreach',
    channelUrl: 'https://www.youtube.com/@ScaleBrandsLab',
    createdAt: '2026-01-15T14:30:00.000Z',
    status: 'ready',
    sheetUrl: MOCK_SHEET_URL,
    rows: MOCK_ROWS,
  },
  {
    id: 'mock-list-2',
    name: 'Scale Brands — Collab outreach (copy)',
    channelUrl: 'https://www.youtube.com/@ScaleBrandsLab',
    createdAt: '2026-01-16T09:00:00.000Z',
    status: 'ready',
    sheetUrl: MOCK_SHEET_URL,
    rows: MOCK_ROWS,
  },
]

export function getMockPodcastListById(id: string): MockPodcastList | undefined {
  return MOCK_PODCAST_LISTS.find((l) => l.id === id)
}
