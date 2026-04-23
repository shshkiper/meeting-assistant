import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from '@/utils/api'

interface User {
  id: string
  email: string
  full_name: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const data = await authApi.login(email, password)
          localStorage.setItem('access_token', data.access_token)
          set({ token: data.access_token, isLoading: false })
          await get().fetchMe()
        } finally {
          set({ isLoading: false })
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        set({ user: null, token: null })
      },

      fetchMe: async () => {
        try {
          const user = await authApi.me()
          set({ user })
        } catch {
          get().logout()
        }
      },
    }),
    { name: 'auth-store', partialize: (s) => ({ token: s.token }) },
  ),
)
