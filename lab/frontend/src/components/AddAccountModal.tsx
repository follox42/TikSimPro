import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  TextInput,
  Alert,
  KeyboardAvoidingView,
  Platform as RNPlatform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Platform, CreateAccount } from '../api/client';
import { useCreateAccount } from '../hooks/useAccounts';

interface AddAccountModalProps {
  visible: boolean;
  onClose: () => void;
}

export default function AddAccountModal({ visible, onClose }: AddAccountModalProps) {
  const [platform, setPlatform] = useState<Platform>('tiktok');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');

  const createAccount = useCreateAccount();

  const handleSubmit = async () => {
    if (!username.trim()) {
      Alert.alert('Error', 'Username is required');
      return;
    }

    const data: CreateAccount = {
      platform,
      username: username.trim(),
    };

    if (email.trim()) {
      data.email = email.trim();
    }

    try {
      await createAccount.mutateAsync(data);
      setUsername('');
      setEmail('');
      setPlatform('tiktok');
      onClose();
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to create account');
    }
  };

  const handleClose = () => {
    setUsername('');
    setEmail('');
    setPlatform('tiktok');
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <KeyboardAvoidingView
        behavior={RNPlatform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.overlay}
      >
        <View style={styles.container}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Add Account</Text>
            <TouchableOpacity onPress={handleClose}>
              <Ionicons name="close" size={28} color="#9ca3af" />
            </TouchableOpacity>
          </View>

          {/* Platform selector */}
          <Text style={styles.label}>Platform</Text>
          <View style={styles.platformSelector}>
            <TouchableOpacity
              style={[
                styles.platformButton,
                platform === 'tiktok' && styles.platformButtonActive,
                platform === 'tiktok' && { borderColor: '#ec4899' },
              ]}
              onPress={() => setPlatform('tiktok')}
            >
              <Text
                style={[
                  styles.platformButtonText,
                  platform === 'tiktok' && { color: '#ec4899' },
                ]}
              >
                TikTok
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.platformButton,
                platform === 'youtube' && styles.platformButtonActive,
                platform === 'youtube' && { borderColor: '#ef4444' },
              ]}
              onPress={() => setPlatform('youtube')}
            >
              <Text
                style={[
                  styles.platformButtonText,
                  platform === 'youtube' && { color: '#ef4444' },
                ]}
              >
                YouTube
              </Text>
            </TouchableOpacity>
          </View>

          {/* Username */}
          <Text style={styles.label}>Username *</Text>
          <TextInput
            style={styles.input}
            value={username}
            onChangeText={setUsername}
            placeholder={platform === 'tiktok' ? '@username' : 'Channel name'}
            placeholderTextColor="#6b7280"
            autoCapitalize="none"
            autoCorrect={false}
          />

          {/* Email */}
          <Text style={styles.label}>Email (optional)</Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            placeholder="email@example.com"
            placeholderTextColor="#6b7280"
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
          />

          {/* Buttons */}
          <View style={styles.buttons}>
            <TouchableOpacity style={styles.cancelButton} onPress={handleClose}>
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.submitButton, !username.trim() && styles.submitButtonDisabled]}
              onPress={handleSubmit}
              disabled={!username.trim() || createAccount.isPending}
            >
              <Ionicons name="add" size={20} color="#fff" />
              <Text style={styles.submitButtonText}>
                {createAccount.isPending ? 'Adding...' : 'Add Account'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: '#1f2937',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#9ca3af',
    marginBottom: 8,
  },
  platformSelector: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  platformButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#374151',
    backgroundColor: '#374151',
    alignItems: 'center',
  },
  platformButtonActive: {
    backgroundColor: 'transparent',
  },
  platformButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#9ca3af',
  },
  input: {
    backgroundColor: '#374151',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#fff',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#4b5563',
  },
  buttons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: '#374151',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#9ca3af',
  },
  submitButton: {
    flex: 1,
    flexDirection: 'row',
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: '#3b82f6',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
