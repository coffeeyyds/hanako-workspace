import { useState, useEffect } from 'react'
import {
  TrendingUp, Landmark, DollarSign, Coins, BarChart3, Globe, Newspaper,
  ChevronRight, Activity, Gauge, ShieldAlert, Flame
} from 'lucide-react'

// ---- Types ----
interface OverviewData {
  a_share_sentiment: Record<string, number>
  bond_snapshot: Record<string, number>
  fx_snapshot: Record<string, number>
  global_indexes: GlobalIndex[]
  crypto_snapshot: Record<string, number | string>
  commodity_snapshot: Record<string, CommodityItem>
  polymarket_snapshot: PolymarketItem[]
  updated_at: string
}
interface GlobalIndex { symbol: string; name: string; price: number; change_pct: number }
interface CommodityItem { name: string; price: number; change_pct: number }
interface PolymarketItem { question: string; outcomes: string; probability: number; volume_24h: number }

// ---- Helpers ----
function PriceSpan({ value, decimals = 2, prefix = '', suffix = '' }: {
  value: number; decimals?: number; prefix?: string; suffix?: string
}) {
  const isUp = value > 0
  const isDown = value < 0
  const cls = isUp ? 'price-up' : isDown ? 'price-down' : 'price-flat'
  const arrow = isUp ? '▲' : isDown ? '▼' : ''
  return (
    <span className={`mono-num font-semibold ${cls}`}>
      {arrow} {prefix}{Math.abs(value).toFixed(decimals)}{suffix}
    </span>
  )
}

function PriceValue({ value, decimals = 2, prefix = '' }: { value: number; decimals?: number; prefix?: string }) {
  return <span className="mono-num font-semibold text-terminal-text">{prefix}{value.toFixed(decimals)}</span>
}

function ChangePill({ value }: { value: number }) {
  const isUp = value > 0
  const cls = isUp ? 'bg-terminal-green/10 text-terminal-green' : value < 0 ? 'bg-terminal-red/10 text-terminal-red' : 'bg-terminal-border/30 text-terminal-muted'
  return (
    <span className={`mono-num text-[11px] px-1.5 py-0.5 rounded font-semibold ${cls}`}>
      {value > 0 ? '+' : ''}{value.toFixed(2)}%
    </span>
  )
}

// ---- Mini Card ----
function MiniCard({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <div className="dashboard-card h-full">
      <div className="flex items-center gap-1.5 mb-2">
        <Icon size={13} className="text-terminal-blue" />
        <span className="card-title !mb-0">{title}</span>
      </div>
      {children}
    </div>
  )
}

