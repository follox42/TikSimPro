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
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { googleApi, GoogleAccount } from '../../src/api/client';

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

function GoogleAccountCard({ account }: { account: GoogleAccount }) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => googleApi.delete(account.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['google-accounts'] });
    },
  });

  const handlePress = () => {
    // Navigate to detail page when implemented
    Alert.alert(
      account.email,
      `Password: ${account.password || 'N/A'}\nRecovery: ${account.recovery_email || 'N/A'}\nStatus: ${account.status}\nChannels: ${account.youtube_channels_count}`,
      [{ text: 'OK' }]
    );
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Account',
      `Are you sure you want to delete ${account.email}?`,
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
          {account.avatar_url ? (
            <Ionicons name="person-circle" size={40} color="#3b82f6" />
          ) : (
            <Ionicons name="logo-google" size={40} color="#3b82f6" />
          )}
        </View>
        <View style={styles.cardInfo}>
          <Text style={styles.email}>{account.email}</Text>
          <Text style={styles.name}>
            {account.first_name} {account.last_name}
          </Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(account.status) }]}>
          <Text style={styles.statusText}>{account.status}</Text>
        </View>
      </View>

      <View style={styles.cardDetails}>
        <View style={styles.detailRow}>
          <Ionicons name="key-outline" size={16} color="#6b7280" />
          <Text style={styles.detailText}>
            {account.password ? '********' : 'No password'}
          </Text>
        </View>

        <View style={styles.detailRow}>
          <Ionicons name="time-outline" size={16} color="#6b7280" />
          <Text style={styles.detailText}>
            Cookies: {formatTimeRemaining(account.cookies_expires_at)}
          </Text>
        </View>

        <View style={styles.detailRow}>
          <Ionicons name="logo-youtube" size={16} color="#ff0000" />
          <Text style={styles.detailText}>
            {account.youtube_channels_count} channel{account.youtube_channels_count !== 1 ? 's' : ''}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

export default function GoogleScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [emailPrefix, setEmailPrefix] = useState('');

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['google-accounts'],
    queryFn: () => googleApi.list(),
  });

  const startSignupMutation = useMutation({
    mutationFn: (prefix?: string) => googleApi.startSignup(prefix),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['google-accounts'] });
      setShowCreateModal(false);
      setEmailPrefix('');
      Alert.alert(
        'Signup Started',
        `Email: ${response.email}\nPassword: ${response.password}\nRecovery: ${response.recovery_email}\n\nComplete signup in Browser tab (VNC)`,
        [{ text: 'OK' }]
      );
    },
    onError: (error: any) => {
      Alert.alert('Error', error.response?.data?.detail || error.message || 'Failed to start signup');
    },
  });

  const handleCreate = () => {
    startSignupMutation.mutate(emailPrefix.trim() || undefined);
  };

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={data?.accounts || []}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => <GoogleAccountCard account={item} />}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor="#3b82f6"
          />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="logo-google" size={64} color="#374151" />
            <Text style={styles.emptyText}>No Google accounts</Text>
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
              <Text style={styles.modalTitle}>New Google Account</Text>
              <TouchableOpacity onPress={() => setShowCreateModal(false)}>
                <Ionicons name="close" size={24} color="#9ca3af" />
              </TouchableOpacity>
            </View>

            <Text style={styles.inputLabel}>Email Prefix (optional)</Text>
            <TextInput
              style={styles.input}
              value={emailPrefix}
              onChangeText={setEmailPrefix}
              placeholder="john.doe (or leave empty to generate)"
              placeholderTextColor="#6b7280"
              autoCapitalize="none"
              autoCorrect={false}
            />
            <Text style={styles.hint}>
              Will create: {emailPrefix || 'random'}@gmail.com
            </Text>

            <View style={styles.infoBox}>
              <Ionicons name="information-circle" size={20} color="#60a5fa" />
              <Text style={styles.infoText}>
                This will open Selenium browser. Complete the signup manually via VNC (Browser tab).
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
  email: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  name: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 2,
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
  cardDetails: {
    borderTopWidth: 1,
    borderTopColor: '#374151',
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
    backgroundColor: '#3b82f6',
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
    backgroundColor: '#1e3a5f',
    padding: 12,
    borderRadius: 10,
    marginTop: 16,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#93c5fd',
    lineHeight: 18,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#3b82f6',
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
