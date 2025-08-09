import { ButtonHTMLAttributes } from 'react'
import clsx from 'clsx'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({ className, variant = 'primary', size = 'md', ...props }: ButtonProps) {
  const variantClasses =
    variant === 'ghost'
      ? 'bg-transparent text-slate-700 hover:bg-slate-100'
      : 'bg-sky-700 text-white hover:bg-sky-800'

  const sizeClasses = size === 'sm' ? 'h-8 px-3' : size === 'lg' ? 'h-10 px-5' : 'h-9 px-4'

  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2',
        'disabled:pointer-events-none disabled:opacity-50',
        variantClasses,
        sizeClasses,
        className
      )}
      {...props}
    />
  )
}
