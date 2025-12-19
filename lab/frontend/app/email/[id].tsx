import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  useWindowDimensions,
} from 'react-native';
import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useEmail, useToggleStar, useMarkRead, useDeleteEmail } from '../../src/hooks/useMail';

function formatFullDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString([], {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function EmailDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const emailId = parseInt(id || '0', 10);

  const { data: email, isLoading, error } = useEmail(emailId);
  const toggleStar = useToggleStar();
  const markRead = useMarkRead();
  const deleteEmail = useDeleteEmail();

  // Mark as read when opened
  useEffect(() => {
    if (email && !email.is_read) {
      markRead.mutate({ id: emailId, is_read: true });
    }
  }, [email?.id]);

  const handleStar = () => {
    toggleStar.mutate(emailId);
  };

  const handleDelete = () => {
    Alert.alert('Delete Email', 'Are you sure you want to delete this email?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteEmail.mutateAsync(emailId);
            router.back();
          } catch (e) {
            Alert.alert('Error', 'Failed to delete email');
          }
        },
      },
    ]);
  };

  const handleMarkUnread = () => {
    markRead.mutate({ id: emailId, is_read: false });
    router.back();
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <Stack.Screen options={{ title: 'Loading...' }} />
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  if (error || !email) {
    return (
      <View style={styles.errorContainer}>
        <Stack.Screen options={{ title: 'Error' }} />
        <Ionicons name="alert-circle" size={64} color="#ef4444" />
        <Text style={styles.errorText}>Failed to load email</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => router.back()}>
          <Text style={styles.retryButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Stack.Screen
        options={{
          title: '',
          headerRight: () => (
            <View style={styles.headerActions}>
              <TouchableOpacity onPress={handleMarkUnread} style={styles.headerButton}>
                <Ionicons name="mail-unread-outline" size={22} color="#9ca3af" />
              </TouchableOpacity>
              <TouchableOpacity onPress={handleStar} style={styles.headerButton}>
                <Ionicons
                  name={email.is_starred ? 'star' : 'star-outline'}
                  size={22}
                  color={email.is_starred ? '#fbbf24' : '#9ca3af'}
                />
              </TouchableOpacity>
              <TouchableOpacity onPress={handleDelete} style={styles.headerButton}>
                <Ionicons name="trash-outline" size={22} color="#ef4444" />
              </TouchableOpacity>
            </View>
          ),
        }}
      />

      <ScrollView style={styles.scrollView}>
        {/* Subject */}
        <View style={styles.subjectContainer}>
          <Text style={styles.subject}>{email.subject || '(No subject)'}</Text>
          {email.alias_prefix && (
            <View style={styles.aliasBadge}>
              <Ionicons name="at" size={12} color="#60a5fa" />
              <Text style={styles.aliasBadgeText}>{email.alias_prefix}</Text>
            </View>
          )}
        </View>

        {/* Sender Info */}
        <View style={styles.senderContainer}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {email.mail_from.charAt(0).toUpperCase()}
            </Text>
          </View>
          <View style={styles.senderInfo}>
            <Text style={styles.senderName}>{email.mail_from}</Text>
            <Text style={styles.recipientText}>
              To: {email.rcpt_to}
            </Text>
          </View>
        </View>

        {/* Date */}
        <View style={styles.dateContainer}>
          <Ionicons name="time-outline" size={14} color="#6b7280" />
          <Text style={styles.dateText}>{formatFullDate(email.received_at)}</Text>
        </View>

        {/* Body */}
        <View style={styles.bodyContainer}>
          {email.body_text ? (
            <Text style={styles.bodyText}>{email.body_text}</Text>
          ) : email.body_html ? (
            <View style={styles.htmlNotice}>
              <Ionicons name="code-outline" size={20} color="#6b7280" />
              <Text style={styles.htmlNoticeText}>
                This email contains HTML content. Plain text preview not available.
              </Text>
            </View>
          ) : (
            <Text style={styles.emptyBody}>(No content)</Text>
          )}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#111827',
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    backgroundColor: '#111827',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#9ca3af',
    marginTop: 16,
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerButton: {
    padding: 6,
  },
  scrollView: {
    flex: 1,
  },
  subjectContainer: {
    padding: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1f2937',
  },
  subject: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    lineHeight: 28,
  },
  aliasBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    marginTop: 10,
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  aliasBadgeText: {
    fontSize: 12,
    color: '#60a5fa',
    fontWeight: '500',
  },
  senderContainer: {
    flexDirection: 'row',
    padding: 16,
    paddingBottom: 12,
    alignItems: 'center',
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#3b82f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  senderInfo: {
    flex: 1,
  },
  senderName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
  recipientText: {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 2,
  },
  dateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#1f2937',
  },
  dateText: {
    fontSize: 13,
    color: '#6b7280',
  },
  bodyContainer: {
    padding: 16,
  },
  bodyText: {
    fontSize: 15,
    color: '#d1d5db',
    lineHeight: 24,
  },
  htmlNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#1f2937',
    borderRadius: 8,
    gap: 10,
  },
  htmlNoticeText: {
    flex: 1,
    fontSize: 14,
    color: '#6b7280',
  },
  emptyBody: {
    fontSize: 15,
    color: '#4b5563',
    fontStyle: 'italic',
  },
});
