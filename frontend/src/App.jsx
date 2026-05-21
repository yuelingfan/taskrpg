import { BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { useEffect, useState, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import TaskList from './pages/TaskList'
import PlanList from './pages/PlanList'
import Profile from './pages/Profile'
import Login from './pages/Login'
import { useAppStore } from './stores/appStore'
import { useUserStore } from './stores/userStore'
import { taskApi, aiApi } from './lib/api'
import clsx from 'clsx'

// 打字机效果组件（完成后渲染 Markdown）
function TypewriterText({ text, speed = 15 }) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)
  const indexRef = useRef(0)

  useEffect(() => {
    setDisplayed('')
    setDone(false)
    indexRef.current = 0

    const timer = setInterval(() => {
      if (indexRef.current < text.length) {
        indexRef.current += 1
        setDisplayed(text.slice(0, indexRef.current))
      } else {
        clearInterval(timer)
        setDone(true)
      }
    }, speed)

    return () => clearInterval(timer)
  }, [text, speed])

  if (done) {
    return (
      <div className="prose prose-invert prose-sm max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
      </div>
    )
  }

  return (
    <span className="text-sm text-[#e7d7b7] whitespace-pre-wrap">
      {displayed}
      <span className="inline-block w-0.5 h-4 bg-[#d4af37] ml-0.5 animate-pulse" />
    </span>
  )
}

// AI 思考步骤组件
function ThinkingSteps({ steps }) {
  if (!steps || steps.length === 0) return null

  const stepIcons = {
    tool: '🔧',
    observation: '📋',
    error: '⚠️',
    thought: '💭',
  }

  return (
    <div className="mb-2 space-y-1">
      {steps.map((step, idx) => (
        <div
          key={idx}
          className={clsx(
            'flex items-start gap-1.5 text-[11px] px-2 py-1 rounded',
            step.type === 'error' ? 'text-red-400/80 bg-red-400/5' : 'text-[#b89b5e]/70'
          )}
        >
          <span className="mt-0.5">{stepIcons[step.type] || '•'}</span>
          <span className="flex-1 truncate">{step.content}</span>
        </div>
      ))}
    </div>
  )
}

const NAV_ITEMS = [
  { name: '任务卷轴', path: '/', icon: '📜' },
  { name: '冒险计划', path: '/plans', icon: '🗺️' },
  { name: '角色属性', path: '/profile', icon: '👤' },
  { name: '技能树', path: '/skills', icon: '🌳' },
  { name: '装备栏', path: '/equipment', icon: '⚔️' },
  { name: '成就', path: '/achievements', icon: '🏆' },
]

function AuthGuard({ children }) {
  const { isAuthenticated, restoreSession } = useUserStore()
  const location = useLocation()

  useEffect(() => {
    restoreSession()
  }, [])

  if (!isAuthenticated && location.pathname !== '/login') {
    return <Navigate to="/login" replace />
  }

  return children
}

function InitData() {
  const { user, isAuthenticated } = useUserStore()
  const { currentUserId, setCurrentUserId, setTasks } = useAppStore()

  const { data: tasksData } = useQuery({
    queryKey: ['tasks', currentUserId],
    queryFn: () => taskApi.list(currentUserId),
    enabled: !!currentUserId,
  })

  useEffect(() => {
    if (user?.id && !currentUserId) {
      setCurrentUserId(user.id)
    }
  }, [user, currentUserId, setCurrentUserId])

  useEffect(() => {
    if (tasksData) {
      setTasks(tasksData)
    }
  }, [tasksData, setTasks])

  return null
}

