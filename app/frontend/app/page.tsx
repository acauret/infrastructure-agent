'use client'

import { useEffect, useRef, useState } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send, Square } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type Message = { role: 'user' | 'assistant' | 'tool'; content: string }

export default function Page() {
  const [input, setInput] = useState('List Azure subscriptions; then check git repos user:acauret type:private')
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setInput('')
    setIsLoading(true)

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
    }
  }

  const handleStop = () => abortRef.current?.abort()

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
      <aside className="hidden lg:block lg:col-span-3">
        <Card>
          <CardHeader>
            <div className="text-sm font-medium text-slate-900">Sessions</div>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-slate-500">New session starts with each request.</div>
          </CardContent>
        </Card>
      </aside>
      <section className="lg:col-span-9">
        <Card>
          <CardHeader>
            <div className="text-base font-semibold text-slate-900">Operations Assistant</div>
            <div className="mt-1 text-xs text-slate-500">Government-ready. Secure. Auditable.</div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-3">
                {messages.length === 0 ? (
                  <div className="text-sm text-slate-500">Ask me to “List Azure subscriptions” and “Check git repos user:acauret type:private”.</div>
                ) : (
                  messages.map((m, i) => (
                    <div key={i} className={m.role === 'user' ? 'text-slate-900' : 'text-slate-800'}>
                      <div className="rounded-md border border-slate-200 bg-slate-50 p-3 whitespace-pre-wrap">
                        {m.content}
                      </div>
                    </div>
                  ))
                )}
              </div>
              <form onSubmit={handleSubmit} className="flex items-center gap-2">
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
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
