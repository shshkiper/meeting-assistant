import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { meetingsApi } from '@/utils/api'
import { Upload, FileVideo, Loader2, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'

const ACCEPTED = {
  'audio/*': ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.webm'],
  'video/*': ['.mp4', '.webm', '.mkv', '.avi'],
}

export default function UploadPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) {
      setFile(accepted[0])
      if (!title) setTitle(accepted[0].name.replace(/\.[^.]+$/, ''))
    }
  }, [title])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxFiles: 1,
    maxSize: 2 * 1024 * 1024 * 1024, // 2 GB
  })

  const uploadMutation = useMutation({
    mutationFn: (fd: FormData) => meetingsApi.upload(fd),
    onSuccess: (meeting) => {
      qc.invalidateQueries({ queryKey: ['meetings'] })
      toast.success('Запись загружена! Обработка началась.')
      navigate(`/meetings/${meeting.id}`)
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? 'Ошибка загрузки')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !title) return
    const fd = new FormData()
    fd.append('file', file)
    fd.append('title', title)
    if (description) fd.append('description', description)
    uploadMutation.mutate(fd)
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Загрузить запись совещания</h1>
      <p className="text-gray-500 mb-8">
        Поддерживаются аудио и видеофайлы (MP3, WAV, MP4, MKV и др.) до 2 ГБ
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Drop zone */}
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
            ${isDragActive
              ? 'border-brand-500 bg-brand-50'
              : file
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300 hover:border-brand-400 hover:bg-gray-50'
            }
          `}
        >
          <input {...getInputProps()} />
          {file ? (
            <div className="flex flex-col items-center gap-2">
              <CheckCircle className="w-12 h-12 text-green-500" />
              <p className="font-medium text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500">{formatSize(file.size)}</p>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setFile(null) }}
                className="text-xs text-red-500 hover:underline mt-1"
              >
                Удалить
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              {isDragActive ? (
                <Upload className="w-12 h-12 text-brand-500 animate-bounce" />
              ) : (
                <FileVideo className="w-12 h-12 text-gray-300" />
              )}
              <div>
                <p className="font-medium text-gray-700">
                  {isDragActive ? 'Отпустите файл' : 'Перетащите файл или нажмите для выбора'}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  Аудио/видео до 2 ГБ
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className="card space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Название совещания <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Напр. Ежеквартальный обзор Q2 2025"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Описание
            </label>
            <textarea
              className="input resize-none"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Цель встречи, участники, контекст..."
            />
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={!file || !title || uploadMutation.isPending}
          className="btn-primary w-full justify-center py-3 text-base"
        >
          {uploadMutation.isPending ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Загрузка...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Загрузить и обработать
            </>
          )}
        </button>

        {/* Info */}
        <div className="rounded-lg bg-blue-50 border border-blue-100 p-4 text-sm text-blue-700">
          <p className="font-medium mb-1">Что произойдёт после загрузки:</p>
          <ol className="list-decimal list-inside space-y-1 text-blue-600">
            <li>Транскрибация аудио с помощью Whisper</li>
            <li>Автоматическая разметка спикеров (диаризация)</li>
            <li>NLP-анализ: ключевые слова, контакты, сентимент</li>
            <li>Генерация саммари и протокола</li>
            <li>Извлечение задач и поручений</li>
          </ol>
        </div>
      </form>
    </div>
  )
}
