import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import logo from '@/assets/logo.png'
import { ApiError, AuthService } from '@/client'
import { useAuth } from '@/hooks/useAuth'
import type { AuthUser } from '@/types/auth'
import { decodeTokenPayload } from '@/utils/token'

export function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () => AuthService.loginApiV1AuthLoginPost({ email, password }),
    onSuccess: (data) => {
      const payload = decodeTokenPayload(data.access_token)
      const user: AuthUser | undefined = payload
        ? {
            id: String(payload.sub ?? ''),
            email,
            role: 'MEMBER' as AuthUser['role'],
          }
        : undefined
      login(data.access_token, user)
      navigate('/', { replace: true })
    },
    onError: (err: unknown) => {
      if (err instanceof ApiError) {
        setErrorMsg(err.status === 401 ? 'Incorrect email or password.' : 'Something went wrong. Please try again.')
      } else {
        setErrorMsg('Unable to reach the server. Check your connection.')
      }
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErrorMsg(null)
    mutation.mutate()
  }

  return (
    <div className="flex min-h-screen" style={{ backgroundColor: '#0a0f1e' }}>
      {/* ── Left panel — brand ── */}
      <div
        className="relative hidden w-1/2 flex-col items-center justify-center overflow-hidden lg:flex"
        style={{
          background: 'linear-gradient(135deg, #0a0f1e 0%, #0f1f4a 55%, #0a0f1e 100%)',
        }}
      >
        {/* Blue glow orbs */}
        <div
          className="absolute"
          style={{
            width: 480,
            height: 480,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(37,99,235,0.25) 0%, transparent 70%)',
            top: '10%',
            left: '10%',
            pointerEvents: 'none',
          }}
        />
        <div
          className="absolute"
          style={{
            width: 300,
            height: 300,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(29,78,216,0.18) 0%, transparent 70%)',
            bottom: '8%',
            right: '5%',
            pointerEvents: 'none',
          }}
        />

        {/* Grid overlay */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              'linear-gradient(rgba(37,99,235,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(37,99,235,0.06) 1px, transparent 1px)',
            backgroundSize: '48px 48px',
          }}
        />

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center gap-6 px-12 text-center">
          <img src={logo} alt="Logo" className="h-28 w-28 rounded-2xl" />
          <div>
            <h1
              className="text-3xl font-bold tracking-tight"
              style={{ color: '#ffffff' }}
            >
              Automation Tools
            </h1>
            <p className="mt-2 text-base" style={{ color: 'rgba(255,255,255,0.45)' }}>
              Build, automate, and deploy — faster.
            </p>
          </div>
          {/* Decorative blue divider */}
          <div
            className="h-px w-24"
            style={{ background: 'linear-gradient(90deg, transparent, #2563eb, transparent)' }}
          />
          <p className="max-w-xs text-sm leading-relaxed" style={{ color: 'rgba(255,255,255,0.3)' }}>
            Streamline your workflows with a unified platform for team collaboration and automation.
          </p>
        </div>
      </div>

      {/* ── Right panel — form ── */}
      <div
        className="flex w-full flex-col items-center justify-center px-6 lg:w-1/2"
        style={{
          background: 'linear-gradient(160deg, #0d1526 0%, #111827 100%)',
        }}
      >
        {/* Mobile logo */}
        <div className="mb-8 flex items-center gap-3 lg:hidden">
          <img src={logo} alt="Logo" className="h-10 w-10 rounded-xl" />
          <span className="text-lg font-bold" style={{ color: '#ffffff' }}>
            Automation Tools
          </span>
        </div>

        {/* Card */}
        <div
          className="w-full max-w-sm rounded-2xl px-8 py-10"
          style={{
            backgroundColor: '#ffffff',
            boxShadow: '0 0 0 1px rgba(255,255,255,0.06), 0 24px 48px rgba(0,0,0,0.5)',
          }}
        >
          <div className="mb-7">
            <h2 className="text-xl font-semibold" style={{ color: '#0a0f1e' }}>
              Welcome back
            </h2>
            <p className="mt-1 text-sm" style={{ color: '#6b7280' }}>
              Sign in to continue
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-sm font-medium"
                style={{ color: '#111827' }}
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="block w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
                style={{
                  border: '1px solid #e5e7eb',
                  color: '#111827',
                  backgroundColor: '#f9fafb',
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#2563eb'
                  e.target.style.backgroundColor = '#ffffff'
                  e.target.style.boxShadow = '0 0 0 3px rgba(37,99,235,0.12)'
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#e5e7eb'
                  e.target.style.backgroundColor = '#f9fafb'
                  e.target.style.boxShadow = 'none'
                }}
              />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium"
                style={{ color: '#111827' }}
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="block w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
                style={{
                  border: '1px solid #e5e7eb',
                  color: '#111827',
                  backgroundColor: '#f9fafb',
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#2563eb'
                  e.target.style.backgroundColor = '#ffffff'
                  e.target.style.boxShadow = '0 0 0 3px rgba(37,99,235,0.12)'
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#e5e7eb'
                  e.target.style.backgroundColor = '#f9fafb'
                  e.target.style.boxShadow = 'none'
                }}
              />
            </div>

            {/* Error */}
            {errorMsg && (
              <div
                className="flex items-start gap-2 rounded-lg px-3 py-2.5 text-sm"
                style={{
                  backgroundColor: '#fff1f2',
                  border: '1px solid #fecdd3',
                  color: '#be123c',
                }}
              >
                <svg className="mt-0.5 h-4 w-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                {errorMsg}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={mutation.isPending}
              className="mt-1 w-full rounded-lg px-4 py-2.5 text-sm font-semibold text-white transition-all disabled:opacity-60"
              style={{
                background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                boxShadow: '0 1px 2px rgba(37,99,235,0.4), 0 4px 12px rgba(37,99,235,0.2)',
              }}
              onMouseEnter={(e) => {
                if (!mutation.isPending) {
                  ;(e.currentTarget).style.background = 'linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%)'
                  ;(e.currentTarget).style.boxShadow = '0 1px 2px rgba(37,99,235,0.5), 0 6px 16px rgba(37,99,235,0.3)'
                }
              }}
              onMouseLeave={(e) => {
                if (!mutation.isPending) {
                  ;(e.currentTarget).style.background = 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)'
                  ;(e.currentTarget).style.boxShadow = '0 1px 2px rgba(37,99,235,0.4), 0 4px 12px rgba(37,99,235,0.2)'
                }
              }}
            >
              {mutation.isPending ? 'Signing in…' : 'Sign in →'}
            </button>
          </form>
        </div>

        <p className="mt-6 text-xs" style={{ color: 'rgba(255,255,255,0.2)' }}>
          Account access is managed by your administrator.
        </p>
      </div>
    </div>
  )
}
