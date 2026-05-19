import { useUserStore } from '../stores/userStore'
import { useAppStore } from '../stores/appStore'

function AttributeCard({ name, value, icon, description }) {
  return (
    <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-xl p-4">
      <div className="flex items-center gap-3 mb-2">
        <span className="text-2xl">{icon}</span>
        <div>
          <h4 className="text-[#e7d7b7] font-semibold">{name}</h4>
          <p className="text-xs text-[#b89b5e]">{description}</p>
        </div>
      </div>
      <div className="text-3xl font-bold text-[#d4af37]">{value}</div>
    </div>
  )
}

function StatBar({ label, value, maxValue = 100, icon }) {
  const percentage = Math.min((value / maxValue) * 100, 100)

  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1.5">
        <div className="flex items-center gap-2">
          <span className="text-sm">{icon}</span>
          <span className="text-[#b89b5e]">{label}</span>
        </div>
        <span className="text-[#e7d7b7] font-bold">{value}</span>
      </div>
      <div className="w-full h-2 bg-[#1a140a] rounded overflow-hidden">
        <div
          className="h-full bg-[#d4af37] rounded transition-all duration-700"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

export default function Profile() {
  const { user } = useUserStore()
  const { tasks } = useAppStore()

  const level = user?.level || 1
  const exp = user?.exp || 0
  const expNeeded = level * 100
  const stats = user?.stats || { str_value: 10, int_value: 10, sta_value: 10, cha_value: 10 }

  const completedTasks = tasks.filter((t) => t.status === 'done')
  const totalExpEarned = completedTasks.reduce((sum, t) => sum + (t.exp_reward || 10), 0)

  const attributes = [
    { name: '力量 STR', value: stats.str_value, icon: '💪', desc: '体力劳动和运动' },
    { name: '智力 INT', value: stats.int_value, icon: '🧠', desc: '学习和知识' },
    { name: '耐力 STA', value: stats.sta_value, icon: '⚡', desc: '耐力和专注' },
    { name: '魅力 CHA', value: stats.cha_value, icon: '✨', desc: '社交和沟通' },
  ]

  return (
    <div className="space-y-6">
      {/* 角色卡片 */}
      <div className="bg-gradient-to-br from-[#0b0b0b] to-[#050505] rounded-2xl p-6 border border-[#d4af37]/20">
        <div className="flex items-center gap-6">
          {/* 头像 */}
          <div className="relative">
            <div className="w-24 h-24 rounded-2xl border-2 border-[#d4af37] bg-[#1a140a] flex items-center justify-center text-4xl font-bold text-[#d4af37] shadow-[0_0_20px_rgba(212,175,55,0.2)]">
              {user?.name?.[0] || 'V'}
            </div>
            <div className="absolute -bottom-2 -right-2 px-2 py-1 bg-[#0b0b0b] rounded-lg border border-[#d4af37]/30 text-xs text-[#d4af37] font-bold">
              LV.{level}
            </div>
          </div>

          {/* 角色信息 */}
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-[#e7d7b7]">{user?.name || 'Voyager'}</h2>
            <p className="text-[#b89b5e] text-sm mt-1">Adventurer Class</p>

            {/* 经验值进度条 */}
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-[#b89b5e]">经验值</span>
                <span className="text-[#d4af37]">
                  {exp} / {expNeeded} XP
                </span>
              </div>
              <div className="w-full h-3 bg-[#1a140a] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#d4af37] rounded-full transition-all duration-500"
                  style={{ width: `${(exp / expNeeded) * 100}%` }}
                />
              </div>
              <p className="text-xs text-[#b89b5e]/70 mt-1">
                距离下一级还需 {expNeeded - exp} XP
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 属性面板 */}
      <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-6">
        <h3 className="text-[#d4af37] font-semibold mb-4">📊 角色属性</h3>
        <div className="grid grid-cols-2 gap-4">
          {attributes.map((attr) => (
            <AttributeCard
              key={attr.name}
              name={attr.name}
              value={attr.value}
              icon={attr.icon}
              description={attr.desc}
            />
          ))}
        </div>
      </div>

      {/* 详细属性条 */}
      <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-6">
        <h3 className="text-[#d4af37] font-semibold mb-4">📈 属性详情</h3>
        <div className="space-y-4">
          <StatBar label="力量 STR" value={stats.str_value} icon="💪" />
          <StatBar label="智力 INT" value={stats.int_value} icon="🧠" />
          <StatBar label="耐力 STA" value={stats.sta_value} icon="⚡" />
          <StatBar label="魅力 CHA" value={stats.cha_value} icon="✨" />
        </div>
      </div>

      {/* 统计信息 */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-4 text-center">
          <div className="text-3xl font-bold text-[#d4af37]">{completedTasks.length}</div>
          <div className="text-sm text-[#b89b5e] mt-1">已完成任务</div>
        </div>
        <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-4 text-center">
          <div className="text-3xl font-bold text-[#d4af37]">{totalExpEarned}</div>
          <div className="text-sm text-[#b89b5e] mt-1">总经验值</div>
        </div>
        <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-4 text-center">
          <div className="text-3xl font-bold text-[#d4af37]">{level}</div>
          <div className="text-sm text-[#b89b5e] mt-1">当前等级</div>
        </div>
      </div>

      {/* 成长记录 */}
      <div className="bg-[#0b0b0b]/80 border border-[#d4af37]/20 rounded-2xl p-6">
        <h3 className="text-[#d4af37] font-semibold mb-4">📜 成长记录</h3>
        {completedTasks.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3">📋</div>
            <p className="text-[#b89b5e]">还没有完成任务</p>
            <p className="text-sm text-[#b89b5e]/70 mt-1">完成任务获得经验值，提升角色等级</p>
          </div>
        ) : (
          <div className="space-y-3">
            {completedTasks.slice(-5).reverse().map((task) => (
              <div
                key={task.id}
                className="flex items-center gap-3 p-3 bg-[#050505] rounded-xl"
              >
                <div className="w-8 h-8 rounded-full bg-[#d4af37]/20 flex items-center justify-center text-[#d4af37] text-sm">
                  ✓
                </div>
                <div className="flex-1">
                  <p className="text-[#e7d7b7] text-sm">{task.title}</p>
                  <p className="text-xs text-[#b89b5e]">已完成</p>
                </div>
                <div className="text-[#d4af37] text-sm font-medium">
                  +{task.exp_reward || 10} XP
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
