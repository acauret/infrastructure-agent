import { InputHTMLAttributes, forwardRef } from 'react'
import clsx from 'clsx'

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input(
  { className, ...props },
  ref
) {
  return (
    <input
      ref={ref}
      className={clsx(
        'flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm',
        'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-sky-500 focus:border-sky-500',
        'placeholder:text-slate-400',
        className
      )}
      {...props}
    />
  )
})
