import { useRef, useState, KeyboardEvent } from 'react'
import { SendHorizonal } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  onSend: (message: string) => void
  disabled: boolean
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }

  const canSend = !disabled && value.trim().length > 0

  return (
    <div
      className="shrink-0 px-4 py-3"
      style={{ background: 'white', borderTop: '1px solid #e5edf8' }}
    >
      <div className="max-w-2xl mx-auto flex items-end gap-3">
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={disabled}
          placeholder="Ask about CEAT tyres for your 2-wheeler…"
          rows={1}
          className={cn(
            'flex-1 resize-none rounded-xl px-4 py-3',
            'text-sm text-slate-800 placeholder:text-slate-400',
            'transition-all duration-150 scrollbar-thin',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'focus:outline-none',
          )}
          style={{
            background: '#F5F8FD',
            border: '1.5px solid #DBEAFE',
            lineHeight: '1.55',
            maxHeight: '160px',
          }}
          onFocus={e => { e.currentTarget.style.border = '1.5px solid #0055AA'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(0,85,170,0.12)' }}
          onBlur={e => { e.currentTarget.style.border = '1.5px solid #DBEAFE'; e.currentTarget.style.boxShadow = 'none' }}
        />

        {/* Send button */}
        <button
          onClick={submit}
          disabled={!canSend}
          className={cn(
            'flex items-center justify-center w-11 h-11 rounded-xl shrink-0 text-white',
            'transition-all duration-150',
            canSend
              ? 'hover:scale-105 active:scale-95 hover:brightness-110'
              : 'opacity-35 cursor-not-allowed',
          )}
          style={{ background: '#F58220' }}
        >
          <SendHorizonal className="w-5 h-5" />
        </button>
      </div>

      <p className="text-center text-[11px] mt-1.5 max-w-2xl mx-auto" style={{ color: '#C4CED8' }}>
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}
