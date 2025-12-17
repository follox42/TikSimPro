import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Play, Trash2, ExternalLink, Filter } from 'lucide-react'
import { videosApi, type Video } from '../api/client'

export default function Videos() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<string>('')
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null)

  const { data: videos, isLoading } = useQuery({
    queryKey: ['videos', filter],
    queryFn: () => videosApi.list({
      limit: 50,
      generator: filter || undefined,
    }).then(r => r.data),
  })

  const { data: stats } = useQuery({
    queryKey: ['video-stats'],
    queryFn: () => videosApi.getStats().then(r => r.data),
  })

  const deleteVideo = useMutation({
    mutationFn: (id: number) => videosApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      setSelectedVideo(null)
    },
  })

  const generators = stats?.by_generator ? Object.keys(stats.by_generator) : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Videos</h1>
          <p className="text-muted-foreground">
            {videos?.length || 0} videos generated
          </p>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
          >
            <option value="">All Generators</option>
            {generators.map((gen) => (
              <option key={gen} value={gen}>{gen}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Video Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {isLoading ? (
          // Loading skeletons
          Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-lg border border-border bg-card">
              <div className="aspect-[9/16] bg-muted" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-3 bg-muted rounded w-1/2" />
              </div>
            </div>
          ))
        ) : videos?.map((video) => (
          <div
            key={video.id}
            onClick={() => setSelectedVideo(video)}
            className="cursor-pointer rounded-lg border border-border bg-card transition-all hover:border-primary"
          >
            {/* Thumbnail */}
            <div className="relative aspect-[9/16] overflow-hidden rounded-t-lg bg-muted">
              {video.video_path ? (
                <video
                  src={`/videos/${video.video_path.split('/').pop()}`}
                  className="h-full w-full object-cover"
                  muted
                  onMouseEnter={(e) => e.currentTarget.play()}
                  onMouseLeave={(e) => {
                    e.currentTarget.pause()
                    e.currentTarget.currentTime = 0
                  }}
                />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <Play className="h-12 w-12 text-muted-foreground" />
                </div>
              )}

              {/* Platform Badge */}
              {video.platform && (
                <span className="absolute right-2 top-2 rounded-full bg-primary px-2 py-1 text-xs font-medium text-primary-foreground">
                  {video.platform}
                </span>
              )}
            </div>

            {/* Info */}
            <div className="p-4">
              <p className="font-medium truncate">{video.generator_name}</p>
              <p className="text-sm text-muted-foreground">
                {video.audio_mode || 'No audio'}
              </p>
              <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                <span>Score: {video.validation_score?.toFixed(2) || 'N/A'}</span>
                <span>{new Date(video.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {videos?.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Play className="h-12 w-12 text-muted-foreground" />
          <p className="mt-4 text-lg font-medium">No videos yet</p>
          <p className="text-sm text-muted-foreground">
            Start the pipeline to generate your first video
          </p>
        </div>
      )}

      {/* Video Detail Modal */}
      {selectedVideo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="mx-4 w-full max-w-2xl rounded-lg bg-card p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-bold">{selectedVideo.generator_name}</h2>
                <p className="text-sm text-muted-foreground">
                  Video #{selectedVideo.id}
                </p>
              </div>
              <button
                onClick={() => setSelectedVideo(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                ×
              </button>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {/* Video Preview */}
              <div className="aspect-[9/16] overflow-hidden rounded-lg bg-muted">
                {selectedVideo.video_path ? (
                  <video
                    src={`/videos/${selectedVideo.video_path.split('/').pop()}`}
                    controls
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <Play className="h-12 w-12 text-muted-foreground" />
                  </div>
                )}
              </div>

              {/* Details */}
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Audio Mode</p>
                  <p>{selectedVideo.audio_mode || 'None'}</p>
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground">Validation Score</p>
                  <p>{selectedVideo.validation_score?.toFixed(2) || 'N/A'}</p>
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground">Platform</p>
                  <p>{selectedVideo.platform || 'Local only'}</p>
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground">Created</p>
                  <p>{new Date(selectedVideo.created_at).toLocaleString()}</p>
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground">Parameters</p>
                  <pre className="mt-1 overflow-auto rounded bg-muted p-2 text-xs">
                    {JSON.stringify(selectedVideo.generator_params, null, 2)}
                  </pre>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-4">
                  {selectedVideo.platform_video_id && (
                    <a
                      href={`https://${selectedVideo.platform}.com/video/${selectedVideo.platform_video_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
                    >
                      <ExternalLink className="h-4 w-4" />
                      View on {selectedVideo.platform}
                    </a>
                  )}
                  <button
                    onClick={() => deleteVideo.mutate(selectedVideo.id)}
                    disabled={deleteVideo.isPending}
                    className="flex items-center gap-2 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
