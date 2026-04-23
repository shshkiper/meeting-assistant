import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksApi } from '@/utils/api'
import { CheckCircle, Circle, Clock, Loader2, ExternalLink } from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

const PRIORITY_STYLES: Record<string, string> = {
  high:   'bg-red-100 text-red-700',
  medium: 'bg-amber-100 text-amber-700',
  low:    'bg-green-100 text-green-700',
}

const PRIORITY_LABELS: Record<string, string> = {
  high: 'Высокий', medium: 'Средний', low: 'Низкий',
}

export default function TasksView({ meetingId }: { meetingId: string }) {
  const qc = useQueryClient()

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['tasks', meetingId],
    queryFn: () => tasksApi.list(meetingId),
  })

  const updateMutation = useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data: object }) =>
      tasksApi.update(taskId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks', meetingId] }),
    onError: () => toast.error('Ошибка обновления'),
  })

  const syncJira = useMutation({
    mutationFn: (taskId: string) => tasksApi.syncJira(taskId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks', meetingId] })
      toast.success('Задача создана в Jira')
    },
    onError: () => toast.error('Ошибка синхронизации с Jira'),
  })

  const toggleStatus = (task: any) => {
    const next = task.status === 'done' ? 'open' : 'done'
    updateMutation.mutate({ taskId: task.id, data: { status: next } })
  }

  if (isLoading)
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    )

  if (tasks.length === 0)
    return (
      <div className="card text-center py-12 text-gray-400">
        Задачи не были обнаружены в записи совещания
      </div>
    )

  const open   = tasks.filter((t: any) => t.status !== 'done')
  const closed = tasks.filter((t: any) => t.status === 'done')

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        {open.length} открытых · {closed.length} выполнено
      </p>

      <div className="space-y-2">
        {tasks.map((task: any) => (
          <div
            key={task.id}
            className={clsx(
              'card flex gap-4 p-4 transition-opacity',
              task.status === 'done' && 'opacity-60',
            )}
          >
            {/* Checkbox */}
            <button
              onClick={() => toggleStatus(task)}
              className="mt-0.5 shrink-0"
              disabled={updateMutation.isPending}
            >
              {task.status === 'done'
                ? <CheckCircle className="w-5 h-5 text-green-500" />
                : <Circle className="w-5 h-5 text-gray-300 hover:text-brand-400 transition-colors" />
              }
            </button>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <p className={clsx('font-medium text-gray-900', task.status === 'done' && 'line-through')}>
                {task.title}
              </p>
              {task.description && (
                <p className="text-sm text-gray-500 mt-1">{task.description}</p>
              )}

              <div className="flex flex-wrap items-center gap-2 mt-2">
                {/* Priority */}
                <span className={`badge ${PRIORITY_STYLES[task.priority] ?? 'bg-gray-100 text-gray-600'}`}>
                  {PRIORITY_LABELS[task.priority] ?? task.priority}
                </span>

                {/* Assignee */}
                {task.assignee_name_raw && (
                  <span className="badge bg-indigo-50 text-indigo-700">
                    👤 {task.assignee_name_raw}
                  </span>
                )}

                {/* Due date */}
                {task.due_date && (
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    {format(new Date(task.due_date), 'd MMM yyyy', { locale: ru })}
                  </span>
                )}

                {/* Jira */}
                {task.jira_key ? (
                  <span className="badge bg-blue-50 text-blue-700 flex items-center gap-1">
                    <ExternalLink className="w-3 h-3" />
                    {task.jira_key}
                  </span>
                ) : (
                  <button
                    onClick={() => syncJira.mutate(task.id)}
                    disabled={syncJira.isPending}
                    className="text-xs text-gray-400 hover:text-blue-600 hover:underline"
                  >
                    → Создать в Jira
                  </button>
                )}
              </div>

              {/* Source segment */}
              {task.source_segment && (
                <blockquote className="mt-2 text-xs text-gray-400 border-l-2 border-gray-200 pl-2 italic">
                  «{task.source_segment.slice(0, 200)}»
                </blockquote>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
