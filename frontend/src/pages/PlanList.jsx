import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useUserStore } from '../stores/userStore'
import { planApi } from '../lib/api'
import clsx from 'clsx'

export default function PlanList() {
  const { user } = useUserStore()
  const queryClient = useQueryClient()
  const userId = user?.id

  const [expandedPlanId, setExpandedPlanId] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newPlanTitle, setNewPlanTitle] = useState('')
  const [newPlanDesc, setNewPlanDesc] = useState('')
  const [stagesInput, setStagesInput] = useState('')

  const { data: plans, isLoading } = useQuery({
    queryKey: ['plans', userId],
    queryFn: () => planApi.list(userId),
    enabled: !!userId,
  })

  const createMutation = useMutation({
    mutationFn: (data) => planApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      setShowCreate(false)
      setNewPlanTitle('')
      setNewPlanDesc('')
      setStagesInput('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => planApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] })
    },
  })

  const toggleExpand = (planId) => {
    setExpandedPlanId(expandedPlanId === planId ? null : planId)
  }

  const handleCreate = () => {
    if (!newPlanTitle.trim()) return
    let stages = []
    if (stagesInput.trim()) {
      try {
        stages = JSON.parse(stagesInput)
      } catch {
        // 非JSON格式，按行分割
        stages = stagesInput.split('\n').filter(Boolean).map((name, i) => ({
          name: name.trim(),
          order: i + 1,
          tasks: [],
        }))
      }
    }
    createMutation.mutate({
      user_id: userId,
      title: newPlanTitle.trim(),
      description: newPlanDesc.trim() || undefined,
      stages,
    })
  }

  if (isLoading) {
    return (
      <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-6">
        <p className="text-[#b89b5e]">加载中...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-[#d4af37]">冒险计划</h2>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-3 py-1.5 rounded-lg bg-[#d4af37]/10 text-[#d4af37] border border-[#d4af37]/30 hover:bg-[#d4af37]/20 text-sm transition-colors"
        >
          {showCreate ? '取消' : '+ 新建计划'}
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-4 space-y-3">
          <input
            value={newPlanTitle}
            onChange={(e) => setNewPlanTitle(e.target.value)}
            placeholder="计划名称（如：考研复习计划）"
            className="w-full bg-[#050505] border border-[#d4af37]/20 rounded-lg px-3 py-2 text-sm text-[#e7d7b7] placeholder-[#b89b5e]/50 outline-none focus:border-[#d4af37]/50"
          />
          <textarea
            value={newPlanDesc}
            onChange={(e) => setNewPlanDesc(e.target.value)}
            placeholder="计划描述（可选）..."
            rows={2}
            className="w-full bg-[#050505] border border-[#d4af37]/20 rounded-lg px-3 py-2 text-sm text-[#e7d7b7] placeholder-[#b89b5e]/50 outline-none focus:border-[#d4af37]/50 resize-none"
          />
          <textarea
            value={stagesInput}
            onChange={(e) => setStagesInput(e.target.value)}
            placeholder={`阶段列表（可选）\n方式1：每行一个阶段名称\n方式2：JSON 格式 [{"name":"阶段1","tasks":[{...}]}]`}
            rows={4}
            className="w-full bg-[#050505] border border-[#d4af37]/20 rounded-lg px-3 py-2 text-sm text-[#e7d7b7] placeholder-[#b89b5e]/50 outline-none focus:border-[#d4af37]/50 resize-none font-mono text-xs"
          />
          <button
            onClick={handleCreate}
            disabled={createMutation.isPending}
            className="w-full py-2 rounded-lg bg-[#d4af37]/10 text-[#d4af37] border border-[#d4af37]/30 hover:bg-[#d4af37]/20 disabled:opacity-50 text-sm transition-colors"
          >
            {createMutation.isPending ? '创建中...' : '创建计划'}
          </button>
        </div>
      )}

      {/* Plans List */}
      {(!plans || plans.length === 0) ? (
        <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-8 text-center">
          <div className="text-3xl mb-2">🗺️</div>
          <p className="text-[#b89b5e] text-sm">还没有冒险计划</p>
          <p className="text-[#b89b5e]/60 text-xs mt-1">对 AI 导师说"帮我规划考研复习"即可自动创建</p>
        </div>
      ) : (
        plans.map((plan) => (
          <PlanCard
            key={plan.id}
            plan={plan}
            isExpanded={expandedPlanId === plan.id}
            onToggle={() => toggleExpand(plan.id)}
            onDelete={() => {
              if (confirm(`确定删除计划「${plan.title}」吗？关联任务不会被删除。`)) {
                deleteMutation.mutate(plan.id)
              }
            }}
          />
        ))
      )}
    </div>
  )
}

