"use client"

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import clsx from 'clsx'

export type ChatRole = 'user' | 'assistant' | 'tool'

export function ChatMessage({ role, content }: { role: ChatRole; content: string }) {
  const isUser = role === 'user'
  return (
    <div className={clsx('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx(
          'max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm shadow-sm transition-colors',
          isUser ? 'bg-sky-600 text-white' : 'bg-white text-slate-800 border border-slate-200'
        )}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw]}
          components={{
            a: (props) => <a {...props} className="text-sky-600 underline" />,
            code: (props) => (
              <code {...props} className="rounded bg-slate-100 px-1 py-0.5 text-[0.85em]" />
            ),
            pre: (props) => (
              <pre {...props} className="overflow-auto rounded-md bg-slate-900 p-3 text-slate-100" />
            ),
            table: (props) => (
              <div className="overflow-x-auto">
                <table {...props} className="w-full text-left text-sm" />
              </div>
            ),
            th: (props) => <th {...props} className="border-b border-slate-200 px-2 py-1 font-medium" />,
            td: (props) => <td {...props} className="border-b border-slate-50 px-2 py-1" />,
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  )
}
