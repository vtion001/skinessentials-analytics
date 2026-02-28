/**
 * Tambo Generative UI Components
 * 
 * This file demonstrates how to use Tambo for generative UI.
 * The AI decides which component to render based on user messages.
 * 
 * To use this:
 * 1. npm install @anthropic-ai/sdk tambo
 * 2. Configure your Anthropic API key
 * 3. Replace App.jsx with GenerativeApp.jsx
 */

import { useState, useEffect } from 'react'
import { 
  TamboProvider, 
  useAgent, 
  useThread,
  useComponents 
} from 'tambo'
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts'

// ==================== CUSTOM COMPONENTS ====================

/**
 * ScoreCard Component
 * Displays a metric with icon and value
 */
const ScoreCard = ({ title, value, change, trend, color = 'emerald' }) => {
  const colorMap = {
    emerald: 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30 text-emerald-400',
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30 text-blue-400',
    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30 text-purple-400',
    amber: 'from-amber-500/20 to-amber-600/10 border-amber-500/30 text-amber-400'
  }

  return (
    <div className={`bg-gradient-to-br ${colorMap[color].split(' ')[0]} ${colorMap[color].split(' ')[1]} 
                    rounded-2xl p-6 border ${colorMap[color].split(' ')[2]}`}>
      <div className="text-slate-400 text-sm mb-2">{title}</div>
      <div className="text-3xl font-bold">{value}</div>
      {change && (
        <div className={`text-sm mt-2 ${trend === 'up' ? 'text-emerald-400' : 'text-red-400'}`}>
          {trend === 'up' ? '↑' : '↓'} {Math.abs(change)}%
        </div>
      )}
    </div>
  )
}

/**
 * DataTable Component
 * Displays tabular data
 */
const DataTable = ({ data, columns }) => {
  if (!data || data.length === 0) return null

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-600">
            {columns.map((col) => (
              <th key={col.key} className="text-left py-3 px-4 text-slate-400 font-medium">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 10).map((row, idx) => (
            <tr key={idx} className="border-b border-slate-700/50 hover:bg-slate-700/30">
              {columns.map((col) => (
                <td key={col.key} className="py-3 px-4">
                  {col.format ? col.format(row[col.key]) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/**
 * ChartComponent Component
 * Generic chart wrapper
 */
const ChartComponent = ({ type, data, config }) => {
  const colors = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444']

  if (type === 'bar') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="name" stroke="#94A3B8" />
          <YAxis stroke="#94A3B8" />
          <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '8px' }} />
          <Bar dataKey="value" fill="#10B981" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  if (type === 'pie') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            label
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '8px' }} />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  // Default to line chart
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="name" stroke="#94A3B8" />
        <YAxis stroke="#94A3B8" />
        <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '8px' }} />
        <Line type="monotone" dataKey="value" stroke="#10B981" strokeWidth={2} dot={{ fill: '#10B981' }} />
      </LineChart>
    </ResponsiveContainer>
  )
}

/**
 * RecommendationCard Component
 * Displays an action item
 */
const RecommendationCard = ({ priority, title, description, action }) => {
  const priorityColors = {
    High: 'border-l-red-500 bg-red-500/10',
    Medium: 'border-l-amber-500 bg-amber-500/10',
    Low: 'border-l-blue-500 bg-blue-500/10',
    Growth: 'border-l-emerald-500 bg-emerald-500/10'
  }

  return (
    <div className={`border-l-4 ${priorityColors[priority] || priorityColors.Low} p-4 rounded-r-lg`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold uppercase tracking-wider">{priority}</span>
      </div>
      <h4 className="font-semibold mb-2">{title}</h4>
      <p className="text-slate-400 text-sm mb-3">{description}</p>
      <div className="text-emerald-400 text-sm">
        → {action}
      </div>
    </div>
  )
}

// ==================== GENERATIVE UI APP ====================

/**
 * GenerativeApp - Main Application with Tambo
 * 
 * This version uses Tambo's AI to dynamically generate
 * the right UI components based on user queries.
 */
export function GenerativeApp({ apiUrl = 'http://localhost:8000' }) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: 'Hi! I can help you analyze your website data. Ask me about your search traffic, web analytics, social performance, or specific metrics.' 
    }
  ])
  const [data, setData] = useState(null)

  // Fetch data on mount
  useEffect(() => {
    fetch(`${apiUrl}/api/ui/overview`)
      .then(res => res.json())
      .then(result => {
        if (result.success) {
          setData(result.data)
        }
      })
      .catch(console.error)
  }, [apiUrl])

  // Handle user message
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = input
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    // Simple keyword-based response (in production, use Claude API)
    let response = generateResponse(userMessage, data)
    
    setMessages(prev => [...prev, { role: 'assistant', content: response }])
  }

  // Keyword-based response generator
  const generateResponse = (query, data) => {
    const q = query.toLowerCase()
    
    if (!data?.hasData) {
      return "I don't have any data yet. Please run an analysis first using the /api/analyze endpoint."
    }

    if (q.includes('search') || q.includes('gsc') || q.includes('clicks')) {
      return `Your search performance shows ${data.searchClicks.toLocaleString()} clicks. `
        + `Your overall score is ${data.overallScore}/100. `
        + `Would you like me to show you a detailed breakdown?`
    }

    if (q.includes('web') || q.includes('ga4') || q.includes('session')) {
      return `Web analytics shows ${data.webSessions.toLocaleString()} sessions. `
        + `Bounce rate is ${(data.bounceRate * 100).toFixed(1)}%. `
        + `Would you like to see the traffic sources?`
    }

    if (q.includes('social') || q.includes('meta') || q.includes('impression')) {
      return `Social media has ${data.socialImpressions.toLocaleString()} impressions. `
        + `Engagement rate is ${(data.engagement * 100).toFixed(1)}%.`
    }

    if (q.includes('score') || q.includes('overall')) {
      return `Your overall performance score is ${data.overallScore}/100. `
        + `Search: ${data.scores.search_visibility}/100, `
        + `Web: ${data.scores.ga4_performance}/100, `
        + `Social: ${data.scores.meta_performance}/100.`
    }

    return `I can show you details about your search traffic, web sessions, social performance, or overall score. What would you like to know?`
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Data Analyst - Generative UI</h1>
        
        {/* Data Overview */}
        {data?.hasData && (
          <div className="grid grid-cols-4 gap-4 mb-8">
            <ScoreCard title="Overall" value={`${data.overallScore}/100`} color="emerald" />
            <ScoreCard title="Search Clicks" value={data.searchClicks.toLocaleString()} color="blue" />
            <ScoreCard title="Sessions" value={data.webSessions.toLocaleString()} color="purple" />
            <ScoreCard title="Impressions" value={data.socialImpressions.toLocaleString()} color="amber" />
          </div>
        )}

        {/* Chat Interface */}
        <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
          <div className="p-4 border-b border-slate-700 bg-slate-800/50">
            <h2 className="font-semibold">Ask about your data</h2>
          </div>
          
          <div className="h-96 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`${msg.role === 'user' ? 'ml-12' : 'mr-12'}`}>
                <div className={`p-4 rounded-2xl ${
                  msg.role === 'user' 
                    ? 'bg-emerald-500/20 border border-emerald-500/30' 
                    : 'bg-slate-700/50 border border-slate-600'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="p-4 border-t border-slate-700">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask: Show me search performance, What's my overall score?, etc."
              className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-xl
                       focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none"
            />
          </form>
        </div>
      </div>
    </div>
  )
}

export { ScoreCard, DataTable, ChartComponent, RecommendationCard }
