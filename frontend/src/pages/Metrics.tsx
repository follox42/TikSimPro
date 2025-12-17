import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, TrendingUp, Eye, Heart, MessageSquare, Trophy } from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { metricsApi, videosApi } from '../api/client'

type Platform = 'all' | 'tiktok' | 'youtube'

export default function Metrics() {
  const [platform, setPlatform] = useState<Platform>('all')
  const [days, setDays] = useState(7)

  const { data: summary } = useQuery({
    queryKey: ['metrics-summary'],
    queryFn: () => metricsApi.summary().then(r => r.data),
  })

  const { data: timeline } = useQuery({
    queryKey: ['metrics-timeline', days],
    queryFn: () => metricsApi.timeline(days).then(r => r.data),
  })

  const { data: tiktokMetrics } = useQuery({
    queryKey: ['metrics-tiktok', days],
    queryFn: () => metricsApi.tiktok(days).then(r => r.data),
    enabled: platform === 'all' || platform === 'tiktok',
  })

  const { data: youtubeMetrics } = useQuery({
    queryKey: ['metrics-youtube', days],
    queryFn: () => metricsApi.youtube(days).then(r => r.data),
    enabled: platform === 'all' || platform === 'youtube',
  })

  const { data: bestPerformers } = useQuery({
    queryKey: ['best-performers'],
    queryFn: () => metricsApi.bestPerformers(5).then(r => r.data),
  })

  const { data: videoStats } = useQuery({
    queryKey: ['video-stats'],
    queryFn: () => videosApi.getStats().then(r => r.data),
  })

  const COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']

  const platformData = [
    { name: 'TikTok', value: tiktokMetrics?.total_videos || 0, color: '#000000' },
    { name: 'YouTube', value: youtubeMetrics?.total_videos || 0, color: '#ff0000' },
  ].filter(p => p.value > 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Metrics</h1>
          <p className="text-muted-foreground">
            Platform performance analytics
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value as Platform)}
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
          >
            <option value="all">All Platforms</option>
            <option value="tiktok">TikTok</option>
            <option value="youtube">YouTube</option>
          </select>

          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex items-center gap-3">
            <Eye className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-2xl font-bold">
                {summary?.total_views?.toLocaleString() || '0'}
              </p>
              <p className="text-sm text-muted-foreground">Total Views</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex items-center gap-3">
            <Heart className="h-8 w-8 text-red-500" />
            <div>
              <p className="text-2xl font-bold">
                {summary?.total_likes?.toLocaleString() || '0'}
              </p>
              <p className="text-sm text-muted-foreground">Total Likes</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex items-center gap-3">
            <MessageSquare className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-2xl font-bold">
                {summary?.total_comments?.toLocaleString() || '0'}
              </p>
              <p className="text-sm text-muted-foreground">Total Comments</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-purple-500" />
            <div>
              <p className="text-2xl font-bold">
                {((summary?.average_engagement_rate || 0) * 100).toFixed(2)}%
              </p>
              <p className="text-sm text-muted-foreground">Avg Engagement</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Views Timeline */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">Views Over Time</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeline?.timeline || []}>
                <XAxis
                  dataKey="date"
                  stroke="#888888"
                  fontSize={12}
                  tickFormatter={(value) => value.split('-').slice(1).join('/')}
                />
                <YAxis stroke="#888888" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="views"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Engagement Timeline */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">Engagement Over Time</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={timeline?.timeline || []}>
                <XAxis
                  dataKey="date"
                  stroke="#888888"
                  fontSize={12}
                  tickFormatter={(value) => value.split('-').slice(1).join('/')}
                />
                <YAxis stroke="#888888" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="likes" fill="#ef4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="comments" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Platform Distribution & Best Performers */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Platform Distribution */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">Platform Distribution</h2>
          <div className="h-64">
            {platformData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={platformData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {platformData.map((entry, index) => (
                      <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                No platform data yet
              </div>
            )}
          </div>
          <div className="mt-4 flex justify-center gap-6">
            {platformData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-2">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-sm">{entry.name}: {entry.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Best Performers */}
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="mb-4 flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-500" />
            <h2 className="text-lg font-semibold">Top Performers</h2>
          </div>
          <div className="space-y-3">
            {(bestPerformers?.best_performers || []).map((video: any, index: number) => (
              <div
                key={video.id}
                className="flex items-center justify-between rounded-lg bg-muted/50 p-3"
              >
                <div className="flex items-center gap-3">
                  <span className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
                    index === 0 ? 'bg-yellow-500 text-yellow-950' :
                    index === 1 ? 'bg-gray-300 text-gray-800' :
                    index === 2 ? 'bg-amber-600 text-amber-950' :
                    'bg-muted text-muted-foreground'
                  }`}>
                    {index + 1}
                  </span>
                  <div>
                    <p className="font-medium">{video.generator_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {video.platform || 'Local'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium">{video.views?.toLocaleString() || 0} views</p>
                  <p className="text-xs text-muted-foreground">
                    {((video.engagement_rate || 0) * 100).toFixed(1)}% eng.
                  </p>
                </div>
              </div>
            ))}
            {(!bestPerformers?.best_performers || bestPerformers.best_performers.length === 0) && (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No performance data yet
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Platform Specific Stats */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* TikTok Stats */}
        {(platform === 'all' || platform === 'tiktok') && (
          <div className="rounded-lg border border-border bg-card p-6">
            <div className="mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              <h2 className="text-lg font-semibold">TikTok Stats</h2>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-2xl font-bold">
                  {tiktokMetrics?.total_videos || 0}
                </p>
                <p className="text-sm text-muted-foreground">Videos</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-2xl font-bold">
                  {tiktokMetrics?.total_views?.toLocaleString() || '0'}
                </p>
                <p className="text-sm text-muted-foreground">Views</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-2xl font-bold">
                  {tiktokMetrics?.total_likes?.toLocaleString() || '0'}
                </p>
                <p className="text-sm text-muted-foreground">Likes</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-2xl font-bold">
                  {((tiktokMetrics?.avg_engagement || 0) * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-muted-foreground">Avg Engagement</p>
              </div>
            </div>
          </div>
        )}

        {/* YouTube Stats */}
        {(platform === 'all' || platform === 'youtube') && (
          <div className="rounded-lg border border-border bg-card p-6">
            <div className="mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-red-500" />
              <h2 className="text-lg font-semibold">YouTube Stats</h2>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-2xl font-bold">
                  {youtubeMetrics?.total_videos || 0}
                </p>
                <p className="text-sm text-muted-foreground">Videos</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-2xl font-bold">
                  {youtubeMetrics?.total_views?.toLocaleString() || '0'}
                </p>
                <p className="text-sm text-muted-foreground">Views</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-2xl font-bold">
                  {youtubeMetrics?.total_likes?.toLocaleString() || '0'}
                </p>
                <p className="text-sm text-muted-foreground">Likes</p>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-2xl font-bold">
                  {((youtubeMetrics?.avg_engagement || 0) * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-muted-foreground">Avg Engagement</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Generator Performance */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold">Performance by Generator</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {videoStats?.by_generator && Object.entries(videoStats.by_generator).map(([gen, count]) => (
            <div
              key={gen}
              className="flex items-center justify-between rounded-lg bg-muted/50 p-4"
            >
              <div>
                <p className="font-medium">{gen}</p>
                <p className="text-sm text-muted-foreground">{count as number} videos</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center">
                <span className="text-lg font-bold text-primary">{count as number}</span>
              </div>
            </div>
          ))}
          {!videoStats?.by_generator && (
            <p className="col-span-full py-8 text-center text-sm text-muted-foreground">
              No generator data yet
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
