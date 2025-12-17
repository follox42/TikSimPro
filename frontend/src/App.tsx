import { Routes, Route, NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Video,
  BarChart3,
  MessageSquare,
  Play,
  Pause
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import Dashboard from './pages/Dashboard'
import Videos from './pages/Videos'
import Metrics from './pages/Metrics'
import Claude from './pages/Claude'
import { api } from './api/client'
import { useWebSocket } from './hooks/useWebSocket'

function App() {
  const queryClient = useQueryClient()

  // WebSocket connection
  const { isConnected } = useWebSocket()

  // Pipeline status
  const { data: pipelineStatus } = useQuery({
    queryKey: ['pipeline-status'],
    queryFn: () => api.get('/api/pipeline/status').then(r => r.data),
    refetchInterval: 10000,
  })

  // Toggle pipeline
  const togglePipeline = useMutation({
    mutationFn: async () => {
      if (pipelineStatus?.running) {
        return api.post('/api/pipeline/stop')
      } else {
        return api.post('/api/pipeline/start')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-status'] })
    },
  })

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/videos', icon: Video, label: 'Videos' },
    { to: '/metrics', icon: BarChart3, label: 'Metrics' },
    { to: '/claude', icon: MessageSquare, label: 'Claude' },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-border bg-card">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center border-b border-border px-6">
            <span className="text-xl font-bold text-primary">TikSimPro</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2 transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`
                }
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* Pipeline Control */}
          <div className="border-t border-border p-4">
            <div className="rounded-lg bg-muted p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Pipeline</span>
                <span className={`h-2 w-2 rounded-full ${
                  pipelineStatus?.running ? 'bg-green-500' : 'bg-gray-500'
                }`} />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {pipelineStatus?.videos_today || 0} videos today
              </p>
              <button
                onClick={() => togglePipeline.mutate()}
                disabled={togglePipeline.isPending}
                className={`mt-3 flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  pipelineStatus?.running
                    ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
                    : 'bg-primary text-primary-foreground hover:bg-primary/90'
                }`}
              >
                {pipelineStatus?.running ? (
                  <>
                    <Pause className="h-4 w-4" />
                    Stop
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Start
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Connection Status */}
          <div className="border-t border-border p-4">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className={`h-2 w-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`} />
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-64 min-h-screen">
        <div className="container mx-auto p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/videos" element={<Videos />} />
            <Route path="/metrics" element={<Metrics />} />
            <Route path="/claude" element={<Claude />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

export default App
