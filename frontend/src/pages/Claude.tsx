import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Send,
  Bot,
  User,
  Loader2,
  Sparkles,
  Play,
  Pause,
  Video,
  BarChart3,
  Trash2,
  RefreshCw,
} from 'lucide-react'
import { claudeApi, pipelineApi, type Conversation } from '../api/client'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  actions?: unknown[]
  timestamp: Date
}

export default function Claude() {
  const queryClient = useQueryClient()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['claude-history'],
    queryFn: () => claudeApi.history(50).then(r => r.data),
  })

  const { data: pipelineStatus } = useQuery({
    queryKey: ['pipeline-status'],
    queryFn: () => pipelineApi.status().then(r => r.data),
  })

  const { data: suggestions } = useQuery({
    queryKey: ['claude-suggestions'],
    queryFn: () => claudeApi.suggestions().then(r => r.data),
  })

  const { data: context } = useQuery({
    queryKey: ['claude-context'],
    queryFn: () => claudeApi.context().then(r => r.data),
  })

  const chatMutation = useMutation({
    mutationFn: (message: string) => claudeApi.chat(message).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claude-history'] })
      queryClient.invalidateQueries({ queryKey: ['pipeline-status'] })
      setInput('')
    },
    onError: (error) => {
      console.error('Chat error:', error)
      alert('Erreur: ' + (error instanceof Error ? error.message : 'Unknown error'))
    },
  })

  const clearHistory = useMutation({
    mutationFn: () => claudeApi.clearHistory(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claude-history'] })
    },
  })

  // Convert history to messages (reverse to show oldest first)
  const messages: Message[] = [...(history || [])].reverse().flatMap((conv: Conversation) => [
    {
      id: conv.id * 2,
      role: 'user' as const,
      content: conv.user_message,
      timestamp: new Date(conv.created_at),
    },
    {
      id: conv.id * 2 + 1,
      role: 'assistant' as const,
      content: conv.assistant_message,
      actions: conv.actions_taken,
      timestamp: new Date(conv.created_at),
    },
  ])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Form submitted, input:', input)
    if (!input.trim() || chatMutation.isPending) {
      console.log('Blocked: empty input or pending')
      return
    }
    console.log('Sending message:', input.trim())
    chatMutation.mutate(input.trim())
  }

  const quickActions = [
    { label: 'Start Loop', icon: Play, action: 'Start the video generation loop' },
    { label: 'Stop Loop', icon: Pause, action: 'Stop the video generation loop' },
    { label: 'Generate One', icon: Video, action: 'Generate one video right now' },
    { label: 'Analyze', icon: BarChart3, action: 'Analyze the performance of recent videos and suggest improvements' },
  ]

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-6">
      {/* Chat Area */}
      <div className="flex flex-1 flex-col rounded-lg border border-border bg-card">
        {/* Chat Header */}
        <div className="flex items-center justify-between border-b border-border p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary">
              <Bot className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h2 className="font-semibold">Claude Assistant</h2>
              <p className="text-xs text-muted-foreground">
                System-aware AI with full context
              </p>
            </div>
          </div>
          <button
            onClick={() => clearHistory.mutate()}
            disabled={clearHistory.isPending}
            className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
            title="Clear history"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {historyLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Bot className="h-16 w-16 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-medium">Welcome to Claude Assistant</h3>
              <p className="mt-2 max-w-md text-sm text-muted-foreground">
                I have full awareness of the TikSimPro system. I can analyze performance,
                control the generation loop, suggest improvements, and help you understand
                what's happening.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {quickActions.map((action) => (
                  <button
                    key={action.label}
                    onClick={() => setInput(action.action)}
                    className="flex items-center gap-2 rounded-full bg-muted px-4 py-2 text-sm hover:bg-muted/80"
                  >
                    <action.icon className="h-4 w-4" />
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
                    <Bot className="h-4 w-4 text-primary-foreground" />
                  </div>
                )}
                <div
                  className={`max-w-[70%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-foreground'
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm text-inherit">{message.content}</p>
                  {message.actions && Array.isArray(message.actions) && message.actions.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {message.actions.map((actionItem: any, i) => {
                        let label = 'action';
                        try {
                          if (typeof actionItem === 'string') {
                            label = actionItem;
                          } else if (actionItem?.action?.action) {
                            label = String(actionItem.action.action);
                          } else if (typeof actionItem?.action === 'string') {
                            label = actionItem.action;
                          }
                        } catch {
                          label = 'action';
                        }
                        const isSuccess = actionItem?.result?.success === true;
                        return (
                          <span
                            key={i}
                            className={`rounded px-2 py-0.5 text-xs ${isSuccess ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}
                          >
                            {label}
                          </span>
                        );
                      })}
                    </div>
                  )}
                  <p className="mt-1 text-xs opacity-50">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
                {message.role === 'user' && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <User className="h-4 w-4 text-foreground" />
                  </div>
                )}
              </div>
            ))
          )}
          {chatMutation.isPending && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
                <Bot className="h-4 w-4 text-primary-foreground" />
              </div>
              <div className="rounded-lg bg-muted px-4 py-3 text-foreground">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="border-t border-border p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Claude about the system..."
              className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
              disabled={chatMutation.isPending}
            />
            <button
              type="submit"
              disabled={!input.trim() || chatMutation.isPending}
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {chatMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              Send
            </button>
          </div>
        </form>
      </div>

      {/* Sidebar */}
      <div className="w-80 space-y-4">
        {/* System Status */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="font-semibold">System Status</h3>
          <div className="mt-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Pipeline</span>
              <span className={`flex items-center gap-1 text-sm ${
                pipelineStatus?.running ? 'text-green-500' : 'text-muted-foreground'
              }`}>
                <span className={`h-2 w-2 rounded-full ${
                  pipelineStatus?.running ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
                }`} />
                {pipelineStatus?.running ? 'Running' : 'Stopped'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Videos Today</span>
              <span className="text-sm font-medium">{pipelineStatus?.videos_today || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total Videos</span>
              <span className="text-sm font-medium">{pipelineStatus?.total_videos || 0}</span>
            </div>
            {pipelineStatus?.last_error && (
              <div className="mt-2 rounded bg-destructive/10 p-2">
                <p className="text-xs text-destructive">{pipelineStatus.last_error}</p>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="font-semibold">Quick Actions</h3>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {quickActions.map((action) => (
              <button
                key={action.label}
                onClick={() => {
                  setInput(action.action)
                }}
                className="flex flex-col items-center gap-1 rounded-lg bg-muted p-3 text-sm hover:bg-muted/80"
              >
                <action.icon className="h-5 w-5" />
                <span className="text-xs">{action.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Suggestions */}
        {suggestions && suggestions.length > 0 && (
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-yellow-500" />
              <h3 className="font-semibold">Suggestions</h3>
            </div>
            <div className="mt-3 space-y-2">
              {suggestions.slice(0, 3).map((suggestion: string, i: number) => (
                <button
                  key={i}
                  onClick={() => setInput(suggestion)}
                  className="w-full rounded-lg bg-muted p-2 text-left text-xs hover:bg-muted/80"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Context Info */}
        {context && (
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Context</h3>
              <button
                onClick={() => queryClient.invalidateQueries({ queryKey: ['claude-context'] })}
                className="rounded p-1 hover:bg-muted"
              >
                <RefreshCw className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
            <div className="mt-3 space-y-2 text-xs text-muted-foreground">
              <p>Conversations: {context.total_conversations || 0}</p>
              <p>System awareness: Full</p>
              <p>Memory: Persistent</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
