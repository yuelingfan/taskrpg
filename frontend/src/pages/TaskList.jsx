import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { taskApi, userApi } from '../lib/api'
import { useAppStore } from '../stores/appStore'
import { useUserStore } from '../stores/userStore'
import clsx from 'clsx'

const QUEST_TIERS = {
  normal: { label: '普通任务', color: 'text-[#b89b5e]', bg: 'bg-[#b89b5e]/10', border: 'border-[#b89b5e]/20', xp: 10 },
  rare: { label: '稀有任务', color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400/30', xp: 30 },
  epic: { label: '史诗任务', color: 'text-purple-400', bg: 'bg-purple-400/10', border: 'border-purple-400/30', xp: 50 },
}

const STATUS_CONFIG = {
  todo: { label: '待领取', color: 'text-[#b89b5e]', bg: 'bg-[#b89b5e]/10' },
  doing: { label: '进行中', color: 'text-[#d4af37]', bg: 'bg-[#d4af37]/10' },
  done: { label: '已完成', color: 'text-green-400', bg: 'bg-green-400/10' },
}

export default function TaskList() {
  const { currentUserId, tasks, filter, setFilter, addTask, updateTask, removeTask } = useAppStore()
  const { user, setUser } = useUserStore()
  const [newTaskTitle, setNewTaskTitle] = useState('')
  const [newTaskDesc, setNewTaskDesc] = useState('')
  const [newTaskDeadline, setNewTaskDeadline] = useState('')
  const [newTaskTier, setNewTaskTier] = useState('normal')
  const [showDone, setShowDone] = useState(false)
  const [expandedTaskId, setExpandedTaskId] = useState(null)

  const createMutation = useMutation({
    mutationFn: taskApi.create,
    onSuccess: (data) => {
      addTask(data)
      setNewTaskTitle('')
      setNewTaskDesc('')
      setNewTaskDeadline('')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => taskApi.update(id, data),
    onSuccess: (data) => {
      updateTask(data.id, data)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: taskApi.delete,
    onSuccess: (_, id) => {
      removeTask(id)
    },
  })

  const completeMutation = useMutation({
    mutationFn: taskApi.complete,
    onSuccess: (data) => {
      updateTask(data.id, data)
      // 刷新用户数据（EXP、等级、属性可能已更新）
      if (user?.id) {
        userApi.get(user.id).then(setUser).catch(() => {})
      }
    },
  })

  const handleCreateTask = (e) => {
    e.preventDefault()
    if (!newTaskTitle.trim() || !currentUserId) return
    const tier = QUEST_TIERS[newTaskTier]
    createMutation.mutate({
      user_id: currentUserId,
      title: newTaskTitle.trim(),
      description: newTaskDesc.trim() || undefined,
      priority: 'medium',
      deadline: newTaskDeadline ? new Date(newTaskDeadline).toISOString() : null,
      exp_reward: tier.xp,
    })
  }

  // 只显示顶级任务（parent_id 为 null 的任务）
  const topLevelTasks = tasks.filter((t) => !t.parent_id)
  const subTasksMap = tasks.reduce((map, t) => {
    if (t.parent_id) {
      if (!map[t.parent_id]) map[t.parent_id] = []
      map[t.parent_id].push(t)
    }
    return map
  }, {})

  const filteredTasks = topLevelTasks.filter((task) => {
    if (showDone) return task.status === 'done'
    if (filter === 'all') return task.status !== 'done'
    return task.status === filter
  })

  const activeTasks = topLevelTasks.filter((t) => t.status !== 'done')
  const completedTasks = topLevelTasks.filter((t) => t.status === 'done')

  return (
    <div className="space-y-6">
      {/* 任务创建区 */}
      <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-6">
        <h3 className="text-[#d4af37] font-semibold mb-4">📜 创建新任务卷轴</h3>
        <form onSubmit={handleCreateTask} className="space-y-3">
          <input
            type="text"
            value={newTaskTitle}
            onChange={(e) => setNewTaskTitle(e.target.value)}
            placeholder="输入任务名称..."
            className="w-full px-4 py-3 bg-[#050505] border border-[#d4af37]/20 rounded-xl text-[#e7d7b7] placeholder-[#b89b5e]/50 focus:outline-none focus:border-[#d4af37]/50 transition-colors"
          />
          <textarea
            value={newTaskDesc}
            onChange={(e) => setNewTaskDesc(e.target.value)}
            placeholder="任务描述（可选）..."
            rows={2}
            className="w-full px-4 py-3 bg-[#050505] border border-[#d4af37]/20 rounded-xl text-[#e7d7b7] placeholder-[#b89b5e]/50 focus:outline-none focus:border-[#d4af37]/50 transition-colors resize-none text-sm"
          />
          <div className="flex gap-3">
            <input
              type="date"
              value={newTaskDeadline}
              onChange={(e) => setNewTaskDeadline(e.target.value)}
              className="px-4 py-2 bg-[#050505] border border-[#d4af37]/20 rounded-xl text-[#e7d7b7] text-sm focus:outline-none focus:border-[#d4af37]/50 transition-colors"
            />
            <div className="flex gap-2 flex-1">
              {Object.entries(QUEST_TIERS).map(([key, tier]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setNewTaskTier(key)}
                  className={clsx(
                    'px-3 py-1.5 rounded-lg text-xs border transition-all',
                    newTaskTier === key
                      ? `${tier.bg} ${tier.color} border-current`
                      : 'border-[#d4af37]/20 text-[#b89b5e] hover:border-[#d4af37]/40'
                  )}
                >
                  {tier.label}
                </button>
              ))}
            </div>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-6 py-2 bg-[#d4af37]/10 text-[#d4af37] rounded-xl border border-[#d4af37]/30 hover:bg-[#d4af37]/20 disabled:opacity-50 transition-colors font-medium text-sm whitespace-nowrap"
            >
              {createMutation.isPending ? '创建中...' : `创建 (${QUEST_TIERS[newTaskTier].xp} XP)`}
            </button>
          </div>
        </form>
      </div>

      {/* 筛选标签 */}
      <div className="flex gap-2">
        {[
          { key: 'all', label: '进行中', count: activeTasks.length },
          { key: 'done', label: '已完成', count: completedTasks.length, showAll: true },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              if (tab.showAll) {
                setShowDone(true)
                setFilter('all')
              } else {
                setShowDone(false)
                setFilter(tab.key)
              }
            }}
            className={clsx(
              'px-4 py-2 rounded-xl text-sm font-medium transition-all border',
              (tab.showAll ? showDone : filter === tab.key && !showDone)
                ? 'bg-[#d4af37]/10 text-[#d4af37] border-[#d4af37]/30'
                : 'bg-[#0b0b0b]/80 text-[#b89b5e] border-[#d4af37]/20 hover:border-[#d4af37]/40'
            )}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* 任务列表 */}
      <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-[#d4af37] font-semibold">
            {showDone ? '✨ 已完成任务' : '⚔️ 当前任务'}
          </h3>
          {!showDone && (
            <span className="text-xs text-[#b89b5e]">
              进行中 {activeTasks.length} 个任务
            </span>
          )}
        </div>

        <div className="space-y-3">
          {filteredTasks.length === 0 ? (
            <div className="py-12 text-center">
              <div className="text-4xl mb-3">{showDone ? '🎉' : '📜'}</div>
              <p className="text-[#b89b5e]">
                {showDone ? '还没有已完成的任务' : '暂无任务，创建一个吧！'}
              </p>
            </div>
          ) : (
            filteredTasks.map((task) => {
              const tier = QUEST_TIERS[task.task_type] || QUEST_TIERS.normal
              const statusConfig = STATUS_CONFIG[task.status]
              const expReward = task.exp_reward || tier.xp

              return (
                <div
                  key={task.id}
                  className={clsx(
                    'p-4 rounded-xl border transition-all duration-200 hover:scale-[1.01]',
                    tier.border,
                    task.status === 'done'
                      ? 'bg-[#050505]/50 opacity-60'
                      : 'bg-[#050505] hover:bg-[#050505]/80'
                  )}
                >
                  <div className="flex items-center gap-4">
                    {/* 完成按钮 */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (task.status !== 'done') {
                          completeMutation.mutate(task.id)
                        }
                      }}
                      disabled={task.status === 'done'}
                      className={clsx(
                        'w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all flex-shrink-0',
                        task.status === 'done'
                          ? 'bg-[#d4af37] border-[#d4af37] text-black'
                          : 'border-[#d4af37]/50 hover:border-[#d4af37] hover:bg-[#d4af37]/20'
                      )}
                    >
                      {task.status === 'done' && '✓'}
                    </button>

                    {/* 任务内容 — 可点击展开 */}
                    <div
                      className="flex-1 min-w-0 cursor-pointer"
                      onClick={() => setExpandedTaskId(expandedTaskId === task.id ? null : task.id)}
                    >
                      <div className="flex items-center gap-2">
                        <p
                          className={clsx(
                            'font-medium text-[#e7d7b7]',
                            task.status === 'done' && 'line-through text-[#b89b5e]'
                          )}
                        >
                          {task.title}
                        </p>
                        <span className="text-[#b89b5e] text-xs">
                          {expandedTaskId === task.id ? '▼' : '▶'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-2 flex-wrap">
                        <span className={clsx('px-2 py-0.5 text-xs rounded', statusConfig.bg, statusConfig.color)}>
                          {statusConfig.label}
                        </span>
                        <span className={clsx('px-2 py-0.5 text-xs rounded', tier.bg, tier.color)}>
                          {tier.label}
                        </span>
                        {task.deadline && (
                          <span className={clsx(
                            'px-2 py-0.5 text-xs rounded bg-red-400/10',
                            new Date(task.deadline) < new Date() && task.status !== 'done'
                              ? 'text-red-400'
                              : 'text-[#b89b5e]'
                          )}>
                            📅 {new Date(task.deadline).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })}
                          </span>
                        )}
                        {task.status !== 'done' && (
                          <span className="ml-auto text-[#d4af37] text-sm font-medium">
                            +{expReward} XP
                          </span>
                        )}
                      </div>
                    </div>

                    {/* 操作按钮 */}
                    {task.status !== 'done' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          updateMutation.mutate({ id: task.id, data: { status: 'doing' } })
                        }}
                        className="p-2 text-[#d4af37] hover:bg-[#d4af37]/10 rounded-lg transition-colors"
                        title="开始任务"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        </svg>
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteMutation.mutate(task.id)
                      }}
                      className="p-2 text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                      title="删除任务"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>

                  {/* 展开内容：描述 + 子任务 */}
                  {expandedTaskId === task.id && (
                    <div className="mt-3 pt-3 border-t border-[#d4af37]/10">
                      {/* 任务描述 */}
                      {task.description && (
                        <p className="text-sm text-[#b89b5e]/80 mb-3 leading-relaxed">
                          {task.description}
                        </p>
                      )}

                      {/* 子任务列表 */}
                      {subTasksMap[task.id]?.length > 0 && (
                        <div>
                          <p className="text-xs text-[#d4af37] mb-2">
                            子任务 ({subTasksMap[task.id].length})
                          </p>
                          <div className="ml-4 pl-4 border-l-2 border-[#d4af37]/20 space-y-2">
                            {subTasksMap[task.id].map((sub) => (
                              <div key={sub.id} className="flex items-center gap-3">
                                <button
                                  onClick={() => {
                                    if (sub.status !== 'done') {
                                      completeMutation.mutate(sub.id)
                                    }
                                  }}
                                  disabled={sub.status === 'done'}
                                  className={clsx(
                                    'w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 transition-all',
                                    sub.status === 'done'
                                      ? 'bg-[#d4af37]/60 border-[#d4af37]/60 text-black text-xs'
                                      : 'border-[#d4af37]/30 hover:border-[#d4af37]/60'
                                  )}
                                >
                                  {sub.status === 'done' && '✓'}
                                </button>
                                <span
                                  className={clsx(
                                    'text-sm text-[#b89b5e]',
                                    sub.status === 'done' && 'line-through opacity-50'
                                  )}
                                >
                                  {sub.title}
                                </span>
                                <span className="text-[10px] text-[#d4af37]">+5 XP</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* 成就提示 */}
      {completedTasks.length > 0 && (
        <div className="bg-gradient-to-r from-[#d4af37]/10 to-[#b89b5e]/10 border border-[#d4af37]/20 rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🏆</span>
              <div>
                <p className="text-[#e7d7b7] font-medium">今日成就</p>
                <p className="text-sm text-[#b89b5e]">
                  已完成 {completedTasks.length} 个任务
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-[#d4af37]">
                +{completedTasks.reduce((sum, t) => sum + (t.exp_reward || 10), 0)} XP
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
