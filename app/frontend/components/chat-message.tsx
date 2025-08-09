"use client"

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import clsx from 'clsx'

export type ChatRole = 'user' | 'assistant' | 'tool'

export function ChatMessage({ role, content }: { role: ChatRole; content: string }) {
  const isUser = role === 'user'
  // Normalize excessive whitespace to avoid huge gaps in rendering
  const sanitized = content
    .replace(/\r\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[\t ]+\n/g, '\n')
    .trimEnd()
  return (
    <div className={clsx('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx(
          'max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm transition-colors',
          isUser ? 'bg-sky-600 text-white' : 'bg-white text-slate-800 border border-slate-200'
        )}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw]}
          components={{
            a: (props: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
              <a {...props} className="text-sky-600 underline" />
            ),
            code: (props: React.HTMLAttributes<HTMLElement>) => (
              <code {...props} className="rounded bg-slate-100 px-1 py-0.5 text-[0.85em]" />
            ),
            pre: (props: React.HTMLAttributes<HTMLPreElement>) => (
              <pre {...props} className="overflow-auto rounded-md bg-slate-900 p-3 text-slate-100" />
            ),
            table: (props: React.TableHTMLAttributes<HTMLTableElement>) => (
              <div className="overflow-x-auto">
                <table {...props} className="w-full text-left text-sm" />
              </div>
            ),
            th: (props: React.ThHTMLAttributes<HTMLTableCellElement>) => (
              <th {...props} className="border-b border-slate-200 px-2 py-1 font-medium" />
            ),
            td: (props: React.TdHTMLAttributes<HTMLTableCellElement>) => (
              <td {...props} className="border-b border-slate-50 px-2 py-1" />
            ),
          }}
        >
          {sanitized}
        </ReactMarkdown>
      </div>
    </div>
  )
}
