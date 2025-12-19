import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mailApi, CreateAlias } from '../api/client';

// Query keys
export const mailKeys = {
  all: ['mail'] as const,
  aliases: () => [...mailKeys.all, 'aliases'] as const,
  emails: (filters?: { alias?: string; unread_only?: boolean; starred_only?: boolean }) =>
    [...mailKeys.all, 'emails', filters] as const,
  email: (id: number) => [...mailKeys.all, 'email', id] as const,
  stats: () => [...mailKeys.all, 'stats'] as const,
};

// Aliases
export function useAliases() {
  return useQuery({
    queryKey: mailKeys.aliases(),
    queryFn: () => mailApi.listAliases(),
  });
}

export function useCreateAlias() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAlias) => mailApi.createAlias(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mailKeys.aliases() });
      queryClient.invalidateQueries({ queryKey: mailKeys.stats() });
    },
  });
}

export function useDeleteAlias() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => mailApi.deleteAlias(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mailKeys.aliases() });
      queryClient.invalidateQueries({ queryKey: mailKeys.stats() });
    },
  });
}

// Emails
export function useEmails(filters?: { alias?: string; unread_only?: boolean; starred_only?: boolean }) {
  return useQuery({
    queryKey: mailKeys.emails(filters),
    queryFn: () => mailApi.listEmails(filters),
  });
}

export function useEmail(id: number, enabled: boolean = true) {
  return useQuery({
    queryKey: mailKeys.email(id),
    queryFn: () => mailApi.getEmail(id),
    enabled,
  });
}

export function useToggleStar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => mailApi.toggleStar(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mailKeys.all });
    },
  });
}

export function useMarkRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, is_read }: { id: number; is_read: boolean }) =>
      mailApi.markRead(id, is_read),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mailKeys.all });
    },
  });
}

export function useDeleteEmail() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => mailApi.deleteEmail(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mailKeys.all });
    },
  });
}

// Stats
export function useMailStats() {
  return useQuery({
    queryKey: mailKeys.stats(),
    queryFn: () => mailApi.getStats(),
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alias?: string) => mailApi.markAllRead(alias),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mailKeys.all });
    },
  });
}
