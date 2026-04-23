import clsx from 'clsx'

const STATUS_MAP: Record<string, { label: string; classes: string }> = {
  uploaded:     { label: 'Загружено',    classes: 'bg-gray-100 text-gray-600' },
  transcribing: { label: 'Транскрипция', classes: 'bg-blue-100 text-blue-700' },
  diarizing:    { label: 'Спикеры',      classes: 'bg-indigo-100 text-indigo-700' },
  analyzing:    { label: 'Анализ',       classes: 'bg-purple-100 text-purple-700' },
  completed:    { label: 'Готово',       classes: 'bg-green-100 text-green-700' },
  failed:       { label: 'Ошибка',       classes: 'bg-red-100 text-red-600' },
}

export default function StatusBadge({ status }: { status: string }) {
  const meta = STATUS_MAP[status] ?? { label: status, classes: 'bg-gray-100 text-gray-600' }
  return (
    <span className={clsx('badge', meta.classes)}>
      {['transcribing', 'diarizing', 'analyzing', 'uploaded'].includes(status) && (
        <span className="mr-1 inline-block w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      )}
      {meta.label}
    </span>
  )
}
