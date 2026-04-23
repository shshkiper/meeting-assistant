import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { transcriptApi } from '@/utils/api'
import { Search, Loader2 } from 'lucide-react'

const SPEAKER_COLORS = [
  'bg-blue-100 text-blue-800',
  'bg-purple-100 text-purple-800',
  'bg-green-100 text-green-800',
  'bg-amber-100 text-amber-800',
  'bg-rose-100 text-rose-800',
  'bg-indigo-100 text-indigo-800',
]

function fmtTime(sec: number) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function TranscriptView({ meetingId }: { meetingId: string }) {
  const [search, setSearch] = useState('')

  const { data: transcript, isLoading } = useQuery({
    queryKey: ['transcript', meetingId],
    queryFn: () => transcriptApi.get(meetingId),
  })

  if (isLoading)
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    )

  if (!transcript) return <p className="text-gray-400">Транскрипция недоступна</p>

  const speakerSet = Array.from(new Set((transcript.segments ?? []).map((s: any) => s.speaker)))
  const speakerColor = (spk: string) =>
    SPEAKER_COLORS[speakerSet.indexOf(spk) % SPEAKER_COLORS.length]

  const filtered = search
    ? (transcript.segments ?? []).filter((s: any) =>
        s.text.toLowerCase().includes(search.toLowerCase()),
      )
    : transcript.segments ?? []

  return (
    <div className="space-y-4">
      {/* Summary */}
      {transcript.summary && (
        <div className="card bg-brand-50 border-brand-100">
          <h3 className="text-sm font-semibold text-brand-700 mb-2">Краткое саммари</h3>
          <p className="text-sm text-gray-700 leading-relaxed">{transcript.summary}</p>
        </div>
      )}

      {/* Speaker legend */}
      {speakerSet.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {speakerSet.map((spk: any) => (
            <span key={spk} className={`badge ${speakerColor(spk)}`}>
              {spk}
            </span>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          className="input pl-9"
          placeholder="Поиск по тексту..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Segments */}
      <div className="card p-0 overflow-hidden divide-y divide-gray-100 max-h-[65vh] overflow-y-auto">
        {filtered.length === 0 && (
          <p className="text-center py-8 text-gray-400 text-sm">Ничего не найдено</p>
        )}
        {filtered.map((seg: any, idx: number) => (
          <div key={idx} className="flex gap-3 px-5 py-3 hover:bg-gray-50 transition-colors">
            {/* Time */}
            <span className="text-xs text-gray-400 whitespace-nowrap mt-0.5 w-12 shrink-0">
              {fmtTime(seg.start)}
            </span>
            {/* Speaker badge */}
            <span className={`badge h-fit shrink-0 mt-0.5 ${speakerColor(seg.speaker)}`}>
              {seg.speaker}
            </span>
            {/* Text */}
            <p className="text-sm text-gray-800 leading-relaxed">
              {search
                ? seg.text.split(new RegExp(`(${search})`, 'gi')).map((part: string, i: number) =>
                    part.toLowerCase() === search.toLowerCase() ? (
                      <mark key={i} className="bg-yellow-200 rounded px-0.5">{part}</mark>
                    ) : (
                      part
                    ),
                  )
                : seg.text}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
