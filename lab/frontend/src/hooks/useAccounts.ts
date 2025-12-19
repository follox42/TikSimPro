import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountsApi, authApi, Platform, AccountStatus, CreateAccount } from '../api/client';

// Query keys
export const accountKeys = {
  all: ['accounts'] as const,
  lists: () => [...accountKeys.all, 'list'] as const,
  list: (filters: { platform?: Platform; status?: AccountStatus }) =>
    [...accountKeys.lists(), filters] as const,
  detail: (id: number) => [...accountKeys.all, 'detail', id] as const,
  loginStatus: (id: number) => [...accountKeys.all, 'loginStatus', id] as const,
};

// List accounts
export function useAccounts(filters?: { platform?: Platform; status?: AccountStatus }) {
  return useQuery({
    queryKey: accountKeys.list(filters || {}),
    queryFn: () => accountsApi.list(filters),
  });
}

// Create account
export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAccount) => accountsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
    },
  });
}

// Delete account
export function useDeleteAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => accountsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
    },
  });
}

// Check status
export function useCheckStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => accountsApi.checkStatus(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
    },
  });
}

// Start login
export function useStartLogin() {
  return useMutation({
    mutationFn: (accountId: number) => authApi.startLogin(accountId),
  });
}

// Login status polling
export function useLoginStatus(accountId: number, enabled: boolean = false) {
  return useQuery({
    queryKey: accountKeys.loginStatus(accountId),
    queryFn: () => authApi.getLoginStatus(accountId),
    enabled,
    refetchInterval: enabled ? 2000 : false,
  });
}

// Cancel login
export function useCancelLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (accountId: number) => authApi.cancelLogin(accountId),
    onSuccess: (_, accountId) => {
      queryClient.invalidateQueries({ queryKey: accountKeys.loginStatus(accountId) });
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
    },
  });
}

// Validate cookies
export function useValidateCookies() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (accountId: number) => authApi.validateCookies(accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
    },
  });
}

// Delete cookies
export function useDeleteCookies() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (accountId: number) => authApi.deleteCookies(accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
    },
  });
}
