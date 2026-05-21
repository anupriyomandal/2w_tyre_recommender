import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { AlertCircle } from 'lucide-react'
import type { ChatMessage } from '@/types'
import ToolCallCard from './ToolCallCard'

function styleContent(text: string): string {
  // Split lines that have multiple SKUs onto separate lines (blank line = paragraph break in markdown)
  const lines = text.split('\n').map(line => {
    if ((line.match(/SKU \d+:/g) ?? []).length <= 1) return line
    const firstColon = line.indexOf(':', line.indexOf('SKU '))
    const head = line.slice(0, firstColon + 1)
    const tail = line.slice(firstColon + 1)
    const parts = tail.split(/\s*-\s+(?=SKU \d+:)/)
    return head + parts[0] + (parts.length > 1 ? '\n\n' + parts.slice(1).join('\n\n') : '')
  })
  let result = lines.join('\n')

  // "SKU 100227: Tyre Name" → orange SKU + blue tyre name via HTML spans
  result = result.replace(
    /SKU (\d+): ([^\n<]+)/g,
    (_m, sku, name) =>
      `SKU <span style="color:#F58220;font-weight:700">${sku}</span>: <span style="color:#0055AA">${name.trim()}</span>`
  )

  // Standalone "SKU XXXXX" with no name after it
  result = result.replace(
    /SKU (\d+)(?!<\/span>|:)/g,
    `SKU <span style="color:#F58220;font-weight:700">$1</span>`
  )

  // Bold each variant name in "Applicable variants: A, B, C"
  result = result.replace(
    /^(Applicable variants:\s*)(.+)$/gim,
    (_m, prefix, variants) =>
      prefix + variants.split(',').map((v: string) => `**${v.trim()}**`).join(', ')
  )

  // Ensure tyre lines are separated by blank lines so markdown breaks them into paragraphs
  result = result.replace(
    /(<\/span>)\n(?=(?:Front|Rear|Applicable))/g,
    '$1\n\n'
  )

  return result
}

interface Props {
  message: ChatMessage
}

export default function MessageBubble({ message }: Props) {
  if (message.kind === 'user') {
    return (
      <div className="flex justify-end animate-slide-right-fade">
        <div
          className="max-w-xs lg:max-w-md px-4 py-3 rounded-2xl rounded-tr-sm text-white text-sm leading-relaxed"
          style={{ background: '#0055AA' }}
        >
          {message.content}
        </div>
      </div>
    )
  }

  if (message.kind === 'tools') {
    return (
      <div className="flex justify-start">
        <ToolCallCard rows={message.rows} collapsed={message.collapsed} />
      </div>
    )
  }

  if (message.kind === 'answer') {
    return (
      <div className="flex justify-start items-start gap-3 animate-slide-left-fade">
        {/* Avatar */}
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5"
          style={{ background: 'linear-gradient(135deg, #0055AA, #273C6F)' }}
        >
          C
        </div>

        {/* Bubble */}
        <div
          className="flex-1 max-w-lg bg-white rounded-2xl rounded-tl-sm px-5 py-4"
          style={{
            boxShadow: '0 2px 10px rgba(0,85,170,0.07)',
            border: '1px solid #e5edf8',
            borderBottom: '2px solid #F58220',
          }}
        >
          <div className="md text-sm text-slate-800">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
              {styleContent(message.content)}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    )
  }

  if (message.kind === 'error') {
    return (
      <div className="flex justify-start animate-slide-up-fade">
        <div
          className="flex items-start gap-2.5 px-4 py-3 rounded-xl text-sm max-w-md"
          style={{ background: '#FFF5F5', border: '1px solid #FED7D7', color: '#C53030' }}
        >
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{message.message}</span>
        </div>
      </div>
    )
  }

  return null
}
