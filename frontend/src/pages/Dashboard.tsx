import { useQuery } from '@tanstack/react-query'
import { Video, Eye, Heart, TrendingUp, Play } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { videosApi, metricsApi, pipelineApi } from '../api/client'

export default function Dashboard() {
  const { data: pipelineStatus } = useQuery({
    queryKey: ['pipeline-status'],
    queryFn: () => pipelineApi.status().then(r => r.data),
  })

  const { data: videoStats } = useQuery({
    queryKey: ['video-stats'],
    queryFn: () => videosApi.getStats().then(r => r.data),
  })

  const { data: metricsSummary } = useQuery({
    queryKey: ['metrics-summary'],
    queryFn: () => metricsApi.summary().then(r => r.data),
  })

  const { data: timeline } = useQuery({
    queryKey: ['metrics-timeline'],
    queryFn: () => metricsApi.timeline(7).then(r => r.data),
  })

  const { data: recentVideos } = useQuery({
    queryKey: ['recent-videos'],
    queryFn: () => videosApi.list({ limit: 5 }).then(r => r.data),
  })

  const stats = [
    {
      label: 'Total Videos',
      value: pipelineStatus?.total_videos || 0,
      icon: Video,
      color: 'text-blue-500',
    },
    {
      label: 'Total Views',
      value: metricsSummary?.total_views?.toLocaleString() || '0',
      icon: Eye,
      color: 'text-green-500',
    },
    {
      label: 'Total Likes',
      value: metricsSummary?.total_likes?.toLocaleString() || '0',
      icon: Heart,
      color: 'text-red-500',
    },
    {
      label: 'Avg Engagement',
      value: `${((metricsSummary?.average_engagement_rate || 0) * 100).toFixed(2)}%`,
      icon: TrendingUp,
      color: 'text-purple-500',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your TikSimPro performance</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-lg border border-border bg-card p-6">
            <div className="flex items-center justify-between">
              <stat.icon className={`h-8 w-8 ${stat.color}`} />
              <span className={`h-2 w-2 rounded-full ${
                pipelineStatus?.running ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
              }`} />
            </div>
            <div className="mt-4">
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </div>
          </div>
        ))}
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
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="views"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Performance by Generator */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">By Generator</h2>
          <div className="space-y-4">
            {videoStats?.by_generator && Object.entries(videoStats.by_generator).map(([gen, count]) => (
              <div key={gen} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-3 w-3 rounded-full bg-primary" />
                  <span className="text-sm">{gen}</span>
                </div>
                <span className="text-sm font-medium">{count as number} videos</span>
              </div>
            ))}
            {!videoStats?.by_generator && (
              <p className="text-sm text-muted-foreground">No data yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent Videos */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold">Recent Videos</h2>
        <div className="space-y-3">
          {recentVideos?.map((video) => (
            <div
              key={video.id}
              className="flex items-center justify-between rounded-lg bg-muted/50 p-4"
            >
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Play className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-medium">{video.generator_name}</p>
                  <p className="text-sm text-muted-foreground">
                    {video.audio_mode || 'No audio'} • {video.platform || 'Local'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium">
                  Score: {video.validation_score?.toFixed(2) || 'N/A'}
                </p>
                <p className="text-xs text-muted-foreground">
                  {new Date(video.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
          {(!recentVideos || recentVideos.length === 0) && (
            <p className="text-center text-sm text-muted-foreground py-8">
              No videos generated yet
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
