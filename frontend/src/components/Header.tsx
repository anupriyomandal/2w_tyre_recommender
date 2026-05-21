import { Trash2, CircleDot } from 'lucide-react'

interface HeaderProps {
  onReset: () => void
}

export default function Header({ onReset }: HeaderProps) {
  return (
    <header
      className="flex items-center justify-between px-6 py-3.5 shrink-0 shadow-md"
      style={{ background: 'linear-gradient(135deg, #273C6F 0%, #1e2f58 100%)' }}
    >
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div
          className="flex items-center justify-center w-9 h-9 rounded-xl shrink-0"
          style={{ background: 'rgba(245,130,32,0.18)', border: '1px solid rgba(245,130,32,0.35)' }}
        >
          <CircleDot className="w-5 h-5" style={{ color: '#F58220' }} strokeWidth={1.75} />
        </div>

        <div className="leading-none">
          <div className="flex items-baseline gap-1.5">
            <span className="text-white font-bold text-[1.25rem] tracking-tight">CEAT</span>
            <span
              className="w-[5px] h-[5px] rounded-full shrink-0 mb-0.5"
              style={{ background: '#F58220' }}
            />
          </div>
          <p className="text-[10px] font-medium tracking-[0.18em] uppercase mt-[1px]"
             style={{ color: 'rgba(180,200,240,0.65)' }}>
            Tyre Advisor
          </p>
        </div>
      </div>

      {/* Reset */}
      <button
        onClick={onReset}
        title="Reset conversation"
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 hover:scale-105 active:scale-95"
        style={{ color: 'rgba(180,200,240,0.6)' }}
        onMouseEnter={e => {
          e.currentTarget.style.color = 'white'
          e.currentTarget.style.background = 'rgba(255,255,255,0.1)'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.color = 'rgba(180,200,240,0.6)'
          e.currentTarget.style.background = 'transparent'
        }}
      >
        <Trash2 className="w-3.5 h-3.5" />
        <span>New chat</span>
      </button>
    </header>
  )
}
