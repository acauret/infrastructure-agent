import { TextareaHTMLAttributes, forwardRef } from 'react'
import clsx from 'clsx'

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className, ...props }, ref) {
    return (
      <textarea
        ref={ref}
        className={clsx(
          'w-full min-h-[100px] rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm',
          'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-sky-500 focus:border-sky-500',
          'placeholder:text-slate-400',
          className
        )}
        {...props}
      />
    )
  }
)
