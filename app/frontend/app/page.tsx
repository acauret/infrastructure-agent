'use client'

import type React from 'react'
import { useEffect, useRef, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send, Square, Zap, Globe, GitBranch } from 'lucide-react'
import { ChatMessage } from '@/components/chat-message'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type Message = { role: 'user' | 'assistant' | 'tool'; content: string }

export default function Page() {
  const [input, setInput] = useState('List Azure subscriptions; then check git repos user:acauret type:private')
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<string>('')
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
    setMessages(prev => [...prev, { role: 'user', content: text }])
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
      let buffer = ''
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        buffer += chunk
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.role === 'assistant') {
            return [...prev.slice(0, -1), { role: 'assistant', content: buffer }]
          }
          return [...prev, { role: 'assistant', content: buffer }]
        })
      }
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err?.message ?? String(err)}` }])
    } finally {
      setIsLoading(false)
      setStatus('')
    }
  }

  const handleStop = () => abortRef.current?.abort()

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col rounded-2xl border border-slate-200 bg-white shadow-sm">
      {/* Top status bar */}
      <div className="flex items-center gap-4 border-b border-slate-200 px-4 py-2 text-xs text-slate-600">
        <span className="inline-flex items-center gap-1"><Zap className="h-3.5 w-3.5 text-sky-600"/> Azure MCP</span>
        <span className="inline-flex items-center gap-1"><GitBranch className="h-3.5 w-3.5 text-emerald-600"/> GitHub MCP</span>
        <span className="inline-flex items-center gap-1"><Globe className="h-3.5 w-3.5 text-violet-600"/> Playwright</span>
        <span className="ml-auto text-slate-400">{status}</span>
      </div>

      {/* Messages */}
      <CardContent className="flex-1 overflow-y-auto bg-slate-50 p-4">
        <div className="mx-auto flex max-w-3xl flex-col gap-3">
          {messages.length === 0 ? (
            <div className="mx-auto max-w-xl text-center text-sm text-slate-500">
              Ask me to “List Azure subscriptions” or “Check git repos user:acauret type:private”.
            </div>
          ) : (
            messages.map((m, i) => <ChatMessage key={i} role={m.role} content={m.content} />)
          )}
        </div>
      </CardContent>

      {/* Composer */}
      <div className="border-t border-slate-200 bg-white p-3">
        <form onSubmit={handleSubmit} className="mx-auto flex max-w-3xl items-center gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your task…"
          />
          <Button type="submit" disabled={isLoading}>
            <Send className="mr-2 h-4 w-4" />
            {isLoading ? 'Sending' : 'Send'}
          </Button>
          <Button type="button" onClick={handleStop} disabled={!isLoading} className="bg-slate-600 hover:bg-slate-700">
            <Square className="mr-2 h-4 w-4" /> Stop
          </Button>
        </form>
      </div>
    </div>
  )
}
