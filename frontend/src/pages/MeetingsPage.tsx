import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { meetingsApi } from '@/utils/api'
import { Link } from 'react-router-dom'
import { Trash2, ChevronRight, Upload } from 'lucide-react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import StatusBadge from '@/components/StatusBadge'
import toast from 'react-hot-toast'

export default function MeetingsPage() {
  const qc = useQueryClient()
  const { data: meetings = [], isLoading } = useQuery({
    queryKey: ['meetings'],
    queryFn: meetingsApi.list,
    refetchInterval: 15_000,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => meetingsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['meetings'] })
      toast.success('Совещание удалено')
    },
    onError: () => toast.error('Ошибка при удалении'),
  })

  if (isLoading)
    return (
      <div className="p-8 flex justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full" />
      </div>
    )

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Совещания</h1>
        <Link to="/upload" className="btn-primary">
          <Upload className="w-4 h-4" />
          Загрузить
        </Link>
      </div>

      {meetings.length === 0 ? (
        <div className="card text-center py-16">
          <p className="text-gray-400 mb-4">Нет загруженных совещаний</p>
          <Link to="/upload" className="btn-primary">Загрузить первое совещание</Link>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Название
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Дата загрузки
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Статус
                </th>
                <th className="w-24" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {meetings.map((m: any) => (
                <tr key={m.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <Link to={`/meetings/${m.id}`} className="font-medium text-gray-900 hover:text-brand-600">
                      {m.title}
                    </Link>
                    {m.description && (
                      <p className="text-xs text-gray-400 mt-0.5 truncate max-w-xs">{m.description}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {format(new Date(m.created_at), 'd MMM yyyy HH:mm', { locale: ru })}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={m.status} />
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => {
                          if (confirm('Удалить совещание?')) deleteMutation.mutate(m.id)
                        }}
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <Link
                        to={`/meetings/${m.id}`}
                        className="p-1.5 text-gray-400 hover:text-brand-600 hover:bg-brand-50 rounded transition-colors"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
