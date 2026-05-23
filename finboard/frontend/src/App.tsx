import { useState } from 'react'
import { BarChart3, TrendingUp, Coins, Newspaper, Globe, Zap, ChevronDown } from 'lucide-react'
import Dashboard from './components/Dashboard'
import StockChart from './components/StockChart'

type TabKey = 'dashboard' | 'stocks' | 'crypto' | 'macro' | 'news'

const TABS: { key: TabKey; label: string; icon: React.ElementType }[] = [
  { key: 'dashboard', label: '总览', icon: BarChart3 },
  { key: 'stocks', label: 'A股', icon: TrendingUp },
  { key: 'crypto', label: '币圈', icon: Coins },
  { key: 'macro', label: '宏观', icon: Globe },
  { key: 'news', label: 'AI资讯', icon: Newspaper },
]

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard')
  const [stockSearch, setStockSearch] = useState('')
  const [watchedStocks] = useState(['000001', '600519'])

  return (
    <div className="min-h-screen bg-terminal-bg">
      {/* Header */}
      <header className="border-b border-terminal-border bg-terminal-panel/50 backdrop-blur sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 flex items-center justify-between h-12">
          <div className="flex items-center gap-3">
            <Zap size={18} className="text-terminal-blue" />
            <h1 className="text-sm font-bold tracking-wider text-terminal-text">
              FinBoard
            </h1>
          </div>

          <div className="flex items-center gap-1">
            {TABS.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.key
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`
                    flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors
                    ${isActive
                      ? 'bg-terminal-blue/15 text-terminal-blue border border-terminal-blue/30'
                      : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-border/30 border border-transparent'
                    }
                  `}
                >
                  <Icon size={14} />
                  {tab.label}
                </button>
              )
            })}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1600px] mx-auto px-4 sm:px-6 py-4">
        {activeTab === 'dashboard' && <Dashboard />}

        {activeTab === 'stocks' && (
          <div className="space-y-4">
            {/* Quick symbol search */}
            <div className="dashboard-card flex items-center gap-4">
              <span className="text-xs text-terminal-muted whitespace-nowrap">快速查看</span>
              <div className="flex gap-2 flex-wrap">
                {watchedStocks.map((s) => (
                  <button
                    key={s}
                    onClick={() => setStockSearch(s)}
                    className={`px-3 py-1 rounded text-xs mono-num border transition-colors ${
                      stockSearch === s
                        ? 'border-terminal-blue text-terminal-blue bg-terminal-blue/10'
                        : 'border-terminal-border text-terminal-muted hover:border-terminal-muted'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
              <input
                type="text"
                placeholder="输入股票代码..."
                value={stockSearch}
                onChange={(e) => setStockSearch(e.target.value)}
                className="ml-auto bg-terminal-bg border border-terminal-border rounded px-3 py-1 text-xs mono-num text-terminal-text focus:outline-none focus:border-terminal-blue w-40"
              />
            </div>

            {stockSearch && (
              <StockChart symbol={stockSearch} name={stockSearch} />
            )}
          </div>
        )}

        {activeTab === 'crypto' && (
          <div className="dashboard-card">
            <div className="card-title">加密货币</div>
            <p className="text-terminal-muted text-sm">Phase 3 实现，敬请期待...</p>
          </div>
        )}

        {activeTab === 'macro' && (
          <div className="dashboard-card">
            <div className="card-title">宏观经济</div>
            <p className="text-terminal-muted text-sm">Phase 4 实现，敬请期待...</p>
          </div>
        )}

        {activeTab === 'news' && (
          <div className="dashboard-card">
            <div className="card-title">AI 最新动态</div>
            <p className="text-terminal-muted text-sm">Phase 5 实现，敬请期待...</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-terminal-border mt-8 py-3 text-center">
        <span className="text-xs text-terminal-muted">
          FinBoard v0.1 · 数据来源: AKShare, yfinance, Binance · AI: DeepSeek
        </span>
      </footer>
    </div>
  )
}
