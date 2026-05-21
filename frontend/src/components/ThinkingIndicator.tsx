export default function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-3 animate-slide-left-fade">
      {/* Avatar */}
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
        style={{ background: 'linear-gradient(135deg, #0055AA, #273C6F)' }}
      >
        C
      </div>
      {/* Dots */}
      <div
        className="flex items-center gap-1 px-4 py-3 rounded-2xl rounded-tl-sm"
        style={{ background: 'white', boxShadow: '0 1px 4px rgba(0,85,170,0.08)', border: '1px solid #e5edf8' }}
      >
        {[0, 1, 2].map(i => (
          <span
            key={i}
            className="block rounded-full animate-bounce-dot"
            style={{
              width: '7px',
              height: '7px',
              background: '#0055AA',
              animationDelay: `${i * 0.18}s`,
            }}
          />
        ))}
      </div>
    </div>
  )
}
