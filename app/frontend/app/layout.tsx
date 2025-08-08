import './globals.css'
import type { ReactNode } from 'react'

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <div className="mx-auto size-full max-w-7xl px-4 sm:px-6 lg:px-8">
          <header className="py-6">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
              Infrastructure Operations Assistant
            </h1>
            <p className="mt-1 text-sm text-slate-600">Government-ready. Secure. Auditable.</p>
          </header>
          <main className="pb-10">{children}</main>
          <footer className="py-6 text-xs text-slate-500">© {new Date().getFullYear()} Agency IT</footer>
        </div>
      </body>
    </html>
  )
}
