import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Alert,
  ActivityIndicator,
  Modal,
  TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tiktokApi, TikTokAccount } from '../../src/api/client';

function getStatusColor(status: string) {
  switch (status) {
    case 'active':
      return '#22c55e';
    case 'pending':
      return '#eab308';
    case 'expired':
      return '#f97316';
    case 'error':
    case 'disabled':
      return '#ef4444';
    default:
      return '#6b7280';
  }
}

function formatTimeRemaining(expiresAt: string | null): string {
  if (!expiresAt) return 'No cookies';

  const now = new Date();
  const expires = new Date(expiresAt);
  const diffMs = expires.getTime() - now.getTime();

  if (diffMs <= 0) return 'Expired';

  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h`;

  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  return `${minutes}m`;
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function TikTokAccountCard({ account }: { account: TikTokAccount }) {
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => tiktokApi.delete(account.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tiktok-accounts'] });
    },
  });

  const handlePress = () => {
    Alert.alert(
      account.username ? `@${account.username}` : account.email || 'Account',
      `Email: ${account.email || 'N/A'}\nPassword: ${account.password || 'N/A'}\nDisplay: ${account.display_name || 'N/A'}\nStatus: ${account.status}`,
      [{ text: 'OK' }]
    );
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Account',
      `Are you sure you want to delete ${account.username || account.email}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deleteMutation.mutate(),
        },
      ]
    );
  };

  return (
    <TouchableOpacity style={styles.card} onPress={handlePress} onLongPress={handleDelete}>
      <View style={styles.cardHeader}>
        <View style={styles.cardIcon}>
          <Ionicons name="musical-notes" size={40} color="#69c9d0" />
        </View>
        <View style={styles.cardInfo}>
          {account.username ? (
            <>
              <Text style={styles.username}>@{account.username}</Text>
              {account.display_name && (
                <Text style={styles.displayName}>{account.display_name}</Text>
              )}
            </>
          ) : (
            <Text style={styles.email}>{account.email}</Text>
          )}
        </View>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(account.status) }]}>
          <Text style={styles.statusText}>{account.status}</Text>
        </View>
      </View>

      <View style={styles.stats}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{formatNumber(account.follower_count)}</Text>
          <Text style={styles.statLabel}>Followers</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{formatNumber(account.following_count)}</Text>
          <Text style={styles.statLabel}>Following</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{formatNumber(account.likes_count)}</Text>
          <Text style={styles.statLabel}>Likes</Text>
        </View>
      </View>

      <View style={styles.cardDetails}>
        <View style={styles.detailRow}>
          <Ionicons name="mail-outline" size={16} color="#6b7280" />
          <Text style={styles.detailText}>{account.email || 'No email'}</Text>
        </View>

        <View style={styles.detailRow}>
          <Ionicons name="time-outline" size={16} color="#6b7280" />
          <Text style={styles.detailText}>
            Cookies: {formatTimeRemaining(account.cookies_expires_at)}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

export default function TikTokScreen() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [emailPrefix, setEmailPrefix] = useState('');

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['tiktok-accounts'],
    queryFn: () => tiktokApi.list(),
  });

  const startSignupMutation = useMutation({
    mutationFn: (prefix: string) => tiktokApi.startSignup(prefix),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['tiktok-accounts'] });
      setShowCreateModal(false);
      setEmailPrefix('');
      Alert.alert(
        'Signup Started',
        `Email: ${response.email}\nPassword: ${response.password}\n\nComplete signup in Browser tab (VNC):\n1. Complete captcha\n2. Click Submit\n3. Enter verification code from email`,
        [{ text: 'OK' }]
      );
    },
    onError: (error: any) => {
      Alert.alert('Error', error.response?.data?.detail || error.message || 'Failed to start signup');
    },
  });

  const handleCreate = () => {
    if (!emailPrefix.trim()) {
      Alert.alert('Error', 'Email prefix is required');
      return;
    }
    startSignupMutation.mutate(emailPrefix.trim());
  };

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#69c9d0" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={data?.accounts || []}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => <TikTokAccountCard account={item} />}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor="#69c9d0"
          />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="musical-notes" size={64} color="#374151" />
            <Text style={styles.emptyText}>No TikTok accounts</Text>
            <Text style={styles.emptyHint}>Tap + to create a new account</Text>
          </View>
        }
      />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => setShowCreateModal(true)}
        disabled={startSignupMutation.isPending}
      >
        {startSignupMutation.isPending ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Ionicons name="add" size={28} color="#fff" />
        )}
      </TouchableOpacity>

      {/* Create Account Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowCreateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>New TikTok Account</Text>
              <TouchableOpacity onPress={() => setShowCreateModal(false)}>
                <Ionicons name="close" size={24} color="#9ca3af" />
              </TouchableOpacity>
            </View>

            <Text style={styles.inputLabel}>Email Prefix</Text>
            <TextInput
              style={styles.input}
              value={emailPrefix}
              onChangeText={setEmailPrefix}
              placeholder="myaccount"
              placeholderTextColor="#6b7280"
              autoCapitalize="none"
              autoCorrect={false}
            />
            <Text style={styles.hint}>
              Will create: {emailPrefix || 'prefix'}@yourdomain.com
            </Text>

            <View style={styles.infoBox}>
              <Ionicons name="information-circle" size={20} color="#69c9d0" />
              <Text style={styles.infoText}>
                This will open Selenium browser. Complete captcha and verification via VNC (Browser tab).
              </Text>
            </View>

            <TouchableOpacity
              style={[styles.createButton, startSignupMutation.isPending && styles.createButtonDisabled]}
              onPress={handleCreate}
              disabled={startSignupMutation.isPending}
            >
              {startSignupMutation.isPending ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Ionicons name="add-circle" size={20} color="#fff" />
                  <Text style={styles.createButtonText}>Start Signup</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#111827',
  },
  list: {
    padding: 16,
    paddingBottom: 100,
  },
  card: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardIcon: {
    marginRight: 12,
  },
  cardInfo: {
    flex: 1,
  },
  username: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  displayName: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 2,
  },
  email: {
    fontSize: 14,
    color: '#9ca3af',
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
    textTransform: 'capitalize',
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#374151',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
  statLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  cardDetails: {
    paddingTop: 12,
    gap: 8,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  detailText: {
    fontSize: 14,
    color: '#9ca3af',
  },
  empty: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#6b7280',
    marginTop: 16,
  },
  emptyHint: {
    fontSize: 14,
    color: '#4b5563',
    marginTop: 8,
  },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#69c9d0',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1f2937',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#9ca3af',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#374151',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#fff',
  },
  hint: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 8,
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#134e4a',
    padding: 12,
    borderRadius: 10,
    marginTop: 16,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#5eead4',
    lineHeight: 18,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#69c9d0',
    borderRadius: 10,
    paddingVertical: 16,
    marginTop: 20,
  },
  createButtonDisabled: {
    opacity: 0.6,
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
