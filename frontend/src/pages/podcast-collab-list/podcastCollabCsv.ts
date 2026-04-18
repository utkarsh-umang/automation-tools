import type { PodcastCollabRow } from './mockData'

function escapeCsvCell(value: string): string {
  if (/[",\n\r]/.test(value)) return `"${value.replace(/"/g, '""')}"`
  return value
}

function rowsToCsv(rows: PodcastCollabRow[]): string {
  const header = ['Podcast name', 'Host / show', 'Relevance %', 'Podcast URL', 'Notes']
  const lines = [
    header.map(escapeCsvCell).join(','),
    ...rows.map((r) =>
      [r.podcastName, r.host, String(r.relevancePct), r.podcastUrl, r.notes].map(escapeCsvCell).join(','),
    ),
  ]
  return lines.join('\r\n')
}

export function downloadPodcastCollabCsv(rows: PodcastCollabRow[], filename: string) {
  const blob = new Blob([rowsToCsv(rows)], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
