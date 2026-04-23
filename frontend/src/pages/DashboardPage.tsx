import { useQuery } from '@tanstack/react-query'
import { analyticsApi, meetingsApi } from '@/utils/api'
import { Mic, CheckSquare, TrendingUp, Clock, Upload } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import StatusBadge from '@/components/StatusBadge'

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  const { data: stats } = useQuery({
    queryKey: ['dashboard'],
    queryFn: analyticsApi.dashboard,
  })

  const { data: meetings = [] } = useQuery({
    queryKey: ['meetings'],
    queryFn: meetingsApi.list,
  })

  const recentMeetings = meetings.slice(0, 5)

  const cards = [
    { label: 'Всего совещаний', value: stats?.total_meetings ?? 0, icon: Mic, color: 'bg-blue-500' },
    { label: 'Обработано', value: stats?.completed_meetings ?? 0, icon: CheckSquare, color: 'bg-green-500' },
    { label: 'Задач поставлено', value: stats?.total_tasks ?? 0, icon: TrendingUp, color: 'bg-purple-500' },
    {
      label: 'В обработке',
      value: (stats?.total_meetings ?? 0) - (stats?.completed_meetings ?? 0),
      icon: Clock,
      color: 'bg-amber-500',
    },
  ]

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Добрый день, {user?.full_name?.split(' ')[0]} 👋
          </h1>
          <p className="text-gray-500 mt-1">Обзор обработанных совещаний</p>
        </div>
        <Link to="/upload" className="btn-primary">
          <Upload className="w-4 h-4" />
          Загрузить запись
        </Link>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-5 mb-8">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card flex items-center gap-4">
            <div className={`${color} w-12 h-12 rounded-xl flex items-center justify-center shrink-0`}>
              <Icon className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Recent meetings */}
      <div className="card">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-gray-900">Последние совещания</h2>
          <Link to="/meetings" className="text-sm text-brand-600 hover:underline font-medium">
            Все совещания →
          </Link>
        </div>
        {recentMeetings.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">
            Нет совещаний. <Link to="/upload" className="text-brand-600 hover:underline">Загрузить первое →</Link>
          </p>
        ) : (
          <div className="divide-y divide-gray-100">
            {recentMeetings.map((m: any) => (
              <Link
                key={m.id}
                to={`/meetings/${m.id}`}
                className="flex items-center justify-between py-3 hover:bg-gray-50 -mx-2 px-2 rounded-lg transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{m.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {format(new Date(m.created_at), 'd MMM yyyy', { locale: ru })}
                  </p>
                </div>
                <StatusBadge status={m.status} />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
