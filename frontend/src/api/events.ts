import { apiBaseURL, apiClient } from './client'
import { getAccessToken } from '@/stores/auth'

export interface RealtimeEvent {
  id: number
  type: string
  target_type: string
  target_id: string
  payload: Record<string, unknown>
  created_at: string
}

export interface RealtimeEventsSinceResponse {
  results: RealtimeEvent[]
  latest_cursor: number
}

export async function fetchRealtimeEventsSince(cursor: number): Promise<RealtimeEventsSinceResponse> {
  const resp = await apiClient.get<RealtimeEventsSinceResponse>('/v1/events/since/', { params: { cursor } })
  return resp.data
}

export function getRealtimeStreamUrl(cursor: number) {
  return `${apiBaseURL}/v1/events/stream/?cursor=${encodeURIComponent(String(cursor))}`
}

export async function openRealtimeStream(cursor: number, signal: AbortSignal, onEvent: (event: RealtimeEvent) => void) {
  const token = getAccessToken()
  if (!token) return

  const response = await fetch(getRealtimeStreamUrl(cursor), {
    headers: { Authorization: `Bearer ${token}` },
    signal,
  })
  if (!response.ok || !response.body) {
    throw new Error(`实时事件连接失败：${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (!signal.aborted) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let separatorIndex = buffer.indexOf('\n\n')
    while (separatorIndex >= 0) {
      const chunk = buffer.slice(0, separatorIndex)
      buffer = buffer.slice(separatorIndex + 2)
      parseSseChunk(chunk, onEvent)
      separatorIndex = buffer.indexOf('\n\n')
    }
  }
}

function parseSseChunk(chunk: string, onEvent: (event: RealtimeEvent) => void) {
  const lines = chunk.split('\n')
  const dataLines = lines
    .filter(line => line.startsWith('data:'))
    .map(line => line.slice(5).trimStart())
  if (dataLines.length === 0) return

  try {
    const event = JSON.parse(dataLines.join('\n')) as RealtimeEvent
    onEvent(event)
  } catch {
    // Ignore malformed SSE payloads; the next reconnect/backfill will recover.
  }
}
