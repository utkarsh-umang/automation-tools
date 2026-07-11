import { useState } from 'react'
import { UserRole } from '@/client'
import { getApiErrorMessage, useCreateUserMutation, useUserListQuery } from '@/hooks/api/useUsersApi'

function formatWhen(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
  } catch {
    return iso
  }
}

export function AdminUsers() {
  const { data: users, isLoading, isError, error, refetch } = useUserListQuery()
  const createMutation = useCreateUserMutation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<UserRole>(UserRole.MEMBER)
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    setFormSuccess(null)
    if (!email.trim() || !password) {
      setFormError('Email and password are required.')
      return
    }
    try {
      await createMutation.mutateAsync({ email: email.trim(), password, role })
      setFormSuccess(`Created ${email.trim()} as ${role}.`)
      setEmail('')
      setPassword('')
      setRole(UserRole.MEMBER)
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold" style={{ color: '#0a0f1e' }}>
          Manage Users
        </h1>
        <p className="mt-1 text-sm" style={{ color: '#6b7280' }}>
          Create logins for your team. MEMBER accounts only ever see the Thumbnail Creator.
        </p>
      </div>

      <div
        className="mb-8 rounded-xl p-5"
        style={{ border: '1px solid #e5e7eb', backgroundColor: '#ffffff', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}
      >
        <h2 className="mb-4 text-base font-semibold" style={{ color: '#111827' }}>
          Create a new login
        </h2>
        <form onSubmit={(e) => void handleCreate(e)} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="teammate@example.com"
              className="w-full rounded-lg px-3 py-2.5 text-sm outline-none"
              style={{ border: '1px solid #e5e7eb', color: '#111827', backgroundColor: '#f9fafb' }}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
              Password
            </label>
            <input
              type="text"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Set a temporary password"
              className="w-full rounded-lg px-3 py-2.5 text-sm outline-none"
              style={{ border: '1px solid #e5e7eb', color: '#111827', backgroundColor: '#f9fafb' }}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
              Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="w-full rounded-lg px-3 py-2.5 text-sm outline-none"
              style={{ border: '1px solid #e5e7eb', color: '#111827', backgroundColor: '#f9fafb' }}
            >
              <option value={UserRole.MEMBER}>MEMBER (Thumbnail Creator only)</option>
              <option value={UserRole.ADMIN}>ADMIN (everything)</option>
            </select>
          </div>
          <div className="sm:col-span-3">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="rounded-lg px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
              style={{ backgroundColor: '#2563eb' }}
            >
              {createMutation.isPending ? 'Creating…' : 'Create login'}
            </button>
            {formError && (
              <p className="mt-2 text-sm" style={{ color: '#be123c' }}>
                {formError}
              </p>
            )}
            {formSuccess && (
              <p className="mt-2 text-sm" style={{ color: '#15803d' }}>
                {formSuccess}
              </p>
            )}
          </div>
        </form>
      </div>

      <div
        className="rounded-xl p-5"
        style={{ border: '1px solid #e5e7eb', backgroundColor: '#ffffff', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}
      >
        <h2 className="mb-4 text-base font-semibold" style={{ color: '#111827' }}>
          Existing logins
        </h2>
        {isLoading && <p className="text-sm" style={{ color: '#6b7280' }}>Loading…</p>}
        {isError && (
          <p className="text-sm" style={{ color: '#be123c' }}>
            {getApiErrorMessage(error)}{' '}
            <button type="button" className="underline" onClick={() => void refetch()}>
              Retry
            </button>
          </p>
        )}
        {!isLoading && !isError && users && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <th className="py-2 pr-4 font-medium" style={{ color: '#6b7280' }}>Email</th>
                  <th className="py-2 pr-4 font-medium" style={{ color: '#6b7280' }}>Role</th>
                  <th className="py-2 pr-4 font-medium" style={{ color: '#6b7280' }}>Active</th>
                  <th className="py-2 pr-4 font-medium" style={{ color: '#6b7280' }}>Created</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td className="py-2 pr-4" style={{ color: '#111827' }}>{u.email}</td>
                    <td className="py-2 pr-4" style={{ color: '#111827' }}>{u.role}</td>
                    <td className="py-2 pr-4" style={{ color: '#111827' }}>{u.is_active ? 'Yes' : 'No'}</td>
                    <td className="py-2 pr-4" style={{ color: '#6b7280' }}>{formatWhen(u.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  )
}
