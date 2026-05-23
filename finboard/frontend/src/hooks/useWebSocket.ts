import { useEffect, useRef, useCallback } from 'react'

export function useWebSocket(
  url: string,
  onMessage: (data: any) => void,
  reconnectInterval = 3000
) {
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    // Don't reconnect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage(data)
        } catch {}
      }

      ws.onclose = () => {
        wsRef.current = null
        setTimeout(connect, reconnectInterval)
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch {
      setTimeout(connect, reconnectInterval)
    }
  }, [url, onMessage, reconnectInterval])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])

  return wsRef
}
