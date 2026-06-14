import { onMounted, onUnmounted } from 'vue'

import { fetchRealtimeEventsSince, openRealtimeStream, type RealtimeEvent } from '@/api/events'
import { useAuthStore } from '@/stores/auth'

const LAST_EVENT_ID_KEY = 'tavern_realtime_last_event_id'
const REALTIME_EVENT_NAME = 'tavern:realtime-event'
const POLL_INTERVAL_MS = 3000
const ENABLE_SSE_STREAM = import.meta.env.VITE_ENABLE_SSE_STREAM === 'true'

let started = false
let controller: AbortController | null = null
let reconnectTimer: number | null = null
let pollTimer: number | null = null
let backfillInFlight = false

function getLastEventId() {
  return Number(localStorage.getItem(LAST_EVENT_ID_KEY) || '0') || 0
}

function setLastEventId(id: number) {
  if (id > getLastEventId()) {
    localStorage.setItem(LAST_EVENT_ID_KEY, String(id))
  }
}

function canUseRealtime() {
  const authStore = useAuthStore()
  return authStore.isAuthenticated && authStore.isReviewApproved && authStore.isAccountNormal
}

function dispatchRealtimeEvent(event: RealtimeEvent) {
  setLastEventId(event.id)
  window.dispatchEvent(new CustomEvent<RealtimeEvent>(REALTIME_EVENT_NAME, { detail: event }))
}

async function backfillEvents() {
  if (backfillInFlight || !canUseRealtime()) return
  backfillInFlight = true
  try {
    const resp = await fetchRealtimeEventsSince(getLastEventId())
    resp.results.forEach(dispatchRealtimeEvent)
    setLastEventId(resp.latest_cursor)
  } catch {
    // Network errors are recovered by the next polling tick or visibility refresh.
  } finally {
    backfillInFlight = false
  }
}

function clearReconnectTimer() {
  if (reconnectTimer !== null) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

function clearPollTimer() {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function scheduleReconnect() {
  if (reconnectTimer !== null) return
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    startStream()
  }, 3000)
}

async function startStream() {
  if (!canUseRealtime()) return

  controller?.abort()
  const localController = new AbortController()
  controller = localController
  try {
    await backfillEvents()
    await openRealtimeStream(getLastEventId(), localController.signal, dispatchRealtimeEvent)
  } catch {
    // Streaming connections can be interrupted by mobile browsers or network changes.
  } finally {
    if (controller === localController && !localController.signal.aborted) scheduleReconnect()
  }
}

function startPolling() {
  if (!canUseRealtime() || pollTimer !== null) return
  backfillEvents()
  pollTimer = window.setInterval(() => {
    if (document.visibilityState === 'visible') {
      backfillEvents()
    }
  }, POLL_INTERVAL_MS)
}

function stopStream() {
  controller?.abort()
  controller = null
  clearReconnectTimer()
}

function stopPolling() {
  clearPollTimer()
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    backfillEvents()
  }
}

export function startRealtimeEvents() {
  if (started) return
  started = true
  document.addEventListener('visibilitychange', handleVisibilityChange)

  if (ENABLE_SSE_STREAM) {
    startStream()
    return
  }
  startPolling()
}

export function stopRealtimeEvents() {
  started = false
  stopStream()
  stopPolling()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
}

export function useRealtimeEvent(handler: (event: RealtimeEvent) => void) {
  function listener(event: Event) {
    handler((event as CustomEvent<RealtimeEvent>).detail)
  }

  onMounted(() => window.addEventListener(REALTIME_EVENT_NAME, listener))
  onUnmounted(() => window.removeEventListener(REALTIME_EVENT_NAME, listener))
}
