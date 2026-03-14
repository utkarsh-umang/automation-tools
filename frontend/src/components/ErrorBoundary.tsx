import { type ReactNode, Component } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="flex min-h-48 flex-col items-center justify-center gap-4 p-8">
          <h2 className="text-xl font-medium text-red-600 dark:text-red-400">
            Something went wrong
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {this.state.error?.message ?? 'An unexpected error occurred.'}
          </p>
        </div>
      )
    }
    return this.props.children
  }
}