// ---- Main ----
export default function Dashboard() {
  const [data, setData] = useState<OverviewData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('/api/overview')
        if (!res.ok) throw new Error('API not ready')
        const d = await res.json()
        setData(d)
        setLoading(false)
      } catch {
        // Backend not ready yet
      }
    }
    fetchData()
    const t = setInterval(fetchData, 10000) // every 10 seconds
    return () => clearInterval(t)
  }, [])

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Activity size={32} className="text-terminal-blue mx-auto mb-3 animate-pulse" />
          <p className="text-terminal-muted text-sm">正在连接后端服务...</p>
          <p className="text-terminal-muted/50 text-xs mt-1">请确保已运行 docker compose up -d</p>
        </div>
      </div>
    )
  }

  const {
    a_share_sentiment: a,
    bond_snapshot: bond,
    fx_snapshot: fx,
    global_indexes: indexes = [],
    crypto_snapshot: crypto,
    commodity_snapshot: comm = {},
    polymarket_snapshot: poly = [],
  } = data

  return (
    <div className="space-y-3">
      {/* ====== ROW 1: 全球指数一览条 ====== */}
      <div className="dashboard-card overflow-x-auto">
        <div className="flex items-center gap-1.5 mb-2">
          <Globe size={13} className="text-terminal-blue" />
          <span className="card-title !mb-0">全球指数</span>
        </div>
        <div className="flex gap-4 overflow-x-auto pb-1">
          {/* A-share indexes (from local storage, always fresh) */}
          <AIndexStrip />
          {/* Global indexes from overview */}
          {indexes.slice(0, 7).map((idx) => (
            <div key={idx.symbol} className="flex-shrink-0 min-w-[90px] text-center">
              <div className="text-[10px] text-terminal-muted truncate">{idx.name}</div>
              <div className="mono-num text-sm font-semibold text-terminal-text mt-0.5">
                {idx.price ? idx.price.toLocaleString() : '—'}
              </div>
              {idx.price > 0 && <ChangePill value={idx.change_pct} />}
            </div>
          ))}
        </div>
      </div>

      {/* ====== ROW 2: 四列卡片 ====== */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* A股情绪 */}
        <MiniCard title="A股情绪" icon={Activity}>
          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">上涨/下跌</span>
              <span className="text-xs">
                <span className="price-up">{a.up_count}</span>
                <span className="text-terminal-muted"> / </span>
                <span className="price-down">{a.down_count}</span>
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">涨停/跌停</span>
              <span className="text-xs">
                <span className="price-up font-bold">{a.limit_up_count}</span>
                <span className="text-terminal-muted"> / </span>
                <span className="price-down font-bold">{a.limit_down_count}</span>
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">成交额</span>
              <span className="text-xs mono-num text-terminal-text">{((a.total_turnover_yi || 0) / 10000).toFixed(2)}万亿</span>
            </div>
            <div className="mt-1 pt-1 border-t border-terminal-border">
              <div className="flex justify-between items-center">
                <span className="text-xs text-terminal-muted">涨跌比</span>
                <span className="text-xs mono-num text-terminal-text">{a.up_ratio}%</span>
              </div>
            </div>
          </div>
        </MiniCard>

        {/* 债市利率 */}
        <MiniCard title="债市利率" icon={Landmark}>
          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">LPR 1Y</span>
              <PriceValue value={bond.lpr_1y || 0} suffix="%" />
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">LPR 5Y</span>
              <PriceValue value={bond.lpr_5y || 0} suffix="%" />
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">Shibor 隔夜</span>
              <PriceValue value={bond.shibor_on || 0} decimals={4} suffix="%" />
            </div>
            <div className="mt-1 pt-1 border-t border-terminal-border">
              <div className="flex justify-between items-center">
                <span className="text-xs text-terminal-muted">10Y 国债</span>
                <PriceValue value={bond.cn_10y_yield || 0} suffix="%" />
              </div>
            </div>
          </div>
        </MiniCard>

        {/* 汇率 */}
        <MiniCard title="汇率" icon={DollarSign}>
          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">USD/CNY</span>
              <PriceValue value={fx.usd_cny || 0} decimals={4} />
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">EUR/USD</span>
              <PriceValue value={fx.eur_usd || 0} decimals={4} />
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">USD/JPY</span>
              <PriceValue value={fx.usd_jpy || 0} decimals={2} />
            </div>
            <div className="mt-1 pt-1 border-t border-terminal-border">
              <div className="flex justify-between items-center">
                <span className="text-xs text-terminal-muted">美元指数</span>
                <PriceValue value={fx.usd_index || 0} decimals={2} />
              </div>
            </div>
          </div>
        </MiniCard>

        {/* 币圈 */}
        <MiniCard title="币圈" icon={Coins}>
          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">BTC</span>
              <div className="flex items-center gap-1">
                <span className="text-xs mono-num font-semibold text-terminal-text">
                  ${(crypto.btc_price as number || 0).toLocaleString()}
                </span>
                <ChangePill value={crypto.btc_change_24h as number || 0} />
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-terminal-muted">ETH</span>
              <div className="flex items-center gap-1">
                <span className="text-xs mono-num font-semibold text-terminal-text">
                  ${(crypto.eth_price as number || 0).toLocaleString()}
                </span>
                <ChangePill value={crypto.eth_change_24h as number || 0} />
              </div>
            </div>
            <div className="mt-1 pt-1 border-t border-terminal-border">
              <div className="flex justify-between items-center">
                <span className="text-xs text-terminal-muted">恐惧贪婪</span>
                <span className={`text-xs mono-num font-bold ${
                  (crypto.fear_greed_value as number) > 70 ? 'price-up' :
                  (crypto.fear_greed_value as number) < 30 ? 'price-down' :
                  'text-terminal-yellow'
                }`}>
                  {crypto.fear_greed_value || '—'} 
                  <span className="text-terminal-muted font-normal ml-0.5">{crypto.fear_greed_classification as string || ''}</span>
                </span>
              </div>
            </div>
          </div>
        </MiniCard>
      </div>

      {/* ====== ROW 3: 大宗 + Polymarket ====== */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* 大宗商品 */}
        <MiniCard title="大宗商品" icon={BarChart3}>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(comm).slice(0, 5).map(([symbol, item]) => (
              <div key={symbol} className="text-center bg-terminal-bg/50 rounded p-2">
                <div className="text-[10px] text-terminal-muted mb-0.5">{item.name.split('(')[0]}</div>
                <div className="mono-num text-xs font-semibold text-terminal-text">
                  {item.price.toFixed(1)}
                </div>
                <ChangePill value={item.change_pct} />
              </div>
            ))}
          </div>
        </MiniCard>

        {/* Polymarket */}
        <MiniCard title="Polymarket 预测" icon={Gauge}>
          {poly.length === 0 ? (
            <div className="text-xs text-terminal-muted">加载中（需翻墙连接 Polymarket API）...</div>
          ) : (
            <div className="space-y-2">
              {poly.slice(0, 4).map((p, i) => (
                <div key={i} className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="text-xs truncate text-terminal-text">{p.question}</div>
                    <div className="text-[10px] text-terminal-muted mt-0.5">
                      {p.outcomes} · 24h ${(p.volume_24h || 0).toLocaleString()}
                    </div>
                  </div>
                  <div className={`mono-num text-sm font-bold flex-shrink-0 ${
                    p.probability > 60 ? 'price-up' : p.probability < 40 ? 'price-down' : 'text-terminal-yellow'
                  }`}>
                    {p.probability}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </MiniCard>
      </div>

      {/* ====== ROW 4: 涨停板 + 热门板块（A股深度可选） ====== */}
      <AtagDetail />
    </div>
  )
}

// ---- A股指数条（复用独立请求，更实时） ----
function AIndexStrip() {
  const [indexes, setIndexes] = useState<any[]>([])
  const NAME_MAP: Record<string, string> = {
    sh000001: '上证', sz399001: '深证', sz399006: '创业板',
    sh000688: '科创50', sh000300: '沪深300',
  }

  useEffect(() => {
    const fetchIdx = async () => {
      try {
        const res = await fetch('/api/stocks/indexes')
        if (!res.ok) return
        const data = await res.json()
        setIndexes(data)
      } catch {}
    }
    fetchIdx()
    const t = setInterval(fetchIdx, 5000)
    return () => clearInterval(t)
  }, [])

  return (
    <>
      {indexes.filter((i: any) => NAME_MAP[i.symbol]).map((idx: any) => (
        <div key={idx.symbol} className="flex-shrink-0 min-w-[80px] text-center">
          <div className="text-[10px] text-terminal-muted">{NAME_MAP[idx.symbol]}</div>
          <div className={`mono-num text-sm font-semibold mt-0.5 ${
            idx.change_pct > 0 ? 'price-up' : idx.change_pct < 0 ? 'price-down' : ''
          }`}>{idx.price.toFixed(0)}</div>
          <ChangePill value={idx.change_pct || 0} />
        </div>
      ))}
    </>
  )
}

// ---- A股深度（涨停板 + 热门板块） ----
function AtagDetail() {
  const [limitUps, setLimitUps] = useState<any[]>([])
  const [sectors, setSectors] = useState<any[]>([])

  useEffect(() => {
    const fetch = async () => {
      try {
        const [luRes, scRes] = await Promise.all([
          fetch('/api/stocks/limit-up'),
          fetch('/api/stocks/sectors?limit=10'),
        ])
        if (luRes.ok) setLimitUps((await luRes.json()).slice(0, 15))
        if (scRes.ok) setSectors(await scRes.json())
      } catch {}
    }
    fetch()
    const t = setInterval(fetch, 15000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      {/* 涨停板 */}
      <div className="dashboard-card">
        <div className="flex items-center gap-1.5 mb-2">
          <Flame size={13} className="text-terminal-red" />
          <span className="card-title !mb-0">涨停板</span>
        </div>
        <div className="overflow-x-auto max-h-64 overflow-y-auto">
          <table className="w-full text-[11px]">
            <thead className="sticky top-0 bg-terminal-panel">
              <tr className="text-terminal-muted border-b border-terminal-border">
                <th className="text-left py-1 px-1.5">股票</th>
                <th className="text-right py-1 px-1.5">涨幅</th>
                <th className="text-right py-1 px-1.5">连板</th>
                <th className="text-right py-1 px-1.5">封单(亿)</th>
              </tr>
            </thead>
            <tbody>
              {limitUps.map((item, i) => (
                <tr key={i} className="border-b border-terminal-border/30 hover:bg-terminal-border/20">
                  <td className="py-1 px-1.5">
                    <span className="font-medium">{item.name}</span>
                    <span className="text-terminal-muted ml-1">{item.symbol}</span>
                  </td>
                  <td className="text-right py-1 px-1.5 price-up mono-num">{item.change_pct?.toFixed(1)}%</td>
                  <td className="text-right py-1 px-1.5">
                    <span className={item.consecutive_days >= 3 ? 'text-terminal-yellow font-bold' : ''}>
                      {item.consecutive_days}板
                    </span>
                  </td>
                  <td className="text-right py-1 px-1.5 mono-num text-terminal-muted">
                    {((item.limit_order_amount || 0) / 1e8).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 热门板块 */}
      <div className="dashboard-card">
        <div className="flex items-center gap-1.5 mb-2">
          <TrendingUp size={13} className="text-terminal-green" />
          <span className="card-title !mb-0">热门板块</span>
        </div>
        <div className="overflow-x-auto max-h-64 overflow-y-auto">
          <table className="w-full text-[11px]">
            <thead className="sticky top-0 bg-terminal-panel">
              <tr className="text-terminal-muted border-b border-terminal-border">
                <th className="text-left py-1 px-1.5">板块</th>
                <th className="text-right py-1 px-1.5">涨幅</th>
                <th className="text-left py-1 px-1.5">领涨股</th>
              </tr>
            </thead>
            <tbody>
              {sectors.map((s, i) => (
                <tr key={i} className="border-b border-terminal-border/30 hover:bg-terminal-border/20">
                  <td className="py-1 px-1.5 font-medium">{s.sector_name}</td>
                  <td className="text-right py-1 px-1.5">
                    <ChangePill value={s.change_pct || 0} />
                  </td>
                  <td className="py-1 px-1.5 text-terminal-muted">{s.leading_stock}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
