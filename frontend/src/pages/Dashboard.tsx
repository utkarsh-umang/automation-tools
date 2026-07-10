import { useNavigate } from 'react-router-dom'
import { ToolCard } from '@/components/dashboard/ToolCard'
import { AppShell } from '@/components/layout/AppShell'
import { toolsForRole } from '@/config/tools'
import { useAuth } from '@/hooks/useAuth'

const youtubeWorkflowSteps = ['Create batch', 'Daily run', 'Track progress', 'Export']
const thumbnailWorkflowSteps = ['Your thumbnails', 'Create with AI', 'Curate & export']

function FeaturedWorkflowPanel({ label, steps }: { label: string; steps: string[] }) {
  return (
    <div
      className="flex w-full shrink-0 flex-col justify-center rounded-xl px-4 py-4 sm:max-w-xs sm:border-l"
      style={{
        borderColor: '#e5e7eb',
        background: 'linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(15,31,74,0.04) 100%)',
      }}
    >
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: '#6b7280' }}>
        {label}
      </p>
      <ol className="space-y-2">
        {steps.map((step, i) => (
          <li key={step} className="flex items-center gap-2 text-sm" style={{ color: '#111827' }}>
            <span
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold"
              style={{
                background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
                color: '#ffffff',
              }}
            >
              {i + 1}
            </span>
            {step}
          </li>
        ))}
      </ol>
    </div>
  )
}

export function Dashboard() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const tools = toolsForRole(user?.role)
  const youtubeTool = tools.find((t) => t.id === 'youtube-script')
  const thumbnailTool = tools.find((t) => t.id === 'thumbnail')
  const rest = tools.filter((t) => t.id !== 'youtube-script' && t.id !== 'thumbnail')

  return (
    <AppShell breadcrumb="Dashboard">
      <main className="mx-auto max-w-7xl px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold" style={{ color: '#0a0f1e' }}>
          Tools Workspace
        </h1>
        <p className="mt-1 text-sm" style={{ color: '#6b7280' }}>
          Internal AI-assisted workflows for outreach and production
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {youtubeTool && (
          <div className="md:col-span-2">
            <ToolCard
              title={youtubeTool.label}
              description={youtubeTool.description}
              tags={youtubeTool.tags}
              status="live"
              featured
              onClick={() => navigate(youtubeTool.path)}
            >
              <FeaturedWorkflowPanel label="Workflow preview" steps={youtubeWorkflowSteps} />
            </ToolCard>
          </div>
        )}

        {thumbnailTool && (
          <div className="md:col-span-2">
            <ToolCard
              title={thumbnailTool.label}
              description={thumbnailTool.description}
              tags={thumbnailTool.tags}
              status="live"
              featured
              onClick={() => navigate(thumbnailTool.path)}
            >
              <FeaturedWorkflowPanel label="Workflow preview" steps={thumbnailWorkflowSteps} />
            </ToolCard>
          </div>
        )}

        {rest.map((tool) => (
          <ToolCard
            key={tool.id}
            title={tool.label}
            description={tool.description}
            tags={tool.tags}
            status={tool.status === 'live' ? 'live' : 'planned'}
            onClick={() => navigate(tool.path)}
          />
        ))}
      </div>
    </main>
    </AppShell>
  )
}
