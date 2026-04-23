import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/utils/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Loader2, Phone, Mail, User } from 'lucide-react'

const SENTIMENT_LABELS: Record<string, string> = {
  positive: '😊 Позитивный',
  negative: '😔 Негативный',
  neutral:  '😐 Нейтральный',
  speech:   '🗣️ Речь',
  skip:     'Пропущено',
}

const SENTIMENT_COLOR: Record<string, string> = {
  positive: '#22c55e',
  negative: '#ef4444',
  neutral:  '#94a3b8',
  speech:   '#6366f1',
}

export default function AnalyticsView({ meetingId }: { meetingId: string }) {
  const { data: sentiment, isLoading: sentLoading } = useQuery({
    queryKey: ['sentiment', meetingId],
    queryFn: () => analyticsApi.sentiment(meetingId),
  })

  const { data: keywords = [], isLoading: kwLoading } = useQuery({
    queryKey: ['keywords', meetingId],
    queryFn: () => analyticsApi.keywords(meetingId),
  })

  const { data: contacts = [], isLoading: ctLoading } = useQuery({
    queryKey: ['contacts', meetingId],
    queryFn: () => analyticsApi.contacts(meetingId),
  })

  const isLoading = sentLoading || kwLoading || ctLoading
  if (isLoading)
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    )

  const kwChartData = keywords
    .slice(0, 12)
    .map((k: any) => ({ name: k.word, score: Math.round((k.score ?? 0) * 100) }))

  const sentScores = sentiment?.scores
    ? Object.entries(sentiment.scores)
        .filter(([k]) => k !== 'skip')
        .map(([k, v]: any) => ({ name: SENTIMENT_LABELS[k] ?? k, value: Math.round(v * 100), key: k }))
        .sort((a, b) => b.value - a.value)
    : []

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Sentiment overall */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Тональность совещания</h3>
        {sentiment?.overall ? (
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl">
              {sentiment.overall === 'positive' ? '😊' : sentiment.overall === 'negative' ? '😔' : '😐'}
            </span>
            <div>
              <p className="font-semibold text-gray-900">
                {SENTIMENT_LABELS[sentiment.overall] ?? sentiment.overall}
              </p>
              <p className="text-xs text-gray-400">Общая тональность записи</p>
            </div>
          </div>
        ) : (
          <p className="text-gray-400 text-sm">Данные недоступны</p>
        )}

        {sentScores.length > 0 && (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={sentScores} layout="vertical">
              <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: any) => `${v}%`} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {sentScores.map((entry, i) => (
                  <Cell key={i} fill={SENTIMENT_COLOR[entry.key] ?? '#94a3b8'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}

        {/* Per-speaker */}
        {sentiment?.segments?.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">По спикерам</p>
            {sentiment.segments.map((s: any) => (
              <div key={s.speaker} className="flex items-center justify-between">
                <span className="text-sm text-gray-700">{s.speaker}</span>
                <span className="badge bg-gray-100 text-gray-600">
                  {SENTIMENT_LABELS[s.sentiment] ?? s.sentiment}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Keywords */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Ключевые слова и темы</h3>
        {kwChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={kwChartData} layout="vertical">
              <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 10 }} />
              <Tooltip formatter={(v: any) => `${v}%`} />
              <Bar dataKey="score" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-400 text-sm">Ключевые слова не найдены</p>
        )}
      </div>

      {/* Contacts */}
      <div className="card lg:col-span-2">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">
          Упомянутые контакты ({contacts.length})
        </h3>
        {contacts.length === 0 ? (
          <p className="text-gray-400 text-sm">Контакты не обнаружены</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {contacts.map((c: any, i: number) => (
              <div key={i} className="rounded-lg border border-gray-100 p-3 bg-gray-50 hover:bg-white transition-colors">
                {c.name && (
                  <div className="flex items-center gap-1.5 text-sm text-gray-800 font-medium">
                    <User className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                    {c.name}
                  </div>
                )}
                {c.email && (
                  <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-1">
                    <Mail className="w-3 h-3 text-gray-400 shrink-0" />
                    {c.email}
                  </div>
                )}
                {c.phone && (
                  <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-1">
                    <Phone className="w-3 h-3 text-gray-400 shrink-0" />
                    {c.phone}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
