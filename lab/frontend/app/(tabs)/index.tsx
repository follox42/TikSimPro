import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AccountCard from '../../src/components/AccountCard';
import AddAccountModal from '../../src/components/AddAccountModal';
import { useAccounts } from '../../src/hooks/useAccounts';
import { Platform, AccountStatus } from '../../src/api/client';

export default function AccountsScreen() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [platformFilter, setPlatformFilter] = useState<Platform | undefined>();

  const { data, isLoading, refetch, isRefetching } = useAccounts({
    platform: platformFilter,
  });

  const accounts = data?.accounts || [];

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <View style={styles.emptyIcon}>
        <Ionicons name="add-circle-outline" size={64} color="#374151" />
      </View>
      <Text style={styles.emptyTitle}>No accounts yet</Text>
      <Text style={styles.emptyText}>
        Add your first TikTok or YouTube account to get started
      </Text>
      <TouchableOpacity style={styles.emptyButton} onPress={() => setShowAddModal(true)}>
        <Ionicons name="add" size={20} color="#fff" />
        <Text style={styles.emptyButtonText}>Add Account</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header Actions */}
      <View style={styles.headerActions}>
        <TouchableOpacity onPress={() => refetch()} style={styles.headerButton}>
          <Ionicons
            name="refresh"
            size={22}
            color="#9ca3af"
            style={isRefetching ? styles.spinning : undefined}
          />
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setShowAddModal(true)} style={styles.addButton}>
          <Ionicons name="add" size={20} color="#fff" />
          <Text style={styles.addButtonText}>Add</Text>
        </TouchableOpacity>
      </View>

      {/* Filters */}
      <View style={styles.filters}>
        <TouchableOpacity
          style={[styles.filterButton, !platformFilter && styles.filterButtonActive]}
          onPress={() => setPlatformFilter(undefined)}
        >
          <Text style={[styles.filterText, !platformFilter && styles.filterTextActive]}>All</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterButton, platformFilter === 'tiktok' && styles.filterButtonTiktok]}
          onPress={() => setPlatformFilter(platformFilter === 'tiktok' ? undefined : 'tiktok')}
        >
          <Text
            style={[styles.filterText, platformFilter === 'tiktok' && styles.filterTextTiktok]}
          >
            TikTok
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterButton, platformFilter === 'youtube' && styles.filterButtonYoutube]}
          onPress={() => setPlatformFilter(platformFilter === 'youtube' ? undefined : 'youtube')}
        >
          <Text
            style={[styles.filterText, platformFilter === 'youtube' && styles.filterTextYoutube]}
          >
            YouTube
          </Text>
        </TouchableOpacity>
      </View>

      {/* Count */}
      <Text style={styles.count}>
        {data?.total || 0} account{(data?.total || 0) !== 1 ? 's' : ''}
      </Text>

      {/* List */}
      {isLoading ? (
        <View style={styles.loading}>
          <ActivityIndicator size="large" color="#3b82f6" />
        </View>
      ) : (
        <FlatList
          data={accounts}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => <AccountCard account={item} />}
          contentContainerStyle={styles.list}
          ListEmptyComponent={renderEmptyState}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor="#3b82f6"
              colors={['#3b82f6']}
            />
          }
        />
      )}

      {/* Add modal */}
      <AddAccountModal visible={showAddModal} onClose={() => setShowAddModal(false)} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  headerActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 8,
    gap: 12,
  },
  headerButton: {
    padding: 8,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#3b82f6',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  spinning: {
    opacity: 0.5,
  },
  filters: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#1f2937',
    borderWidth: 1,
    borderColor: '#374151',
  },
  filterButtonActive: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  filterButtonTiktok: {
    backgroundColor: 'rgba(236, 72, 153, 0.2)',
    borderColor: '#ec4899',
  },
  filterButtonYoutube: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    borderColor: '#ef4444',
  },
  filterText: {
    fontSize: 14,
    color: '#9ca3af',
  },
  filterTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  filterTextTiktok: {
    color: '#ec4899',
    fontWeight: '600',
  },
  filterTextYoutube: {
    color: '#ef4444',
    fontWeight: '600',
  },
  count: {
    paddingHorizontal: 16,
    paddingBottom: 8,
    fontSize: 14,
    color: '#6b7280',
  },
  list: {
    padding: 16,
    paddingTop: 0,
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#1f2937',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#d1d5db',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 24,
    paddingHorizontal: 40,
  },
  emptyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#3b82f6',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 10,
  },
  emptyButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
