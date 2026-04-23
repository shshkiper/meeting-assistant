// ── Domain types shared across the frontend ──────────────────────────────────

export type MeetingStatus =
  | 'uploaded'
  | 'transcribing'
  | 'diarizing'
  | 'analyzing'
  | 'completed'
  | 'failed'

export type TaskStatus = 'open' | 'in_progress' | 'done' | 'cancelled'
export type Priority   = 'high' | 'medium' | 'low'

export interface User {
  id: string
  email: string
  full_name: string
  role: 'admin' | 'manager' | 'member'
  is_active: boolean
  created_at: string
}

export interface Meeting {
  id: string
  title: string
  description: string | null
  meeting_date: string | null
  duration_seconds: number | null
  status: MeetingStatus
  owner_id: string
  created_at: string
  updated_at: string
}

export interface MeetingDetail extends Meeting {
  transcript: Transcript | null
  protocol: Protocol | null
  tasks: Task[]
  participants: Participant[]
}

export interface Segment {
  speaker: string
  start: number
  end: number
  text: string
}

export interface Transcript {
  id: string
  meeting_id: string
  raw_text: string | null
  segments: Segment[] | null
  language_detected: string | null
  summary: string | null
  keywords: Array<{ word: string; score: number }> | null
  contacts: Array<{ name?: string; email?: string; phone?: string }> | null
  sentiment: {
    overall: string
    scores: Record<string, number>
    segments: Array<{ speaker: string; sentiment: string; scores: Record<string, number> }>
  } | null
  created_at: string
}

export interface Protocol {
  id: string
  meeting_id: string
  content_md: string | null
  content_html: string | null
  agenda: string[] | null
  decisions: string[] | null
  next_meeting_date: string | null
  created_at: string
  updated_at: string
}

export interface Task {
  id: string
  meeting_id: string
  title: string
  description: string | null
  assignee_id: string | null
  assignee_name_raw: string | null
  due_date: string | null
  priority: Priority
  status: TaskStatus
  jira_key: string | null
  source_segment: string | null
  created_at: string
}

export interface Participant {
  id: string
  speaker_label: string
  display_name: string | null
  role_in_meeting: string | null
}

export interface DashboardStats {
  total_meetings: number
  completed_meetings: number
  total_tasks: number
}
