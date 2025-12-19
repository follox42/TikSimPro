import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Account } from '../api/client';
import StatusBadge from './StatusBadge';
import {
  useStartLogin,
  useLoginStatus,
  useCancelLogin,
  useValidateCookies,
  useDeleteAccount,
  useDeleteCookies,
} from '../hooks/useAccounts';

interface AccountCardProps {
  account: Account;
}

export default function AccountCard({ account }: AccountCardProps) {
  const [showLoginStatus, setShowLoginStatus] = useState(false);

  const startLogin = useStartLogin();
  const cancelLogin = useCancelLogin();
  const validateCookies = useValidateCookies();
  const deleteAccount = useDeleteAccount();
  const deleteCookies = useDeleteCookies();

  const { data: loginStatus } = useLoginStatus(account.id, showLoginStatus);

  const handleStartLogin = async () => {
    try {
      await startLogin.mutateAsync(account.id);
      setShowLoginStatus(true);
      Alert.alert(
        'Login Started',
        'Complete the login in the browser window on your server.',
        [{ text: 'OK' }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to start login');
    }
  };

  const handleCancelLogin = async () => {
    try {
      await cancelLogin.mutateAsync(account.id);
      setShowLoginStatus(false);
    } catch (error) {
      Alert.alert('Error', 'Failed to cancel login');
    }
  };

  const handleValidate = async () => {
    try {
      const result = await validateCookies.mutateAsync(account.id);
      Alert.alert(
        'Validation Result',
        result.status === 'active' ? 'Cookies are valid!' : 'Cookies expired or invalid'
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to validate cookies');
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Account',
      `Are you sure you want to delete ${account.username}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteAccount.mutateAsync(account.id);
            } catch (error) {
              Alert.alert('Error', 'Failed to delete account');
            }
          },
        },
      ]
    );
  };

  const handleDeleteCookies = () => {
    Alert.alert(
      'Delete Cookies',
      'Are you sure you want to delete all cookies for this account?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteCookies.mutateAsync(account.id);
            } catch (error) {
              Alert.alert('Error', 'Failed to delete cookies');
            }
          },
        },
      ]
    );
  };

  const isLoggingIn = loginStatus?.in_progress;
  const platformColor = account.platform === 'tiktok' ? '#ec4899' : '#ef4444';

  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.platformInfo}>
          <View style={[styles.platformIcon, { backgroundColor: platformColor + '30' }]}>
            <Text style={[styles.platformText, { color: platformColor }]}>
              {account.platform === 'tiktok' ? 'TT' : 'YT'}
            </Text>
          </View>
          <View>
            <Text style={styles.username}>{account.username}</Text>
            <Text style={styles.platform}>{account.platform}</Text>
          </View>
        </View>
        <StatusBadge status={account.status} />
      </View>

      {/* Info */}
      {account.email && <Text style={styles.email}>{account.email}</Text>}
      {account.status_message && (
        <Text style={styles.statusMessage} numberOfLines={1}>
          {account.status_message}
        </Text>
      )}

      {/* Cookies indicator */}
      <View style={styles.cookiesInfo}>
        <Ionicons
          name="key-outline"
          size={14}
          color={account.has_cookies ? '#4ade80' : '#facc15'}
        />
        <Text style={[styles.cookiesText, { color: account.has_cookies ? '#4ade80' : '#facc15' }]}>
          {account.has_cookies ? 'Cookies saved' : 'No cookies'}
        </Text>
      </View>

      {/* Login status */}
      {isLoggingIn && loginStatus && (
        <View style={styles.loginStatus}>
          <ActivityIndicator size="small" color="#60a5fa" />
          <Text style={styles.loginStatusText}>{loginStatus.message}</Text>
        </View>
      )}

      {/* Actions */}
      <View style={styles.actions}>
        {!isLoggingIn ? (
          <TouchableOpacity
            style={[styles.button, styles.primaryButton]}
            onPress={handleStartLogin}
            disabled={startLogin.isPending}
          >
            <Ionicons name="log-in-outline" size={18} color="#fff" />
            <Text style={styles.buttonText}>Login</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[styles.button, styles.cancelButton]}
            onPress={handleCancelLogin}
          >
            <Ionicons name="close-circle-outline" size={18} color="#fff" />
            <Text style={styles.buttonText}>Cancel</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity
          style={[styles.iconButton]}
          onPress={handleValidate}
          disabled={!account.has_cookies || validateCookies.isPending}
        >
          {validateCookies.isPending ? (
            <ActivityIndicator size="small" color="#9ca3af" />
          ) : (
            <Ionicons name="checkmark-circle-outline" size={22} color="#9ca3af" />
          )}
        </TouchableOpacity>

        {account.has_cookies && (
          <TouchableOpacity style={styles.iconButton} onPress={handleDeleteCookies}>
            <Ionicons name="key-outline" size={22} color="#fb923c" />
          </TouchableOpacity>
        )}

        <TouchableOpacity style={styles.iconButton} onPress={handleDelete}>
          <Ionicons name="trash-outline" size={22} color="#f87171" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  platformInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  platformIcon: {
    width: 48,
    height: 48,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  platformText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  username: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  platform: {
    fontSize: 13,
    color: '#9ca3af',
    textTransform: 'capitalize',
  },
  email: {
    fontSize: 13,
    color: '#9ca3af',
    marginBottom: 4,
  },
  statusMessage: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 8,
  },
  cookiesInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  cookiesText: {
    fontSize: 12,
  },
  loginStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(96, 165, 250, 0.1)',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(96, 165, 250, 0.3)',
  },
  loginStatusText: {
    color: '#60a5fa',
    fontSize: 13,
    flex: 1,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  button: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 8,
  },
  primaryButton: {
    backgroundColor: '#3b82f6',
  },
  cancelButton: {
    backgroundColor: '#f97316',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  iconButton: {
    width: 44,
    height: 44,
    backgroundColor: '#374151',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
