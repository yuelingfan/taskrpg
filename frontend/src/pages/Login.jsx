import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../lib/api'
import { useUserStore } from '../stores/userStore'
import { useAppStore } from '../stores/appStore'

export default function Login() {
  const navigate = useNavigate()
  const [isRegister, setIsRegister] = useState(false)
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')

  const setUser = useUserStore((s) => s.setUser)
  const setToken = useUserStore((s) => s.setToken)
  const setCurrentUserId = useAppStore((s) => s.setCurrentUserId)

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setToken(data.access_token)
      setUser(data.user)
      setCurrentUserId(data.user.id)
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      navigate('/')
    },
    onError: (err) => {
      setError(err.response?.data?.detail || '登录失败')
    },
  })

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      setToken(data.access_token)
      setUser(data.user)
      setCurrentUserId(data.user.id)
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      navigate('/')
    },
    onError: (err) => {
      setError(err.response?.data?.detail || '注册失败')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    if (!name.trim()) {
      setError('请输入冒险者名称')
      return
    }
    if (!password.trim()) {
      setError('请输入密钥')
      return
    }

    if (isRegister) {
      if (password !== confirmPassword) {
        setError('两次输入的密码不一致')
        return
      }
      registerMutation.mutate({ name: name.trim(), password })
    } else {
      loginMutation.mutate({ name: name.trim(), password })
    }
  }

  const isPending = loginMutation.isPending || registerMutation.isPending

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,#2a1f10,transparent_60%)] opacity-60" />

      <div className="relative w-full max-w-md px-6">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold tracking-[0.3em] text-[#d4af37] mb-2">AURORA</h1>
          <p className="text-sm text-[#b89b5e]">冒险者成长系统</p>
          <div className="w-16 h-px bg-[#d4af37]/30 mx-auto mt-4" />
        </div>

        <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-8 shadow-[0_0_40px_rgba(212,175,55,0.05)]">
          <h2 className="text-xl font-bold text-[#e7d7b7] text-center mb-6">
            {isRegister ? '创建冒险者身份' : '欢迎回来，冒险者'}
          </h2>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-[#b89b5e] mb-1.5">冒险者名称</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="输入你的名称..."
                className="w-full px-4 py-3 bg-[#050505] border border-[#d4af37]/20 rounded-xl text-[#e7d7b7] placeholder-[#b89b5e]/40 focus:outline-none focus:border-[#d4af37]/50 transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm text-[#b89b5e] mb-1.5">密钥（密码）</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="输入密码..."
                className="w-full px-4 py-3 bg-[#050505] border border-[#d4af37]/20 rounded-xl text-[#e7d7b7] placeholder-[#b89b5e]/40 focus:outline-none focus:border-[#d4af37]/50 transition-colors"
              />
            </div>

            {isRegister && (
              <div>
                <label className="block text-sm text-[#b89b5e] mb-1.5">确认密钥</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="再次输入密码..."
                  className="w-full px-4 py-3 bg-[#050505] border border-[#d4af37]/20 rounded-xl text-[#e7d7b7] placeholder-[#b89b5e]/40 focus:outline-none focus:border-[#d4af37]/50 transition-colors"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={isPending}
              className="w-full py-3 bg-[#d4af37]/10 text-[#d4af37] rounded-xl border border-[#d4af37]/30 hover:bg-[#d4af37]/20 disabled:opacity-50 transition-colors font-medium mt-2"
            >
              {isPending ? '请稍候...' : isRegister ? '创建身份' : '进入冒险'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsRegister(!isRegister)
                setError('')
                setConfirmPassword('')
              }}
              className="text-sm text-[#b89b5e] hover:text-[#d4af37] transition-colors"
            >
              {isRegister ? '已有身份？直接登录' : '没有身份？立即注册'}
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-[#b89b5e]/50 mt-8">
          TaskRPG - AI驱动的冒险者任务系统
        </p>
      </div>
    </div>
  )
}