function Sidebar() {
  const { user, logout } = useUserStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="col-span-2 bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-4 shadow-lg">
      {/* Logo */}
      <div className="text-center mb-6">
        <h1 className="text-lg font-bold tracking-widest text-[#d4af37]">AURORA</h1>
        <p className="text-[10px] text-[#b89b5e]">冒险者成长系统</p>
      </div>

      {/* Avatar */}
      <div className="text-center mb-6">
        <div className="w-16 h-16 mx-auto rounded-full border-2 border-[#d4af37] bg-[#1a140a] flex items-center justify-center text-2xl">
          {user?.name?.[0] || 'V'}
        </div>
        <div className="mt-2 font-semibold text-[#d4af37]">
          {user?.name || 'Voyager'}
        </div>
        <div className="text-xs text-[#b89b5e]">Adventurer Class</div>
      </div>

      {/* Navigation */}
      <nav className="space-y-2 text-sm">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all border border-transparent',
                isActive
                  ? 'bg-[#d4af37]/10 border-[#d4af37]/30 text-[#d4af37] shadow-[0_0_10px_rgba(212,175,55,0.15)]'
                  : 'text-[#b89b5e] hover:bg-[#d4af37]/10 hover:text-[#d4af37]'
              )
            }
          >
            <span>{item.icon}</span>
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="mt-6 pt-4 border-t border-[#d4af37]/20">
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-[#b89b5e] hover:bg-red-500/10 hover:text-red-400 border border-transparent hover:border-red-500/30 transition-colors text-sm"
        >
          <span>🚪</span>
          <span>退出登录</span>
        </button>
      </div>
    </div>
  )
}

