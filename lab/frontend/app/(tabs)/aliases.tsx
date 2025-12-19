import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  TextInput,
  Modal,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAliases, useCreateAlias, useDeleteAlias, useMailStats } from '../../src/hooks/useMail';
import { EmailAlias } from '../../src/api/client';

function AliasRow({
  alias,
  domain,
  onDelete,
}: {
  alias: EmailAlias;
  domain: string;
  onDelete: () => void;
}) {
  const handleDelete = () => {
    Alert.alert('Delete Alias', `Delete "${alias.alias}@${domain}"?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: onDelete },
    ]);
  };

  return (
    <View style={styles.aliasRow}>
      <View style={styles.aliasIcon}>
        <Ionicons name="at" size={20} color="#60a5fa" />
      </View>
      <View style={styles.aliasContent}>
        <Text style={styles.aliasAddress}>
          <Text style={styles.aliasPrefix}>{alias.alias}</Text>
          <Text style={styles.aliasDomain}>@{domain}</Text>
        </Text>
        {alias.description && <Text style={styles.aliasDescription}>{alias.description}</Text>}
        <Text style={styles.aliasStats}>
          {alias.email_count} email{alias.email_count !== 1 ? 's' : ''} received
        </Text>
      </View>
      <TouchableOpacity onPress={handleDelete} style={styles.deleteButton}>
        <Ionicons name="trash-outline" size={20} color="#ef4444" />
      </TouchableOpacity>
    </View>
  );
}

function CreateAliasModal({
  visible,
  onClose,
  domain,
}: {
  visible: boolean;
  onClose: () => void;
  domain: string;
}) {
  const [alias, setAlias] = useState('');
  const [description, setDescription] = useState('');
  const createAlias = useCreateAlias();

  const handleCreate = async () => {
    if (!alias.trim()) {
      Alert.alert('Error', 'Please enter an alias prefix');
      return;
    }

    try {
      await createAlias.mutateAsync({
        alias: alias.trim().toLowerCase(),
        description: description.trim() || undefined,
      });
      setAlias('');
      setDescription('');
      onClose();
    } catch (e: any) {
      Alert.alert('Error', e.response?.data?.detail || 'Failed to create alias');
    }
  };

  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Create Alias</Text>
            <TouchableOpacity onPress={onClose}>
              <Ionicons name="close" size={24} color="#9ca3af" />
            </TouchableOpacity>
          </View>

          <Text style={styles.inputLabel}>Alias Prefix</Text>
          <View style={styles.aliasInputContainer}>
            <TextInput
              style={styles.aliasInput}
              value={alias}
              onChangeText={setAlias}
              placeholder="newsletter"
              placeholderTextColor="#6b7280"
              autoCapitalize="none"
              autoCorrect={false}
            />
            <Text style={styles.aliasInputDomain}>@{domain}</Text>
          </View>
          <Text style={styles.inputHint}>
            All emails sent to this address will be stored in your inbox
          </Text>

          <Text style={[styles.inputLabel, { marginTop: 16 }]}>Description (optional)</Text>
          <TextInput
            style={styles.input}
            value={description}
            onChangeText={setDescription}
            placeholder="Newsletter subscriptions"
            placeholderTextColor="#6b7280"
          />

          <TouchableOpacity
            style={[styles.createButton, createAlias.isPending && styles.buttonDisabled]}
            onPress={handleCreate}
            disabled={createAlias.isPending}
          >
            {createAlias.isPending ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="add" size={20} color="#fff" />
                <Text style={styles.createButtonText}>Create Alias</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

export default function AliasesScreen() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const { data: stats } = useMailStats();
  const { data: aliases, isLoading, refetch, isRefetching } = useAliases();
  const deleteAlias = useDeleteAlias();

  // TODO: Get domain from settings
  const domain = 'example.com';

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <View style={styles.emptyIcon}>
        <Ionicons name="at" size={64} color="#374151" />
      </View>
      <Text style={styles.emptyTitle}>No aliases yet</Text>
      <Text style={styles.emptyText}>
        Create aliases to organize incoming emails. All emails to your domain are received, but
        aliases help you filter and categorize them.
      </Text>
      <TouchableOpacity style={styles.emptyButton} onPress={() => setShowCreateModal(true)}>
        <Ionicons name="add" size={20} color="#fff" />
        <Text style={styles.emptyButtonText}>Create Alias</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Email Aliases</Text>
          <Text style={styles.headerSubtitle}>{stats?.total_aliases || 0} aliases created</Text>
        </View>
        <TouchableOpacity style={styles.addButton} onPress={() => setShowCreateModal(true)}>
          <Ionicons name="add" size={20} color="#fff" />
          <Text style={styles.addButtonText}>New</Text>
        </TouchableOpacity>
      </View>

      {/* Info */}
      <View style={styles.infoBox}>
        <Ionicons name="information-circle" size={20} color="#60a5fa" />
        <Text style={styles.infoText}>
          All emails sent to *@{domain} are received. Aliases help you filter and track specific
          addresses.
        </Text>
      </View>

      {/* List */}
      {isLoading ? (
        <View style={styles.loading}>
          <ActivityIndicator size="large" color="#3b82f6" />
        </View>
      ) : (
        <FlatList
          data={aliases || []}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <AliasRow
              alias={item}
              domain={domain}
              onDelete={() => deleteAlias.mutate(item.id)}
            />
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

      {/* Create Modal */}
      <CreateAliasModal
        visible={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        domain={domain}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1f2937',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 2,
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
  infoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
    marginHorizontal: 16,
    marginTop: 12,
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    borderRadius: 8,
    gap: 10,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#93c5fd',
    lineHeight: 18,
  },
  list: {
    padding: 16,
  },
  aliasRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    backgroundColor: '#1f2937',
    borderRadius: 10,
    marginBottom: 10,
  },
  aliasIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  aliasContent: {
    flex: 1,
  },
  aliasAddress: {
    fontSize: 15,
  },
  aliasPrefix: {
    fontWeight: '600',
    color: '#fff',
  },
  aliasDomain: {
    color: '#6b7280',
  },
  aliasDescription: {
    fontSize: 13,
    color: '#9ca3af',
    marginTop: 2,
  },
  aliasStats: {
    fontSize: 12,
    color: '#4b5563',
    marginTop: 4,
  },
  deleteButton: {
    padding: 8,
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
    marginBottom: 24,
    lineHeight: 20,
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
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1f2937',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 40,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#9ca3af',
    marginBottom: 8,
  },
  aliasInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111827',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#374151',
  },
  aliasInput: {
    flex: 1,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#fff',
  },
  aliasInputDomain: {
    paddingRight: 16,
    fontSize: 16,
    color: '#6b7280',
  },
  inputHint: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 6,
  },
  input: {
    backgroundColor: '#111827',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#374151',
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#3b82f6',
    paddingVertical: 16,
    borderRadius: 10,
    marginTop: 24,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
