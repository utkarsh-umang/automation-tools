import { createContext, useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { OpenAPI } from '@/client'
import type { AuthUser } from '@/types/auth'
import { getToken, removeToken, setToken } from '@/utils/token'

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user?: AuthUser) => void
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setTokenState] = useState<string | null>(null)
  const [user, setUser] = useState<AuthUser | null>(null)

  // Restore session from localStorage on mount
  useEffect(() => {
    const stored = getToken()
    if (stored) {
      OpenAPI.TOKEN = stored
      setTokenState(stored)
      // User details are stored alongside the token
      try {
        const storedUser = localStorage.getItem('auth_user')
        if (storedUser) {
          setUser(JSON.parse(storedUser) as AuthUser)
        }
      } catch {
        // ignore parse errors
      }
    }
  }, [])

  const login = useCallback((newToken: string, newUser?: AuthUser) => {
    setToken(newToken)
    OpenAPI.TOKEN = newToken
    setTokenState(newToken)
    if (newUser) {
      localStorage.setItem('auth_user', JSON.stringify(newUser))
      setUser(newUser)
    }
  }, [])

  const logout = useCallback(() => {
    removeToken()
    localStorage.removeItem('auth_user')
    OpenAPI.TOKEN = undefined
    setTokenState(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: token !== null,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
