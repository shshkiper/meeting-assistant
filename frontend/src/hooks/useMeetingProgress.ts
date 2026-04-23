import { useEffect, useState, useRef } from 'react'

interface ProgressState {
  step: string
  progress: number
  connected: boolean
}

export function useMeetingProgress(meetingId: string, enabled: boolean) {
  const [state, setState] = useState<ProgressState>({
    step: '',
    progress: 0,
    connected: false,
  })
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!enabled || !meetingId) return

    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${protocol}://${location.host}/ws/meetings/${meetingId}/progress`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setState((s) => ({ ...s, connected: true }))
    ws.onclose = () => setState((s) => ({ ...s, connected: false }))

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.ping) return
        setState((s) => ({
          ...s,
          step: msg.step ?? s.step,
          progress: msg.progress ?? s.progress,
        }))
      } catch {}
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [meetingId, enabled])

  return state
}
