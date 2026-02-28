import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts'
import { 
  TrendingUp, TrendingDown, Search, Globe, Share2, 
  AlertTriangle, CheckCircle, Loader2, RefreshCw 
} from 'lucide-react'

const queryClient = new QueryClient()

const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444']

function Dashboard() {
  const [siteUrl, setSiteUrl] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  // Fetch overview data
  const { data: overviewData, isLoading, refetch } = useQuery({
    queryKey: ['overview'],
    queryFn: async () => {
      const res = await fetch('/api/ui/overview')
      return res.json()
    },
    refetchInterval: 30000
  })

  // Run analysis
  const runAnalysis = async () => {
    if (!siteUrl) return
    
    setIsAnalyzing(true)
    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          website_url: siteUrl,
          days: 30,
          channels: ['gsc', 'ga4', 'meta']
        })
      })
      const result = await res.json()
      if (result.success) {
        refetch()
      }
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const data = overviewData?.data
  const hasData = data?.hasData

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-800/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                Data Analyst
              </h1>
              <p className="text-slate-400 text-sm">Multi-Channel Analytics Dashboard</p>
            </div>
            <button 
              onClick={() => refetch()}
              className="p-2 rounded-lg bg-slate-700 hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Analysis Form */}
        <div className="bg-slate-800/50 rounded-2xl p-6 mb-8 border border-slate-700">
          <div className="flex gap-4">
            <input
              type="url"
              placeholder="Enter website URL (e.g., https://example.com)"
              value={siteUrl}
              onChange={(e) => setSiteUrl(e.target.value)}
              className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-600 
                       focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 
                       outline-none transition-all"
            />
            <button
              onClick={runAnalysis}
              disabled={!siteUrl || isAnalyzing}
              className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 
                       disabled:cursor-not-allowed rounded-xl font-semibold transition-colors
                       flex items-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <TrendingUp className="w-5 h-5" />
                  Analyze
                </>
              )}
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-12 h-12 animate-spin text-emerald-500" />
          </div>
        ) : !hasData ? (
          <div className="text-center py-20">
            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-slate-800 flex items-center justify-center">
              <Search className="w-12 h-12 text-slate-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-300 mb-2">No Data Yet</h2>
            <p className="text-slate-500">Enter a website URL above to start analysis</p>
          </div>
        ) : (
          <>
            {/* Score Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <ScoreCard 
                title="Overall Score"
                value={data?.overallScore}
                icon={TrendingUp}
                color="emerald"
              />
              <ScoreCard 
                title="Search Clicks"
                value={data?.searchClicks}
                icon={Search}
                color="blue"
              />
              <ScoreCard 
                title="Web Sessions"
                value={data?.webSessions}
                icon={Globe}
                color="purple"
              />
              <ScoreCard 
                title="Social Impressions"
                value={data?.socialImpressions}
                icon={Share2}
                color="amber"
              />
            </div>

            {/* Channel Performance */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Search Performance */}
              <ChannelCard 
                title="Search Performance"
                data={data?.channels?.search}
                icon={Search}
                metrics={[
                  { label: 'Clicks', key: 'total_clicks' },
                  { label: 'Impressions', key: 'total_impressions' },
                  { label: 'Avg CTR', key: 'average_ctr', format: 'percent' },
                  { label: 'Avg Position', key: 'average_position' }
                ]}
              />
              
              {/* Web Analytics */}
              <ChannelCard 
                title="Web Analytics"
                data={data?.channels?.web}
                icon={Globe}
                metrics={[
                  { label: 'Sessions', key: 'total_sessions' },
                  { label: 'Users', key: 'total_users' },
                  { label: 'Bounce Rate', key: 'bounce_rate', format: 'percent' },
                  { label: 'Conversions', key: 'conversions' }
                ]}
              />
            </div>

            {/* Scores Chart */}
            <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700">
              <h3 className="text-lg font-semibold mb-6">Performance Scores</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={[
                      { name: 'Search', score: data?.scores?.search_visibility },
                      { name: 'Web', score: data?.scores?.ga4_performance },
                      { name: 'Social', score: data?.scores?.meta_performance },
                      { name: 'Technical', score: data?.scores?.technical_health },
                      { name: 'Content', score: data?.scores?.content_performance },
                    ]}
                    layout="vertical"
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis type="number" domain={[0, 100]} stroke="#94A3B8" />
                    <YAxis type="category" dataKey="name" stroke="#94A3B8" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1E293B', 
                        border: '1px solid #334155',
                        borderRadius: '8px'
                      }}
                    />
                    <Bar dataKey="score" fill="#10B981" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

function ScoreCard({ title, value, icon: Icon, color }) {
  const colorClasses = {
    emerald: 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30',
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30',
    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30',
    amber: 'from-amber-500/20 to-amber-600/10 border-amber-500/30'
  }
  
  const iconColors = {
    emerald: 'text-emerald-400',
    blue: 'text-blue-400',
    purple: 'text-purple-400',
    amber: 'text-amber-400'
  }

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} rounded-2xl p-6 border`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-slate-400 text-sm">{title}</span>
        <Icon className={`w-5 h-5 ${iconColors[color]}`} />
      </div>
      <div className="text-3xl font-bold">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
    </div>
  )
}

function ChannelCard({ title, data, icon: Icon, metrics }) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700">
        <div className="flex items-center gap-3 mb-4">
          <Icon className="w-5 h-5 text-slate-400" />
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
        <p className="text-slate-500 text-center py-8">No data available</p>
      </div>
    )
  }

  const formatValue = (value, format) => {
    if (value === undefined || value === null) return '-'
    if (format === 'percent') return `${(value * 100).toFixed(2)}%`
    if (typeof value === 'number') return value.toLocaleString()
    return value
  }

  return (
    <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700">
      <div className="flex items-center gap-3 mb-6">
        <Icon className="w-5 h-5 text-emerald-400" />
        <h3 className="text-lg font-semibold">{title}</h3>
      </div>
      <div className="space-y-4">
        {metrics.map((metric) => (
          <div key={metric.key} className="flex justify-between items-center py-2 border-b border-slate-700/50">
            <span className="text-slate-400">{metric.label}</span>
            <span className="font-semibold text-lg">
              {formatValue(data[metric.key], metric.format)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  )
}
