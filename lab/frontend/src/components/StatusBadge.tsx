import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { AccountStatus } from '../api/client';

interface StatusBadgeProps {
  status: AccountStatus;
}

const statusConfig: Record<AccountStatus, { label: string; bgColor: string; textColor: string }> = {
  pending: {
    label: 'Pending',
    bgColor: 'rgba(234, 179, 8, 0.2)',
    textColor: '#facc15',
  },
  active: {
    label: 'Active',
    bgColor: 'rgba(34, 197, 94, 0.2)',
    textColor: '#4ade80',
  },
  expired: {
    label: 'Expired',
    bgColor: 'rgba(249, 115, 22, 0.2)',
    textColor: '#fb923c',
  },
  error: {
    label: 'Error',
    bgColor: 'rgba(239, 68, 68, 0.2)',
    textColor: '#f87171',
  },
  disabled: {
    label: 'Disabled',
    bgColor: 'rgba(107, 114, 128, 0.2)',
    textColor: '#9ca3af',
  },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <View style={[styles.badge, { backgroundColor: config.bgColor }]}>
      <Text style={[styles.text, { color: config.textColor }]}>{config.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  text: {
    fontSize: 12,
    fontWeight: '600',
  },
});
