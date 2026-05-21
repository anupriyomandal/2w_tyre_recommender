import { Search, FileText, Tag, CheckCircle2, Loader2, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ToolRow } from '@/types'

const TOOL_ICON: Record<string, React.ElementType> = {
  tyre_semantic_search: Search,
  product_description: FileText,
  landing_price: Tag,
}

function ToolRowItem({ row, index }: { row: ToolRow; index: number }) {
  const Icon = TOOL_ICON[row.tool] ?? FileText
  const done = row.status === 'done'

  return (
    <div
      className="flex items-center gap-3 py-2 animate-row-appear"
      style={{ animationDelay: `${index * 40}ms`, opacity: 0 }}
    >
      {/* Icon chip */}
      <div
        className={cn(
          'flex items-center justify-center w-7 h-7 rounded-lg shrink-0 transition-colors duration-300',
          done ? 'bg-slate-100' : 'bg-[#EEF3FA]'
        )}
      >
        <Icon
          className={cn('w-3.5 h-3.5 transition-colors duration-300', done ? 'text-slate-400' : 'text-[#0055AA]')}
        />
      </div>

      {/* Label */}
      <span
        className={cn(
          'flex-1 text-sm leading-snug transition-colors duration-300',
          done ? 'text-slate-400' : 'text-slate-700'
        )}
      >
        {row.label}
      </span>

      {/* Status */}
      <div className="shrink-0 w-5 flex items-center justify-center">
        {done ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
        ) : (
          <Loader2 className="w-4 h-4 text-[#0055AA] animate-spin" />
        )}
      </div>
    </div>
  )
}

interface ToolCallCardProps {
  rows: ToolRow[]
  collapsed: boolean
}

export default function ToolCallCard({ rows, collapsed }: ToolCallCardProps) {
  const allDone = rows.every(r => r.status === 'done')

  return (
    <div
      className={cn(
        'transition-all duration-500 ease-in-out animate-slide-left-fade',
        collapsed ? 'opacity-35 scale-[0.985]' : 'opacity-100 scale-100'
      )}
    >
      <div
        className="bg-white rounded-2xl rounded-tl-sm overflow-hidden"
        style={{
          border: '1px solid #e5edf8',
          borderLeft: '4px solid #0055AA',
          boxShadow: '0 2px 8px rgba(0,85,170,0.07)',
          maxWidth: '22rem',
        }}
      >
        {/* Header row */}
        <div
          className="flex items-center gap-2 px-4 py-2.5"
          style={{ borderBottom: '1px solid #f0f5fc', background: allDone ? '#fafcff' : '#f5f8ff' }}
        >
          <Zap
            className="w-3.5 h-3.5 transition-colors duration-500"
            style={{ color: allDone ? '#94a3b8' : '#F58220' }}
          />
          <span
            className="text-[10px] font-semibold tracking-[0.15em] uppercase transition-colors duration-500"
            style={{ color: allDone ? '#94a3b8' : '#273C6F' }}
          >
            {allDone ? 'Reasoned' : 'Reasoning…'}
          </span>
        </div>

        {/* Tool rows */}
        <div className="px-4 py-1 divide-y divide-slate-50">
          {rows.map((row, i) => (
            <ToolRowItem key={row.id} row={row} index={i} />
          ))}
        </div>
      </div>
    </div>
  )
}
