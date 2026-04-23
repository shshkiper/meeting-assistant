import { useEffect, useState } from 'react'

const STEP_ORDER = [
  'Загрузка аудио',
  'Транскрибация',
  'Разметка спикеров',
  'Анализ текста',
  'Генерация саммари',
  'Генерация протокола',
  'Извлечение задач',
  'Обработка завершена',
]

interface Props {
  meetingId: string
  status: string
}

export default function ProcessingProgress({ meetingId, status }: Props) {
  const [progress, setProgress] = useState(0)
  const [step, setStep] = useState('')

  useEffect(() => {
    const wsUrl = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/meetings/${meetingId}/progress`
    const ws = new WebSocket(wsUrl)

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.ping) return
        if (msg.progress !== undefined) setProgress(msg.progress)
        if (msg.step) setStep(msg.step)
      } catch {}
    }

    ws.onerror = () => {}
    return () => ws.close()
  }, [meetingId])

  return (
    <div className="mb-6 card">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-gray-700">
          {step || 'Обработка записи...'}
        </p>
        <span className="text-sm font-semibold text-brand-600">{progress}%</span>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-brand-500 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps */}
      <div className="mt-4 flex gap-1 flex-wrap">
        {STEP_ORDER.map((s) => {
          const done = progress >= (STEP_ORDER.indexOf(s) + 1) * (100 / STEP_ORDER.length)
          const active = s === step
          return (
            <span
              key={s}
              className={`
                text-xs px-2 py-1 rounded-full
                ${done ? 'bg-green-100 text-green-700' : active ? 'bg-brand-100 text-brand-700' : 'bg-gray-100 text-gray-400'}
              `}
            >
              {done && '✓ '}{s}
            </span>
          )
        })}
      </div>
    </div>
  )
}
