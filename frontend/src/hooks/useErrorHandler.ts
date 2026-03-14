import { useCallback } from 'react'

export function useErrorHandler() {
  return useCallback((error: unknown) => {
    console.error(error)
    // Optionally show toast, send to analytics, etc.
  }, [])
}
