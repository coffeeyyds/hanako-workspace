import { useState, useEffect } from 'react'

// Types
interface IndexData {
  symbol: string
  name: string
  price: number
  change_pct: number
  change_amount: number
}

// Index name display map
const INDEX_DISPLAY: Record<string, string> = {
  sh000001: '上证指数',
  sz399001: '深证成指',
  sz399006: '创业板指',
  sh000688: '科创50',
  sh000300: '沪深300',
  sh000016: '上证50',
  sz399905: '中证500',
  sh000852: '中证1000',
}

export default function IndexCards() {
  const [indexes, setIndexes] = useState<IndexData[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchIndexes = async () => {
      try {
        const res = await fetch('/api/stocks/indexes')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setIndexes(data)
        setError(null)
      } catch (e) {
        setError('等待后端启动...')
      }
    }

    fetchIndexes()
    const timer = setInterval(fetchIndexes, 5000) // refresh every 5s
    return () => clearInterval(timer)
  }, [])

  if (error) {
    return (
      <div className="dashboard-card">
        <div className="card-title">核心指数</div>
        <div className="text-terminal-muted text-sm">{error}</div>
      </div>
    )
  }

  return (
    <div className="dashboard-card">
      <div className="card-title">核心指数</div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {indexes.map((idx) => {
          const isUp = idx.change_pct > 0
          const isDown = idx.change_pct < 0
          const colorClass = isUp ? 'price-up' : isDown ? 'price-down' : 'price-flat'
          const arrow = isUp ? '▲' : isDown ? '▼' : '—'

          return (
            <div key={idx.symbol} className="text-center">
              <div className="text-xs text-terminal-muted truncate">
                {INDEX_DISPLAY[idx.symbol] || idx.name}
              </div>
              <div className={`mono-num text-lg font-semibold ${colorClass}`}>
                {idx.price.toFixed(2)}
              </div>
              <div className={`mono-num text-xs ${colorClass}`}>
                {arrow} {Math.abs(idx.change_pct).toFixed(2)}%
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
