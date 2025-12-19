import React, { useState, useEffect } from 'react';
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
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { youtubeChannelsApi, googleApi, oauthApi, YouTubeChannel, GoogleAccount, OAuthConfig } from '../../src/api/client';
import { useGoogleAuth, useDefaultOAuthConfig } from '../../src/hooks/useGoogleAuth';

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function YouTubeChannelCard({
  channel,
  oauthConfig
}: {
  channel: YouTubeChannel;
  oauthConfig: OAuthConfig | null;
}) {
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => youtubeChannelsApi.delete(channel.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['youtube-channels'] });
    },
  });

  const revokeMutation = useMutation({
    mutationFn: () => oauthApi.revokeToken(channel.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['youtube-channels'] });
      Alert.alert('Success', 'OAuth disconnected');
    },
    onError: (error: any) => {
      Alert.alert('Error', error.response?.data?.detail || error.message);
    },
  });

  const { isLoading, isAuthorizing, error, promptAsync, reset } = useGoogleAuth({
    channelId: channel.id,
    oauthConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['youtube-channels'] });
      Alert.alert('Success', 'OAuth connected! You can now use YouTube API.');
    },
    onError: (err) => {
      Alert.alert('OAuth Error', err.message);
    },
  });

  const handlePress = () => {
    Alert.alert(
      channel.channel_name || 'Unnamed Channel',
      `Channel ID: ${channel.channel_id || 'N/A'}\nHandle: ${channel.handle || 'N/A'}\nGoogle: ${channel.google_email}\nOAuth: ${channel.has_oauth ? 'Connected' : 'Not connected'}`,
      [{ text: 'OK' }]
    );
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Channel',
      `Are you sure you want to delete ${channel.channel_name}?`,
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

  const handleOAuthConnect = () => {
    if (!oauthConfig) {
      Alert.alert('No OAuth Config', 'Configure OAuth credentials in Settings first.');
      return;
    }
    promptAsync();
  };

  const handleOAuthDisconnect = () => {
    Alert.alert(
      'Disconnect OAuth',
      'Are you sure you want to disconnect OAuth? You will no longer be able to use YouTube API for this channel.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Disconnect',
          style: 'destructive',
          onPress: () => revokeMutation.mutate(),
        },
      ]
    );
  };

  return (
    <TouchableOpacity style={styles.card} onPress={handlePress} onLongPress={handleDelete}>
      <View style={styles.cardHeader}>
        <View style={styles.cardIcon}>
          <Ionicons name="logo-youtube" size={40} color="#ff0000" />
        </View>
        <View style={styles.cardInfo}>
          <Text style={styles.channelName}>{channel.channel_name || 'Unnamed'}</Text>
          {channel.handle && (
            <Text style={styles.handle}>@{channel.handle}</Text>
          )}
        </View>
        <TouchableOpacity
          style={[styles.oauthBadge, { backgroundColor: channel.has_oauth ? '#22c55e' : '#ef4444' }]}
          onPress={channel.has_oauth ? handleOAuthDisconnect : handleOAuthConnect}
          disabled={isLoading || isAuthorizing || revokeMutation.isPending}
        >
          {isLoading || isAuthorizing || revokeMutation.isPending ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <>
              <Ionicons name={channel.has_oauth ? 'checkmark-circle' : 'key'} size={12} color="#fff" />
              <Text style={styles.oauthText}>{channel.has_oauth ? 'Connected' : 'Connect'}</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      <View style={styles.stats}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{formatNumber(channel.subscriber_count)}</Text>
          <Text style={styles.statLabel}>Subs</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{formatNumber(channel.video_count)}</Text>
          <Text style={styles.statLabel}>Videos</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{formatNumber(channel.view_count)}</Text>
          <Text style={styles.statLabel}>Views</Text>
        </View>
      </View>

      <View style={styles.cardFooter}>
        <Ionicons name="logo-google" size={14} color="#6b7280" />
        <Text style={styles.googleEmail}>{channel.google_email}</Text>
      </View>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={reset}>
            <Ionicons name="close-circle" size={16} color="#ef4444" />
          </TouchableOpacity>
        </View>
      )}
    </TouchableOpacity>
  );
}

