import { useState, useRef, useCallback } from 'react'
import type { ChatMessage, ToolRow } from './types'
import Header from './components/Header'
import MessageList from './components/MessageList'
import ChatInput from './components/ChatInput'

const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8002').replace(/\/$/, '')

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [hasPendingTool, setHasPendingTool] = useState(false)

  const sessionId = useRef(crypto.randomUUID())
  const toolsMsgId = useRef<string | null>(null)
  const pendingCount = useRef(0)

  const resetSession = useCallback(async () => {
    await fetch(`${API_BASE}/session/${sessionId.current}`, { method: 'DELETE' }).catch(() => {})
    sessionId.current = crypto.randomUUID()
    toolsMsgId.current = null
    pendingCount.current = 0
    setMessages([])
    setIsStreaming(false)
    setHasPendingTool(false)
  }, [])

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isStreaming) return

    // Reset per-turn tracking
    const turnToolsId = crypto.randomUUID()
    toolsMsgId.current = null
    pendingCount.current = 0

    setMessages(prev => [...prev, { kind: 'user', id: crypto.randomUUID(), content }])
    setIsStreaming(true)
    setHasPendingTool(false)

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, session_id: sessionId.current }),
      })

      if (!response.ok) throw new Error(`Server error ${response.status}`)
      if (!response.body) throw new Error('No response body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) continue

          let ev: Record<string, unknown>
          try { ev = JSON.parse(trimmed) } catch { continue }

          switch (ev.type) {
            case 'tool_start': {
              const newRow: ToolRow = {
                id: ev.id as string,
                tool: ev.tool as string,
                label: ev.label as string,
                status: 'pending',
              }
              pendingCount.current++
              setHasPendingTool(true)

              if (!toolsMsgId.current) {
                toolsMsgId.current = turnToolsId
                setMessages(prev => [...prev, {
                  kind: 'tools', id: turnToolsId, rows: [newRow], collapsed: false,
                }])
              } else {
                setMessages(prev => prev.map(m =>
                  m.id === toolsMsgId.current && m.kind === 'tools'
                    ? { ...m, rows: [...m.rows, newRow] }
                    : m
                ))
              }
              break
            }

            case 'tool_done': {
              pendingCount.current = Math.max(0, pendingCount.current - 1)
              if (pendingCount.current === 0) setHasPendingTool(false)

              setMessages(prev => prev.map(m => {
                if (m.id !== toolsMsgId.current || m.kind !== 'tools') return m
                return { ...m, rows: m.rows.map((r: ToolRow) =>
                  r.id === ev.id ? { ...r, status: 'done' as const } : r
                )}
              }))
              break
            }

            case 'answer': {
              // Collapse only this turn's tools card
              setMessages(prev => [
                ...prev.map(m =>
                  m.id === toolsMsgId.current && m.kind === 'tools'
                    ? { ...m, collapsed: true }
                    : m
                ),
                { kind: 'answer', id: crypto.randomUUID(), content: ev.content as string },
              ])
              setHasPendingTool(false)
              break
            }

            case 'error': {
              setMessages(prev => [...prev, {
                kind: 'error', id: crypto.randomUUID(), message: ev.message as string,
              }])
              break
            }

            case 'done': {
              setIsStreaming(false)
              setHasPendingTool(false)
              break
            }
          }
        }
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        kind: 'error',
        id: crypto.randomUUID(),
        message: err instanceof Error ? err.message : 'An unexpected error occurred.',
      }])
    } finally {
      setIsStreaming(false)
      setHasPendingTool(false)
    }
  }, [isStreaming])

  // Show thinking dots when streaming but no tool is actively running
  const showThinking = isStreaming && !hasPendingTool

  return (
    <div className="flex flex-col h-full" style={{ background: '#EEF3FA' }}>
      <Header onReset={resetSession} />
      <MessageList
        messages={messages}
        showThinking={showThinking}
        onSuggestion={sendMessage}
      />
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  )
}