function TopBar() {
  const { user } = useUserStore()

  const level = user?.level || 1
  const exp = user?.exp || 0
  const expNeeded = level * 100

  return (
    <div className="flex justify-between items-center mb-6">
      <div>
        <h2 className="text-2xl font-bold text-[#e7d7b7]">
          {getGreeting()}，冒险者
        </h2>
        <p className="text-[#b89b5e] text-sm mt-1">完成任务以提升角色属性与战斗力</p>
      </div>
      <div className="flex items-center gap-4">
        <div className="px-4 py-2 rounded-xl border border-[#d4af37]/30 bg-[#0c0c0c] shadow-[0_0_20px_rgba(212,175,55,0.15)] flex items-center gap-3">
          <span className="text-[#b89b5e] text-sm">LV. {level}</span>
          <div className="w-24 h-2 bg-[#1a140a] rounded overflow-hidden">
            <div
              className="h-full bg-[#d4af37] rounded transition-all duration-500"
              style={{ width: `${(exp / expNeeded) * 100}%` }}
            />
          </div>
          <span className="text-[#d4af37] text-sm">{exp}/{expNeeded}</span>
        </div>

        {/* 属性面板 */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-[#d4af37]/20 bg-[#0c0c0c]">
          <span className="text-xs" title="力量">⚔️ {user?.stats?.str_value ?? 10}</span>
          <span className="text-xs" title="智力">🧠 {user?.stats?.int_value ?? 10}</span>
          <span className="text-xs" title="耐力">❤️ {user?.stats?.sta_value ?? 10}</span>
          <span className="text-xs" title="魅力">✨ {user?.stats?.cha_value ?? 10}</span>
        </div>

        <div className="w-10 h-10 rounded-full border border-[#d4af37]/40 bg-gradient-to-br from-[#1a140a] to-[#000]" />
      </div>
    </div>
  )
}

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return '清晨好'
  if (hour < 18) return '午后好'
  return '夜幕临'
}

function RightPanel() {
  const { user } = useUserStore()
  const currentUserId = useAppStore((s) => s.currentUserId)
  const setCurrentUserId = useAppStore((s) => s.setCurrentUserId)
  const aiInput = useAppStore((s) => s.aiInput)
  const setAiInput = useAppStore((s) => s.setAiInput)
  const aiLoading = useAppStore((s) => s.aiLoading)
  const setAiLoading = useAppStore((s) => s.setAiLoading)
  const addTask = useAppStore((s) => s.addTask)
  const queryClient = useQueryClient()
  const sessionDropdownRef = useRef(null)
  const [messages, setMessages] = useState([])
  const [aiSessionId, setAiSessionId] = useState(null)
  const [sessions, setSessions] = useState([])
  const [showSessions, setShowSessions] = useState(false)

  // 点击外部关闭会话下拉
  useEffect(() => {
    function handleClickOutside(e) {
      if (sessionDropdownRef.current && !sessionDropdownRef.current.contains(e.target)) {
        setShowSessions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const stats = user?.stats || { str_value: 10, int_value: 10, sta_value: 10, cha_value: 10 }

  const attributes = [
    { name: '力量', value: stats.str_value, icon: '💪' },
    { name: '智力', value: stats.int_value, icon: '🧠' },
    { name: '耐力', value: stats.sta_value, icon: '⚡' },
    { name: '专注', value: stats.cha_value, icon: '✨' },
  ]

  const typeMap = {
    learning: { label: '学习', color: 'text-blue-400', bg: 'bg-blue-400/10' },
    work: { label: '工作', color: 'text-orange-400', bg: 'bg-orange-400/10' },
    exercise: { label: '运动', color: 'text-green-400', bg: 'bg-green-400/10' },
    social: { label: '社交', color: 'text-pink-400', bg: 'bg-pink-400/10' },
    other: { label: '其他', color: 'text-[#b89b5e]', bg: 'bg-[#b89b5e]/10' },
  }

  const priorityMap = {
    low: { label: '低', color: 'text-gray-400' },
    medium: { label: '中', color: 'text-[#b89b5e]' },
    high: { label: '高', color: 'text-orange-400' },
    urgent: { label: '紧急', color: 'text-red-400' },
  }

  // 加载会话列表
  useEffect(() => {
    if (currentUserId) {
      aiApi.listSessions(currentUserId).then(setSessions).catch(() => {})
    }
  }, [currentUserId])

  // 加载历史消息
  useEffect(() => {
    if (aiSessionId) {
      aiApi.getMessages(aiSessionId).then((msgs) => {
        // 过滤掉 system 消息和 tool 调用
        const filtered = msgs.filter((m) => m.role === 'user' || m.role === 'ai')
        setMessages(filtered)
      }).catch(() => {
        setMessages([])
      })
    } else {
      setMessages([])
    }
  }, [aiSessionId])

  const chatMutation = useMutation({
    mutationFn: ({ message, userId, sessionId }) => aiApi.chat(message, userId, sessionId),
    onMutate: () => {
      setAiLoading(true)
    },
    onSuccess: (data) => {
      setAiLoading(false)
      if (data.session_id) {
        setAiSessionId(data.session_id)
      }
      // 如果后端返回了新的 user_id（自动创建用户），更新前端
      if (data.user_id && data.user_id !== currentUserId) {
        setCurrentUserId(data.user_id)
      }
      setMessages((prev) => [
        ...prev,
        { role: 'ai', content: data.reply, steps: data.steps || [] },
      ])
      setAiInput('')
      // 刷新任务列表（Agent 可能创建了任务）
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
    onError: (err) => {
      setAiLoading(false)
      setMessages((prev) => [
        ...prev,
        { role: 'ai', content: err.response?.data?.detail || '召唤失败，请稍后重试' },
      ])
    },
  })

  const handleSummon = () => {
    if (!aiInput.trim() || !currentUserId) return
    const userMsg = aiInput.trim()
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    chatMutation.mutate({ message: userMsg, userId: currentUserId, sessionId: aiSessionId })
  }

  const handleCreateTask = async (task) => {
    if (!currentUserId) return
    let mainTask = null
    try {
      // 创建主任务
      mainTask = await taskApi.create({
        user_id: currentUserId,
        title: task.title,
        description: task.description,
        priority: task.priority,
        task_type: task.task_type,
        deadline: task.deadline ? new Date(task.deadline).toISOString() : null,
        exp_reward: task.exp_reward || 10,
      })
      addTask(mainTask)
    } catch (err) {
      alert(err.response?.data?.detail || '创建主任务失败')
      return
    }

    // 创建子任务（失败不影响主任务）
    if (task.subtasks?.length > 0 && mainTask) {
      const failedSubs = []
      for (const sub of task.subtasks) {
        try {
          const subTask = await taskApi.create({
            user_id: currentUserId,
            parent_id: mainTask.id,
            title: sub.title,
            priority: sub.priority || 'medium',
            task_type: task.task_type,
            exp_reward: 5,
          })
          addTask(subTask)
        } catch (err) {
          failedSubs.push(sub.title || '未命名子任务')
        }
      }
      if (failedSubs.length > 0) {
        alert(`主任务已创建，但以下子任务创建失败：${failedSubs.join('、')}`)
      }
    }

    // 从 pending 中移除
    setAiPendingTasks((prev) => prev.filter((t) => t.title !== task.title))
  }

  return (
    <div className="col-span-3 space-y-6">
      {/* 属性面板 */}
      <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-6">
        <h3 className="text-[#d4af37] mb-4 font-semibold">角色属性</h3>
        <div className="space-y-3">
          {attributes.map((attr) => (
            <div key={attr.name} className="mb-2">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#b89b5e]">{attr.icon} {attr.name}</span>
                <span className="text-[#e7d7b7]">{attr.value}</span>
              </div>
              <div className="h-2 bg-[#1a140a] rounded">
                <div
                  className="h-2 bg-[#d4af37] rounded transition-all"
                  style={{ width: `${attr.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI 占星系统 - 聊天卡片 */}
      <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl flex flex-col" style={{ maxHeight: 520 }}>
        {/* 标题 */}
        <div className="p-4 border-b border-[#d4af37]/10 flex justify-between items-start">
          <div>
            <h3 className="text-[#d4af37] font-semibold">🔮 AI 任务导师</h3>
            <p className="text-[10px] text-[#b89b5e] mt-0.5">
              {aiSessionId ? '会话已保存 · 刷新后保留' : '新对话'}
            </p>
          </div>
          <div className="relative" ref={sessionDropdownRef}>
            <button
              onClick={() => setShowSessions(!showSessions)}
              className="text-xs text-[#b89b5e] hover:text-[#d4af37] transition-colors px-2 py-1 rounded border border-[#d4af37]/20 hover:border-[#d4af37]/40"
            >
              会话 ▼
            </button>
            {showSessions && (
              <div className="absolute right-0 top-8 w-48 bg-[#0b0b0b] border border-[#d4af37]/20 rounded-lg shadow-lg z-10 overflow-hidden">
                <button
                  onClick={() => {
                    setAiSessionId(null)
                    setMessages([])
                    setShowSessions(false)
                  }}
                  className="w-full text-left px-3 py-2 text-xs text-[#d4af37] hover:bg-[#d4af37]/10 border-b border-[#d4af37]/10"
                >
                  + 新建对话
                </button>
                {sessions.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => {
                      setAiSessionId(s.id)
                      setShowSessions(false)
                    }}
                    className={clsx(
                      'w-full text-left px-3 py-2 text-xs hover:bg-[#d4af37]/10 truncate',
                      aiSessionId === s.id ? 'text-[#d4af37] bg-[#d4af37]/5' : 'text-[#b89b5e]'
                    )}
                  >
                    {s.title}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 聊天记录区域 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[280px]">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center py-8">
              <div className="text-3xl mb-2">✨</div>
              <p className="text-xs text-[#b89b5e]">在下方输入你的计划或意图</p>
              <p className="text-[10px] text-[#b89b5e]/60 mt-1">例如：准备下周考试 + 健身计划</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx}>
              {msg.role === 'user' ? (
                <div className="flex justify-end">
                  <div className="max-w-[85%] bg-[#d4af37]/10 border border-[#d4af37]/20 rounded-xl rounded-tr-sm px-3 py-2">
                    <p className="text-sm text-[#e7d7b7]">{msg.content}</p>
                  </div>
                </div>
              ) : (
                <div className="flex justify-start">
                  <div className="max-w-[90%] w-full">
                    <div className="bg-[#050505] border border-[#d4af37]/10 rounded-xl rounded-tl-sm px-3 py-2">
                      {/* 思考步骤 */}
                      {msg.steps && msg.steps.length > 0 && (
                        <ThinkingSteps steps={msg.steps} />
                      )}
                      {/* 最终回复 — 历史消息直接渲染 Markdown，最新消息用打字机 */}
                      {idx === messages.length - 1 && msg.steps ? (
                        <TypewriterText text={msg.content} speed={12} />
                      ) : (
                        <div className="text-sm text-[#e7d7b7] prose prose-invert prose-sm max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}

          {aiLoading && (
            <div className="flex justify-start">
              <div className="bg-[#050505] border border-[#d4af37]/10 rounded-xl rounded-tl-sm px-3 py-2 flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-[#d4af37]/30 border-t-[#d4af37] rounded-full animate-spin" />
                <span className="text-xs text-[#b89b5e]">AI 解析中...</span>
              </div>
            </div>
          )}
        </div>

        {/* 输入框 */}
        <div className="p-3 border-t border-[#d4af37]/10">
          <div className="flex gap-2">
            <input
              value={aiInput}
              onChange={(e) => setAiInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSummon()}
              disabled={aiLoading}
              className="flex-1 bg-[#050505] border border-[#d4af37]/20 rounded-lg px-3 py-2 text-sm outline-none text-[#e7d7b7] placeholder-[#b89b5e]/50 focus:border-[#d4af37]/50 transition-colors disabled:opacity-50"
              placeholder="输入你的意图..."
            />
            <button
              onClick={handleSummon}
              disabled={aiLoading || !aiInput.trim()}
              className="px-4 py-2 rounded-lg bg-[#d4af37]/10 text-[#d4af37] border border-[#d4af37]/30 hover:bg-[#d4af37]/20 disabled:opacity-50 transition-colors text-sm"
            >
              发送
            </button>
          </div>
        </div>
      </div>

      {/* 今日统计 */}
      <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-4">
        <h3 className="text-[#d4af37] mb-3 text-sm font-semibold">今日试炼</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-[#050505] rounded-lg p-3 text-center">
            <div className="text-xl font-bold text-[#d4af37]">0</div>
            <div className="text-xs text-[#b89b5e]">进行中</div>
          </div>
          <div className="bg-[#050505] rounded-lg p-3 text-center">
            <div className="text-xl font-bold text-[#d4af37]">0</div>
            <div className="text-xs text-[#b89b5e]">已完成</div>
          </div>
        </div>
      </div>
    </div>
  )
}

function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#050505] text-[#e7d7b7] relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,#2a1f10,transparent_60%)] opacity-60" />

      <div className="relative p-6">
        <div className="grid grid-cols-12 gap-6">
          <Sidebar />
          <div className="col-span-7 space-y-6">
            <TopBar />
            {children}
          </div>
          <RightPanel />
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <AuthGuard>
              <InitData />
              <DashboardLayout>
                <Routes>
                  <Route path="/" element={<TaskList />} />
                  <Route path="/plans" element={<PlanList />} />
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/skills" element={<Placeholder title="技能树" desc="Phase 2 实现" />} />
                  <Route path="/equipment" element={<Placeholder title="装备栏" desc="Phase 4 实现" />} />
                  <Route path="/achievements" element={<Placeholder title="成就系统" desc="Phase 4 实现" />} />
                </Routes>
              </DashboardLayout>
            </AuthGuard>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

function Placeholder({ title, desc }) {
  return (
    <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-6">
      <h2 className="text-xl font-semibold text-[#d4af37] mb-2">{title}</h2>
      <p className="text-[#b89b5e]">{desc}</p>
    </div>
  )
}