export default function YouTubeScreen() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedGoogleId, setSelectedGoogleId] = useState<number | null>(null);
  const [channelName, setChannelName] = useState('');
  const [channelHandle, setChannelHandle] = useState('');

  // Get default OAuth config for native auth
  const { config: oauthConfig, isLoading: oauthLoading } = useDefaultOAuthConfig();

  const { data: channels, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['youtube-channels'],
    queryFn: () => youtubeChannelsApi.list(),
  });

  const { data: googleAccounts } = useQuery({
    queryKey: ['google-accounts'],
    queryFn: () => googleApi.list({ status: 'active' }),
  });

  const createMutation = useMutation({
    mutationFn: () => youtubeChannelsApi.create(selectedGoogleId!, channelName, channelHandle || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['youtube-channels'] });
      setShowCreateModal(false);
      setChannelName('');
      setChannelHandle('');
      setSelectedGoogleId(null);
      Alert.alert('Success', 'Channel created! Complete setup in Browser tab.');
    },
    onError: (error: any) => {
      Alert.alert('Error', error.response?.data?.detail || error.message);
    },
  });

  const handleCreate = () => {
    if (!selectedGoogleId) {
      Alert.alert('Error', 'Select a Google account first');
      return;
    }
    if (!channelName.trim()) {
      Alert.alert('Error', 'Enter a channel name');
      return;
    }
    createMutation.mutate();
  };

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#ff0000" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {!oauthLoading && !oauthConfig && (
        <View style={styles.warningBanner}>
          <Ionicons name="warning" size={20} color="#f59e0b" />
          <Text style={styles.warningText}>No OAuth config. Go to Settings to add one.</Text>
        </View>
      )}
      <FlatList
        data={channels?.channels || []}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => <YouTubeChannelCard channel={item} oauthConfig={oauthConfig} />}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor="#ff0000"
          />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="logo-youtube" size={64} color="#374151" />
            <Text style={styles.emptyText}>No YouTube channels</Text>
            <Text style={styles.emptyHint}>Create a Google account first, then add a channel</Text>
          </View>
        }
      />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => setShowCreateModal(true)}
      >
        <Ionicons name="add" size={28} color="#fff" />
      </TouchableOpacity>

      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowCreateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Create YouTube Channel</Text>
              <TouchableOpacity onPress={() => setShowCreateModal(false)}>
                <Ionicons name="close" size={24} color="#9ca3af" />
              </TouchableOpacity>
            </View>

            <Text style={styles.inputLabel}>Google Account</Text>
            <View style={styles.accountList}>
              {(googleAccounts?.accounts || []).map((acc) => (
                <TouchableOpacity
                  key={acc.id}
                  style={[
                    styles.accountOption,
                    selectedGoogleId === acc.id && styles.accountOptionSelected,
                  ]}
                  onPress={() => setSelectedGoogleId(acc.id)}
                >
                  <Ionicons name="logo-google" size={20} color={selectedGoogleId === acc.id ? '#3b82f6' : '#6b7280'} />
                  <Text style={[
                    styles.accountOptionText,
                    selectedGoogleId === acc.id && styles.accountOptionTextSelected,
                  ]}>
                    {acc.email}
                  </Text>
                </TouchableOpacity>
              ))}
              {(googleAccounts?.accounts || []).length === 0 && (
                <Text style={styles.noAccounts}>No active Google accounts. Create one first.</Text>
              )}
            </View>

            <Text style={styles.inputLabel}>Channel Name</Text>
            <TextInput
              style={styles.input}
              value={channelName}
              onChangeText={setChannelName}
              placeholder="My Awesome Channel"
              placeholderTextColor="#6b7280"
            />

            <Text style={styles.inputLabel}>Handle (optional)</Text>
            <TextInput
              style={styles.input}
              value={channelHandle}
              onChangeText={setChannelHandle}
              placeholder="@myawesomechannel"
              placeholderTextColor="#6b7280"
              autoCapitalize="none"
            />

            <TouchableOpacity
              style={[styles.createButton, createMutation.isPending && styles.createButtonDisabled]}
              onPress={handleCreate}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Ionicons name="add-circle" size={20} color="#fff" />
                  <Text style={styles.createButtonText}>Create Channel</Text>
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
  channelName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  handle: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 2,
  },
  oauthBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  oauthText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#fff',
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
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 12,
  },
  googleEmail: {
    fontSize: 13,
    color: '#6b7280',
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
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#ff0000',
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
    maxHeight: '80%',
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
    marginTop: 16,
  },
  input: {
    backgroundColor: '#374151',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#fff',
  },
  accountList: {
    gap: 8,
  },
  accountOption: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 12,
    borderRadius: 10,
    backgroundColor: '#374151',
  },
  accountOptionSelected: {
    backgroundColor: '#1e40af',
    borderWidth: 1,
    borderColor: '#3b82f6',
  },
  accountOptionText: {
    fontSize: 14,
    color: '#9ca3af',
  },
  accountOptionTextSelected: {
    color: '#fff',
  },
  noAccounts: {
    color: '#6b7280',
    fontSize: 14,
    textAlign: 'center',
    padding: 16,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#ff0000',
    borderRadius: 10,
    paddingVertical: 16,
    marginTop: 24,
  },
  createButtonDisabled: {
    opacity: 0.6,
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#78350f',
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 8,
  },
  warningText: {
    flex: 1,
    fontSize: 13,
    color: '#fef3c7',
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#450a0a',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginTop: 12,
  },
  errorText: {
    flex: 1,
    fontSize: 12,
    color: '#fecaca',
    marginRight: 8,
  },
});
