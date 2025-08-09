"use client"

import React, { useMemo, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronRight, Copy } from 'lucide-react'

type ToolEventItem = {
  name?: string
  arguments?: any
  output?: any
}

export function ToolEventCard({
  kind,
  agent,
  items,
  defaultOpen = false,
  maxPreview = 1,
}: {
  kind: 'call' | 'result'
  agent?: string
  items: ToolEventItem[]
  defaultOpen?: boolean
  maxPreview?: number
}) {
  const [open, setOpen] = useState<boolean>(defaultOpen)
  const visible = open ? items : items.slice(0, maxPreview)
  const extra = Math.max(0, items.length - visible.length)

  const header = useMemo(() => {
    const label = kind === 'call' ? 'Tool call' : 'Tool result'
    const agentPart = agent ? ` (${agent})` : ''
    return `${label}${agentPart}`
  }, [kind, agent])

  const copyAll = async () => {
    try {
      const payload = { kind, agent, items }
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2))
    } catch {
      // ignore
    }
  }

  return (
    <Card className="border-slate-200">
      <div className="flex items-center justify-between px-3 py-2">
        <div className="text-sm font-medium text-slate-700">
          {header} <span className="text-slate-400">• {items.length} item{items.length !== 1 ? 's' : ''}</span>
        </div>
        <div className="flex items-center gap-2">
          {items.length > maxPreview && (
            <Button type="button" variant="ghost" size="sm" onClick={() => setOpen((v) => !v)} className="text-slate-600">
              {open ? <ChevronDown className="h-4 w-4"/> : <ChevronRight className="h-4 w-4"/>}
              {open ? 'Collapse' : `Expand (+${extra})`}
            </Button>
          )}
          <Button type="button" variant="ghost" size="sm" onClick={copyAll} className="text-slate-600">
            <Copy className="h-4 w-4 mr-1"/>
            Copy
          </Button>
        </div>
      </div>
      <CardContent className="space-y-3">
        {visible.map((it, idx) => {
          const title = it.name || (kind === 'call' ? 'call' : 'result')
          const body = kind === 'call' ? it.arguments : it.output
          let pretty = ''
          try {
            pretty = JSON.stringify(body, null, 2)
          } catch {
            pretty = String(body)
          }
          return (
            <div key={idx} className="rounded-md border border-slate-200 bg-white">
              <div className="px-3 py-2 text-xs font-semibold text-slate-600 border-b border-slate-200">{title}</div>
              <pre className="m-0 max-h-56 overflow-auto bg-slate-900 p-3 text-[12px] leading-5 text-slate-100 rounded-b-md">
{pretty}
              </pre>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
