"use client"

import React, { useEffect, useRef, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Send, Square, Zap, Globe, GitBranch } from 'lucide-react'
import { ChatMessage } from '@/components/chat-message'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type Message = { role: 'user' | 'assistant' | 'tool'; content: string }

export default function Page() {
  const [input, setInput] = useState<string>('List Azure subscriptions; then check git repos user:acauret type:private')
  const [messages, setMessages] = useState<Array<Message>>([])
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<string>('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [pendingInputPrompt, setPendingInputPrompt] = useState<string | null>(null)
  const [pendingInputText, setPendingInputText] = useState<string>('')
  const abortRef = useRef<AbortController | null>(null)

  const scrollRef = useRef<HTMLDivElement | null>(null)
  useEffect(() => () => abortRef.current?.abort(), [])
  useEffect(() => {
    // Auto-scroll to bottom on new messages
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
  setMessages((prev: Array<Message>) => [...prev, { role: 'user', content: text }])
    setInput('')
    setIsLoading(true)
    setStatus('Connecting...')

    abortRef.current?.abort()
    const ac = new AbortController()
    abortRef.current = ac

    try {
      const res = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: text }),
        signal: ac.signal,
      })
      if (!res.ok || !res.body) throw new Error('Request failed')
      setStatus('Streaming...')
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let textBuffer = ''

      const handleEvent = (evt: any) => {
        const t = evt?.type
        switch (t) {
          case 'session':
            if (typeof evt?.id === 'string') setSessionId(evt.id)
            break
          case 'status':
            setStatus(evt?.text ?? '')
            break
          case 'request':
            // Backend also emits the user prompt; we already rendered it.
            break
          case 'input_request': {
            const prompt = typeof evt?.prompt === 'string' ? evt.prompt : 'Input requested'
            setPendingInputPrompt(prompt)
            setPendingInputText('')
            break
          }
          case 'message': {
            const content = typeof evt?.text === 'string' ? evt.text : ''
            setMessages((prev: Array<Message>) => [...prev, { role: 'assistant', content }])
            break
          }
          case 'chunk': {
            const delta = typeof evt?.text === 'string' ? evt.text : ''
            if (!delta) break
            setMessages((prev: Array<Message>) => {
              const last = prev[prev.length - 1]
              if (last && last.role === 'assistant') {
                return [...prev.slice(0, -1), { role: 'assistant', content: (last.content || '') + delta }]
              }
              return [...prev, { role: 'assistant', content: delta }]
            })
            break
          }
          case 'tool_call': {
            const calls = evt?.calls ?? (evt?.name ? [{ name: evt.name, arguments: evt?.arguments }] : [])
            let pretty = ''
            try { pretty = JSON.stringify(calls, null, 2) } catch { pretty = String(calls) }
            const header = `Tool call${evt?.agent ? ` (${evt.agent})` : ''}`
            setMessages((prev: Array<Message>) => [
              ...prev,
              { role: 'tool', content: `${header}\n\n\`\`\`json\n${pretty}\n\`\`\`` },
            ])
            break
          }
          case 'tool_result': {
            const results = evt?.results ?? (evt?.output ? [{ output: evt.output }] : [])
            let pretty = ''
            try { pretty = JSON.stringify(results, null, 2) } catch { pretty = String(results) }
            const header = `Tool result${evt?.agent ? ` (${evt.agent})` : ''}`
            setMessages((prev: Array<Message>) => [
              ...prev,
              { role: 'tool', content: `${header}\n\n\`\`\`json\n${pretty}\n\`\`\`` },
            ])
            break
          }
          case 'error': {
            const msg = evt?.text ?? 'Unknown error'
            setMessages((prev: Array<Message>) => [...prev, { role: 'assistant', content: `Error: ${msg}` }])
            break
          }
          default:
            // ignore other events or log as a subtle tool message if needed
            break
        }
      }

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        textBuffer += chunk
        let idx = textBuffer.indexOf('\n')
        while (idx !== -1) {
          const line = textBuffer.slice(0, idx).trim()
          textBuffer = textBuffer.slice(idx + 1)
          if (line.length > 0) {
            try { handleEvent(JSON.parse(line)) } catch { /* ignore malformed line */ }
          }
          idx = textBuffer.indexOf('\n')
        }
      }
      // Flush any remaining line
      const tail = textBuffer.trim()
      if (tail) {
        try { handleEvent(JSON.parse(tail)) } catch { /* ignore */ }
      }
    } catch (err: any) {
      setMessages((prev: Array<Message>) => [...prev, { role: 'assistant', content: `Error: ${err?.message ?? String(err)}` }])
    } finally {
      setIsLoading(false)
      setStatus('')
    }
  }

  const handleStop = () => abortRef.current?.abort()

  const submitPendingInput = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!sessionId) return
    const text = pendingInputText.trim()
    if (!text) return
    try {
      await fetch(`${API_BASE}/input`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session: sessionId, text }),
      })
      setPendingInputPrompt(null)
      setPendingInputText('')
      setMessages((prev: Array<Message>) => [...prev, { role: 'user', content: text }])
    } catch (err) {
      setStatus('Failed to send input')
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col rounded-2xl border border-slate-200 bg-white shadow-sm">
      {/* Top status bar */}
  <div className="flex items-center gap-4 border-b border-slate-200 px-4 py-2 text-xs text-slate-600 bg-gradient-to-r from-slate-50 to-white">
        <span className="inline-flex items-center gap-1"><Zap className="h-3.5 w-3.5 text-sky-600"/> Azure MCP</span>
        <span className="inline-flex items-center gap-1"><GitBranch className="h-3.5 w-3.5 text-emerald-600"/> GitHub MCP</span>
        <span className="inline-flex items-center gap-1"><Globe className="h-3.5 w-3.5 text-violet-600"/> Playwright</span>
        <span className="ml-auto text-slate-400">{status}</span>
      </div>

      {/* Messages */}
      <CardContent className="flex-1 overflow-y-auto bg-slate-50 p-4">
        <div ref={scrollRef as any} className="mx-auto flex max-w-3xl flex-col gap-3">
          {messages.length === 0 ? (
            <div className="mx-auto max-w-xl text-center text-sm text-slate-500">
              Ask me to “List Azure subscriptions” or “Check git repos user:acauret type:private”.
            </div>
          ) : (
            messages.map((m: Message, i: number) => (
              <div key={i}>
                <ChatMessage role={m.role} content={m.content} />
              </div>
            ))
          )}
        </div>
      </CardContent>

      {/* Composer */}
      <div className="border-t border-slate-200 bg-white p-3 space-y-2">
        <form onSubmit={handleSubmit} className="mx-auto grid max-w-3xl grid-cols-[1fr_auto_auto] items-start gap-2">
          <Textarea
            value={input}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInput(e.target.value)}
            placeholder="Describe your task… (Shift+Enter = newline, Enter = send)"
            onKeyDown={(e: React.KeyboardEvent<HTMLTextAreaElement>) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                if (!isLoading) void handleSubmit(e as any)
              }
            }}
            className="min-h-[44px] max-h-40"
          />
          <Button type="submit" disabled={isLoading} className="h-[44px]">
            <Send className="mr-2 h-4 w-4" />
            {isLoading ? 'Sending' : 'Send'}
          </Button>
          <Button type="button" onClick={handleStop} disabled={!isLoading} className="h-[44px] bg-slate-600 hover:bg-slate-700">
            <Square className="mr-2 h-4 w-4" /> Stop
          </Button>
        </form>

        {pendingInputPrompt && (
          <form onSubmit={submitPendingInput} className="mx-auto grid max-w-3xl grid-cols-[1fr_auto] items-start gap-2">
            <Textarea
              value={pendingInputText}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPendingInputText(e.target.value)}
              placeholder={pendingInputPrompt}
              className="min-h-[44px] max-h-40 border-amber-300"
            />
            <Button type="submit" disabled={!sessionId} className="h-[44px] bg-amber-600 hover:bg-amber-700">
              Reply
            </Button>
          </form>
        )}
      </div>
    </div>
  )
}
