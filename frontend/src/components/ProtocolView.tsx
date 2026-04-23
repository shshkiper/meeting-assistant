import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { protocolApi } from '@/utils/api'
import { Edit3, Save, X, Loader2, Download } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'

export default function ProtocolView({ meetingId }: { meetingId: string }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const qc = useQueryClient()

  const { data: protocol, isLoading } = useQuery({
    queryKey: ['protocol', meetingId],
    queryFn: () => protocolApi.get(meetingId),
  })

  const updateMutation = useMutation({
    mutationFn: (content_md: string) => protocolApi.update(meetingId, { content_md }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['protocol', meetingId] })
      setEditing(false)
      toast.success('Протокол сохранён')
    },
    onError: () => toast.error('Ошибка сохранения'),
  })

  const handleExport = async () => {
    try {
      const blob = await protocolApi.exportDocx(meetingId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `protocol_${meetingId}.docx`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Протокол скачан')
    } catch {
      toast.error('Ошибка экспорта')
    }
  }

  const startEdit = () => {
    setDraft(protocol?.content_md ?? '')
    setEditing(true)
  }

  if (isLoading)
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    )

  if (!protocol) return <p className="text-gray-400">Протокол недоступен</p>

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-end gap-2">
        {editing ? (
          <>
            <button onClick={() => setEditing(false)} className="btn-secondary">
              <X className="w-4 h-4" /> Отмена
            </button>
            <button
              onClick={() => updateMutation.mutate(draft)}
              disabled={updateMutation.isPending}
              className="btn-primary"
            >
              {updateMutation.isPending
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Save className="w-4 h-4" />
              }
              Сохранить
            </button>
          </>
        ) : (
          <>
            <button onClick={startEdit} className="btn-secondary">
              <Edit3 className="w-4 h-4" /> Редактировать
            </button>
            <button onClick={handleExport} className="btn-primary">
              <Download className="w-4 h-4" /> Скачать DOCX
            </button>
          </>
        )}
      </div>

      {/* Content */}
      {editing ? (
        <textarea
          className="input font-mono text-sm resize-none min-h-[70vh]"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
      ) : (
        <div className="card prose prose-sm max-w-none">
          <ReactMarkdown>{protocol.content_md ?? ''}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}
