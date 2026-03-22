import type { UserRole } from '@/client'

export interface AuthUser {
  id: string
  email: string
  role: UserRole
}

export interface AuthState {
  user: AuthUser | null
  token: string | null
}
