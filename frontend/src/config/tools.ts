export type ToolNavStatus = 'live' | 'soon'

export type ToolIconId = 'youtube' | 'book' | 'list' | 'pdf' | 'image'

export interface ToolDefinition {
  id: string
  label: string
  path: string
  status: ToolNavStatus
  description: string
  tags: string[]
  iconId: ToolIconId
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
  },
  {
    id: 'thumbnail',
    label: 'Thumbnail Creator',
    path: '/thumbnail',
    status: 'live',
    description: 'Thumbnail concepts and batch exports for short-form.',
    tags: ['Thumbnails', 'Creative'],
    iconId: 'image',
  },
  {
    id: 'podscan',
    label: 'Podscan Collab List',
    path: '/podscan',
    status: 'live',
    description: 'Build a Podscan-style collab list from a YouTube channel for outreach (sheet + CSV export).',
    tags: ['Podcasts', 'Leads', 'Podscan'],
    iconId: 'list',
  },
  {
    id: 'library-lp',
    label: 'Library LP Creator',
    path: '/library-lp',
    status: 'soon',
    description: 'Generate landing pages from your content library templates.',
    tags: ['Landing pages', 'Content'],
    iconId: 'book',
  },
  {
    id: 'lead-magnet-pdf',
    label: 'Lead Magnet PDF',
    path: '/lead-magnet-pdf',
    status: 'soon',
    description: 'Create client-ready PDF lead magnets from outlines.',
    tags: ['PDF', 'Lead gen'],
    iconId: 'pdf',
  },
]
