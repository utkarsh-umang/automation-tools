import { useContext } from 'react'
import { YouTubeScriptContext } from '@/context/youtubeScriptContext'

export function useYouTubeScript() {
  const ctx = useContext(YouTubeScriptContext)
  if (!ctx) {
    throw new Error('useYouTubeScript must be used within YouTubeScriptProvider')
  }
  return ctx
}
