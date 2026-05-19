import { create } from 'zustand'

export const useAppStore = create((set, get) => ({
  currentUserId: null,
  setCurrentUserId: (id) => set({ currentUserId: id }),

  filter: 'all',
  setFilter: (filter) => set({ filter }),

  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
  updateTask: (id, updates) => set((state) => ({
    tasks: state.tasks.map(t => t.id === id ? { ...t, ...updates } : t)
  })),
  removeTask: (id) => set((state) => ({
    tasks: state.tasks.filter(t => t.id !== id)
  })),

  // AI 占星系统状态
  aiInput: '',
  setAiInput: (text) => set({ aiInput: text }),
  aiPendingTasks: [],
  setAiPendingTasks: (tasks) => {
    if (typeof tasks === 'function') {
      set((state) => ({ aiPendingTasks: tasks(state.aiPendingTasks) }))
    } else {
      set({ aiPendingTasks: tasks })
    }
  },
  clearAiPendingTasks: () => set({ aiPendingTasks: [] }),
  aiLoading: false,
  setAiLoading: (loading) => set({ aiLoading: loading }),
  aiReply: '',
  setAiReply: (reply) => set({ aiReply: reply }),
}))
