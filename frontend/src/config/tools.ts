import type { UserRole } from '@/client'

export type ToolNavStatus = 'live' | 'soon'

export type ToolIconId = 'youtube' | 'book' | 'list' | 'pdf' | 'image' | 'chart'

export interface ToolDefinition {
  id: string
  label: string
  path: string
  status: ToolNavStatus
  description: string
  tags: string[]
  iconId: ToolIconId
  /** MEMBER accounts only ever see tools with adminOnly: false. ADMIN sees everything. */
  adminOnly: boolean
}

export const tools: ToolDefinition[] = [
  {
    id: 'youtube-script',
    label: 'YT List Creator',
    path: '/youtube-script',
    status: 'live',
    description: 'Find channels from search terms and extract contact emails across daily API quota.',
    tags: ['YouTube API', 'Email', 'Batches'],
    iconId: 'youtube',
    adminOnly: true,
  },
  {
    id: 'thumbnail',
    label: 'Thumbnail Creator',
    path: '/thumbnail',
    status: 'live',
    description: 'Thumbnail concepts and batch exports for short-form.',
    tags: ['Thumbnails', 'Creative'],
    iconId: 'image',
    adminOnly: false,
  },
  {
    id: 'hooks-analyzer',
    label: 'Hooks Analyzer',
    path: '/hooks-analyzer',
    status: 'soon',
    description: 'Deploy high-performance analysis on video hooks to maximize retention.',
    tags: ['Hooks', 'Analysis'],
    iconId: 'chart',
    adminOnly: true,
  },
  {
    id: 'podscan',
    label: 'Podscan Collab List',
    path: '/podscan',
    status: 'soon',
    description: 'Build a Podscan-style collab list from a YouTube channel for outreach (sheet + CSV export).',
    tags: ['Podcasts', 'Leads', 'Podscan'],
    iconId: 'list',
    adminOnly: true,
  },
  {
    id: 'library-lp',
    label: 'Library LP Creator',
    path: '/library-lp',
    status: 'soon',
    description: 'Generate landing pages from your content library templates.',
    tags: ['Landing pages', 'Content'],
    iconId: 'book',
    adminOnly: true,
  },
  {
    id: 'lead-magnet-pdf',
    label: 'Lead Magnet PDF',
    path: '/lead-magnet-pdf',
    status: 'soon',
    description: 'Create client-ready PDF lead magnets from outlines.',
    tags: ['PDF', 'Lead gen'],
    iconId: 'pdf',
    adminOnly: true,
  },
]

export function toolsForRole(role: UserRole | undefined): ToolDefinition[] {
  return role === 'ADMIN' ? tools : tools.filter((t) => !t.adminOnly)
}
