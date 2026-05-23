import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts'

interface KlineData {
  symbol: string
  name: string
  price: number
  change_pct: number
  change_amount: number
  volume: number
  turnover: number
  high: number
  low: number
  open: number
  pre_close: number
}

// Mock K-line data until we have real historical data
function generateMockKline(basePrice: number): CandlestickData[] {
  const data: CandlestickData[] = []
  let price = basePrice
  const now = new Date()
  for (let i = 60; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    const timeStr = date.toISOString().split('T')[0]

    const change = (Math.random() - 0.48) * price * 0.03
    const open = price
    const close = price + change
    const high = Math.max(open, close) + Math.random() * price * 0.01
    const low = Math.min(open, close) - Math.random() * price * 0.01

    data.push({
      time: timeStr as Time,
      open: +open.toFixed(2),
      high: +high.toFixed(2),
      low: +low.toFixed(2),
      close: +close.toFixed(2),
    })
    price = close
  }
  return data
}

interface Props {
  symbol: string
  name: string
}

export default function StockChart({ symbol, name }: Props) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const [stock, setStock] = useState<KlineData | null>(null)

  // Fetch realtime data
  useEffect(() => {
    const fetchStock = async () => {
      try {
        const res = await fetch(`/api/stocks/spot/${symbol}`)
        if (!res.ok) return
        const data = await res.json()
        setStock(data)
      } catch {}
    }
    fetchStock()
    const timer = setInterval(fetchStock, 5000)
    return () => clearInterval(timer)
  }, [symbol])

  // Setup chart
  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#12171f' },
        textColor: '#5c6e80',
      },
      grid: {
        vertLines: { color: '#1e2a3a' },
        horzLines: { color: '#1e2a3a' },
      },
      crosshair: {
        mode: 0,
      },
      timeScale: {
        borderColor: '#1e2a3a',
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: '#1e2a3a',
      },
    })

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#00d4aa',
      downColor: '#ff4757',
      borderUpColor: '#00d4aa',
      borderDownColor: '#ff4757',
      wickUpColor: '#00d4aa',
      wickDownColor: '#ff4757',
    })

    const mockData = generateMockKline(stock?.price || 15)
    candleSeries.setData(mockData)

    chartRef.current = chart

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [stock?.price])

  const isUp = (stock?.change_pct ?? 0) > 0
  const colorClass = isUp ? 'price-up' : 'price-down'

  return (
    <div className="dashboard-card">
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-sm font-semibold">{name}</span>
          <span className="text-xs text-terminal-muted ml-2">{symbol}</span>
        </div>
        {stock && (
          <div className="text-right">
            <div className={`mono-num text-xl font-bold ${colorClass}`}>
              {stock.price.toFixed(2)}
            </div>
            <div className={`mono-num text-xs ${colorClass}`}>
              {isUp ? '▲' : '▼'} {stock.change_pct.toFixed(2)}%
            </div>
          </div>
        )}
      </div>
      <div ref={chartContainerRef} />
    </div>
  )
}
