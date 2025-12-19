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
import { useRouter } from 'expo-router';
import { useEmails, useMailStats, useToggleStar, useMarkAllRead } from '../../src/hooks/useMail';
import { EmailSummary } from '../../src/api/client';

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else if (days === 1) {
    return 'Yesterday';
  } else if (days < 7) {
    return date.toLocaleDateString([], { weekday: 'short' });
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }
}

function EmailRow({ email, onPress }: { email: EmailSummary; onPress: () => void }) {
  const toggleStar = useToggleStar();

  const handleStar = () => {
    toggleStar.mutate(email.id);
  };

  return (
    <TouchableOpacity
      style={[styles.emailRow, !email.is_read && styles.emailUnread]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <TouchableOpacity onPress={handleStar} style={styles.starButton}>
        <Ionicons
          name={email.is_starred ? 'star' : 'star-outline'}
          size={20}
          color={email.is_starred ? '#fbbf24' : '#6b7280'}
        />
      </TouchableOpacity>
      <View style={styles.emailContent}>
        <View style={styles.emailHeader}>
          <Text style={[styles.emailFrom, !email.is_read && styles.textBold]} numberOfLines={1}>
            {email.mail_from}
          </Text>
          <Text style={styles.emailDate}>{formatDate(email.received_at)}</Text>
        </View>
        <Text style={[styles.emailSubject, !email.is_read && styles.textBold]} numberOfLines={1}>
          {email.subject || '(No subject)'}
        </Text>
        {email.alias_prefix && (
          <View style={styles.aliasBadge}>
            <Text style={styles.aliasBadgeText}>{email.alias_prefix}</Text>
          </View>
        )}
      </View>
      <Ionicons name="chevron-forward" size={20} color="#4b5563" />
    </TouchableOpacity>
  );
}

export default function MailScreen() {
  const router = useRouter();
  const [filter, setFilter] = useState<'all' | 'unread' | 'starred'>('all');

  const { data: stats } = useMailStats();
  const { data, isLoading, refetch, isRefetching } = useEmails({
    unread_only: filter === 'unread',
    starred_only: filter === 'starred',
  });
  const markAllRead = useMarkAllRead();

  const emails = data?.emails || [];

  const handleMarkAllRead = () => {
    markAllRead.mutate(undefined);
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <View style={styles.emptyIcon}>
        <Ionicons name="mail-outline" size={64} color="#374151" />
      </View>
      <Text style={styles.emptyTitle}>No emails</Text>
      <Text style={styles.emptyText}>
        {filter === 'all'
          ? 'Your inbox is empty. Emails sent to your domain will appear here.'
          : filter === 'unread'
          ? 'No unread emails'
          : 'No starred emails'}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{stats?.total_emails || 0}</Text>
          <Text style={styles.statLabel}>Total</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, styles.unreadValue]}>{stats?.unread_emails || 0}</Text>
          <Text style={styles.statLabel}>Unread</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{stats?.emails_today || 0}</Text>
          <Text style={styles.statLabel}>Today</Text>
        </View>
        {(stats?.unread_emails || 0) > 0 && (
          <TouchableOpacity style={styles.markAllButton} onPress={handleMarkAllRead}>
            <Ionicons name="checkmark-done" size={16} color="#60a5fa" />
            <Text style={styles.markAllText}>Mark all read</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Filters */}
      <View style={styles.filters}>
        <TouchableOpacity
          style={[styles.filterButton, filter === 'all' && styles.filterButtonActive]}
          onPress={() => setFilter('all')}
        >
          <Text style={[styles.filterText, filter === 'all' && styles.filterTextActive]}>All</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterButton, filter === 'unread' && styles.filterButtonActive]}
          onPress={() => setFilter('unread')}
        >
          <Text style={[styles.filterText, filter === 'unread' && styles.filterTextActive]}>
            Unread
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterButton, filter === 'starred' && styles.filterButtonActive]}
          onPress={() => setFilter('starred')}
        >
          <Ionicons
            name="star"
            size={14}
            color={filter === 'starred' ? '#fff' : '#9ca3af'}
            style={{ marginRight: 4 }}
          />
          <Text style={[styles.filterText, filter === 'starred' && styles.filterTextActive]}>
            Starred
          </Text>
        </TouchableOpacity>
      </View>

      {/* List */}
      {isLoading ? (
        <View style={styles.loading}>
          <ActivityIndicator size="large" color="#3b82f6" />
        </View>
      ) : (
        <FlatList
          data={emails}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <EmailRow email={item} onPress={() => router.push(`/email/${item.id}`)} />
          )}
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
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#1f2937',
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  statItem: {
    alignItems: 'center',
    marginRight: 20,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
  unreadValue: {
    color: '#3b82f6',
  },
  statLabel: {
    fontSize: 11,
    color: '#9ca3af',
    marginTop: 2,
  },
  markAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 'auto',
    gap: 4,
  },
  markAllText: {
    fontSize: 13,
    color: '#60a5fa',
  },
  filters: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 16,
    backgroundColor: '#1f2937',
    borderWidth: 1,
    borderColor: '#374151',
  },
  filterButtonActive: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  filterText: {
    fontSize: 13,
    color: '#9ca3af',
  },
  filterTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  list: {
    paddingBottom: 20,
  },
  emailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    backgroundColor: '#111827',
    borderBottomWidth: 1,
    borderBottomColor: '#1f2937',
  },
  emailUnread: {
    backgroundColor: '#1a2332',
  },
  starButton: {
    padding: 4,
    marginRight: 10,
  },
  emailContent: {
    flex: 1,
    marginRight: 8,
  },
  emailHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  emailFrom: {
    flex: 1,
    fontSize: 14,
    color: '#d1d5db',
    marginRight: 8,
  },
  emailDate: {
    fontSize: 12,
    color: '#6b7280',
  },
  emailSubject: {
    fontSize: 14,
    color: '#9ca3af',
  },
  textBold: {
    fontWeight: '600',
    color: '#fff',
  },
  aliasBadge: {
    alignSelf: 'flex-start',
    marginTop: 6,
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  aliasBadgeText: {
    fontSize: 11,
    color: '#60a5fa',
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
    paddingHorizontal: 40,
  },
});
