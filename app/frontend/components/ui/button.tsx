import { ButtonHTMLAttributes } from 'react'
import clsx from 'clsx'

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2',
        'disabled:pointer-events-none disabled:opacity-50',
        'bg-sky-700 text-white hover:bg-sky-800 h-9 px-4 py-2',
        className
      )}
      {...props}
    />
  )
}
