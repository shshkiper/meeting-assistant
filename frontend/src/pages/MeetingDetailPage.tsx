import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { meetingsApi, transcriptApi, protocolApi, tasksApi, analyticsApi } from '@/utils/api'
import {
  ChevronLeft, FileText, Mic, CheckSquare, BarChart2,
  Download, Loader2, RefreshCw
} from 'lucide-react'
import StatusBadge from '@/components/StatusBadge'
import TranscriptView from '@/components/TranscriptView'
import ProtocolView from '@/components/ProtocolView'
import TasksView from '@/components/TasksView'
import AnalyticsView from '@/components/AnalyticsView'
import ProcessingProgress from '@/components/ProcessingProgress'
import toast from 'react-hot-toast'

const TABS = [
  { id: 'transcript', label: 'Транскрипция', icon: Mic },
  { id: 'protocol',   label: 'Протокол',     icon: FileText },
  { id: 'tasks',      label: 'Задачи',        icon: CheckSquare },
  { id: 'analytics',  label: 'Аналитика',     icon: BarChart2 },
] as const

type Tab = (typeof TABS)[number]['id']

export default function MeetingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [activeTab, setActiveTab] = useState<Tab>('transcript')
  const qc = useQueryClient()

  const { data: meeting, isLoading } = useQuery({
    queryKey: ['meeting', id],
    queryFn: () => meetingsApi.get(id!),
    refetchInterval: (data: any) =>
      ['uploaded', 'transcribing', 'diarizing', 'analyzing'].includes(data?.status)
        ? 5000
        : false,
  })

  const isProcessing = ['uploaded', 'transcribing', 'diarizing', 'analyzing'].includes(
    meeting?.status ?? '',
  )
  const isCompleted = meeting?.status === 'completed'
  const isFailed = meeting?.status === 'failed'

  const exportDocx = async () => {
    try {
      const blob = await protocolApi.exportDocx(id!)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `protocol_${id}.docx`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Ошибка экспорта протокола')
    }
  }

  if (isLoading)
    return (
      <div className="p-8 flex justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    )

  if (!meeting) return <div className="p-8 text-gray-500">Совещание не найдено</div>

  return (
    <div className="p-8">
      {/* Back + header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <Link
            to="/meetings"
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-3"
          >
            <ChevronLeft className="w-4 h-4" /> Все совещания
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{meeting.title}</h1>
            <StatusBadge status={meeting.status} />
          </div>
          {meeting.description && (
            <p className="text-gray-500 mt-1">{meeting.description}</p>
          )}
        </div>
        {isCompleted && (
          <button onClick={exportDocx} className="btn-secondary">
            <Download className="w-4 h-4" />
            Скачать протокол
          </button>
        )}
      </div>

      {/* Processing progress */}
      {isProcessing && <ProcessingProgress meetingId={id!} status={meeting.status} />}

      {/* Failed */}
      {isFailed && (
        <div className="mb-6 rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          <p className="font-medium">Ошибка обработки</p>
          <p className="mt-1 text-red-600">
            При обработке записи произошла ошибка. Попробуйте загрузить файл снова.
          </p>
        </div>
      )}

      {/* Tabs */}
      {isCompleted && (
        <>
          <div className="flex gap-1 border-b border-gray-200 mb-6">
            {TABS.map(({ id: tabId, label, icon: Icon }) => (
              <button
                key={tabId}
                onClick={() => setActiveTab(tabId)}
                className={`
                  flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors
                  ${activeTab === tabId
                    ? 'border-brand-600 text-brand-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {activeTab === 'transcript' && <TranscriptView meetingId={id!} />}
          {activeTab === 'protocol'   && <ProtocolView meetingId={id!} />}
          {activeTab === 'tasks'      && <TasksView meetingId={id!} />}
          {activeTab === 'analytics'  && <AnalyticsView meetingId={id!} />}
        </>
      )}
    </div>
  )
}