function PlanCard({ plan, isExpanded, onToggle, onDelete }) {
  const [progress, setProgress] = useState(null)

  useEffect(() => {
    if (isExpanded && plan.id) {
      planApi.progress(plan.id).then(setProgress).catch(() => {})
    }
  }, [isExpanded, plan.id])

  const stages = plan.stages || []
  const statusLabel = {
    active: '进行中',
    completed: '已完成',
    paused: '已暂停',
  }[plan.status] || plan.status

  const statusColor = {
    active: 'text-green-400',
    completed: 'text-[#d4af37]',
    paused: 'text-gray-400',
  }[plan.status] || 'text-[#b89b5e]'

  return (
    <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl overflow-hidden">
      {/* Header - clickable */}
      <div
        onClick={onToggle}
        className="p-4 cursor-pointer hover:bg-[#d4af37]/5 transition-colors"
      >
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className={clsx('text-xs font-medium', statusColor)}>
                {statusLabel}
              </span>
              <h3 className="text-[#e7d7b7] font-semibold">{plan.title}</h3>
            </div>
            {plan.description && (
              <p className="text-xs text-[#b89b5e]/80 mt-1">{plan.description}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#b89b5e]">{stages.length} 个阶段</span>
            <span className="text-[#b89b5e]">{isExpanded ? '▼' : '▶'}</span>
          </div>
        </div>

        {/* Progress bar */}
        {progress && (
          <div className="mt-3">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-[#b89b5e]">总进度</span>
              <span className="text-[#d4af37]">{progress.progress_percent}%</span>
            </div>
            <div className="h-1.5 bg-[#1a140a] rounded overflow-hidden">
              <div
                className="h-full bg-[#d4af37] rounded transition-all duration-500"
                style={{ width: `${progress.progress_percent}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-[#b89b5e]/60 mt-1">
              <span>{progress.completed_tasks}/{progress.total_tasks} 任务</span>
              <span>当前阶段: {progress.current_stage || '待定'}</span>
            </div>
          </div>
        )}
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-[#d4af37]/10">
          {/* Stages */}
          {stages.length > 0 && (
            <div className="mt-3 space-y-2">
              <h4 className="text-xs text-[#d4af37] font-semibold">阶段详情</h4>
              {stages.map((stage, idx) => (
                <div
                  key={idx}
                  className="bg-[#050505] rounded-lg p-3 border border-[#d4af37]/10"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-[#d4af37]/10 text-[#d4af37] text-[10px] flex items-center justify-center font-bold">
                      {stage.order || idx + 1}
                    </span>
                    <span className="text-sm text-[#e7d7b7] font-medium">{stage.name}</span>
                  </div>
                  {stage.description && (
                    <p className="text-xs text-[#b89b5e]/70 mt-1 ml-7">{stage.description}</p>
                  )}
                  {stage.tasks && stage.tasks.length > 0 && (
                    <div className="mt-2 ml-7 space-y-1">
                      {stage.tasks.map((task, tidx) => (
                        <div key={tidx} className="text-xs text-[#b89b5e]">
                          · {task.title || task}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="mt-3 flex gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDelete()
              }}
              className="px-3 py-1.5 rounded-lg text-xs text-red-400 border border-red-400/20 hover:bg-red-400/10 transition-colors"
            >
              删除计划
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
