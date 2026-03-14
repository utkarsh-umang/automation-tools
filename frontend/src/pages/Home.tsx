import { useHealthQuery } from '@/hooks/api/useHealthQuery'
import { Loader } from '@/components/Loader'

export function Home() {
  const { data, isLoading, error } = useHealthQuery()

  return (
    <main className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-3xl font-semibold">Welcome</h1>
      <p className="text-gray-600 dark:text-gray-400">
        React + TypeScript + Vite frontend template
      </p>
      <section className="mt-6 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800">
        <h2 className="text-sm font-medium text-gray-600 dark:text-gray-400">
          API health check
        </h2>
        {isLoading && (
          <div className="mt-2 flex justify-center">
            <Loader />
          </div>
        )}
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">
            API unreachable: {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        )}
        {data !== undefined && (
          <div className="mt-2 text-sm text-green-600 dark:text-green-400">
            <p>API connected. Status: {data.status}</p>
            <p className="mt-1 text-gray-600 dark:text-gray-400">
              Postgres: {data.postgres} · Mongo: {data.mongo} · Redis: {data.redis}
            </p>
          </div>
        )}
      </section>
    </main>
  )
}
