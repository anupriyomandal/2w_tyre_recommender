import { useEffect, useRef } from 'react'
import { CircleDot } from 'lucide-react'
import type { ChatMessage } from '@/types'
import MessageBubble from './MessageBubble'
import ThinkingIndicator from './ThinkingIndicator'

interface Props {
  messages: ChatMessage[]
  showThinking: boolean
  onSuggestion: (q: string) => void
}

const SUGGESTIONS = [
  'What tyres fit a Hero Splendor?',
  'Bajaj Pulsar 150cc tyre recommendation',
  'Royal Enfield Classic 350 tyres',
  'Honda Activa front and rear tyre',
]

function Welcome({ onSuggestion }: { onSuggestion: (q: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6 py-12 animate-slide-up-fade">
      <div
        className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5 shadow-lg"
        style={{ background: 'linear-gradient(135deg, #0055AA 0%, #273C6F 100%)' }}
      >
        <CircleDot className="w-8 h-8 text-white" strokeWidth={1.5} />
      </div>

      <h2 className="text-lg font-semibold mb-1.5" style={{ color: '#273C6F' }}>
        CEAT Tyre Advisor
      </h2>
      <p className="text-slate-400 text-sm max-w-[280px] leading-relaxed mb-6">
        Ask me about CEAT tyres for any 2-wheeler. I'll find the right Front &amp; Rear fitment from our catalogue.
      </p>

      {/* Suggestion chips */}
      <div className="flex flex-wrap gap-2 justify-center max-w-sm">
        {SUGGESTIONS.map(q => (
          <button
            key={q}
            onClick={() => onSuggestion(q)}
            className="text-xs px-3.5 py-2 rounded-full font-medium transition-all duration-150 hover:scale-105 active:scale-95"
            style={{
              background: 'white',
              border: '1px solid #DBEAFE',
              color: '#0055AA',
              boxShadow: '0 1px 3px rgba(0,85,170,0.07)',
            }}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}

export default function MessageList({ messages, showThinking, onSuggestion }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, showThinking])

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-5">
      {messages.length === 0 ? (
        <Welcome onSuggestion={onSuggestion} />
      ) : (
        <div className="max-w-2xl mx-auto flex flex-col gap-4">
          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {showThinking && <ThinkingIndicator />}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
