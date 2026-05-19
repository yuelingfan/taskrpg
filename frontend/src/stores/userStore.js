import { create } from 'zustand'

export const useUserStore = create((set) => ({
  user: null,
  token: localStorage.getItem('token') || null,
  isAuthenticated: !!localStorage.getItem('token'),

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setToken: (token) => set({ token, isAuthenticated: !!token }),

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ user: null, token: null, isAuthenticated: false })
  },

  // Restore session from localStorage on app init
  restoreSession: () => {
    const token = localStorage.getItem('token')
    const userJson = localStorage.getItem('user')
    if (token && userJson) {
      try {
        const user = JSON.parse(userJson)
        set({ user, token, isAuthenticated: true })
        return user
      } catch {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }
    return null
  },
}))
