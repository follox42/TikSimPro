import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ScrollView,
  ActivityIndicator,
  Modal,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  setApiBaseUrl,
  settingsApi,
  oauthApi,
  RecoveryEmailConfig,
  OAuthConfig,
  OAuthConfigCreate,
} from '../../src/api/client';

const API_URL_KEY = 'lab_api_url';
const DEFAULT_URL = 'http://192.168.1.100:8001/api';

export default function SettingsScreen() {
  const queryClient = useQueryClient();
  const [apiUrl, setApiUrl] = useState(DEFAULT_URL);
  const [isTesting, setIsTesting] = useState(false);

  // Recovery email state
  const [recoveryMode, setRecoveryMode] = useState<'fixed' | 'auto'>('fixed');
  const [fixedEmail, setFixedEmail] = useState('');
  const [recoveryDomain, setRecoveryDomain] = useState('');

  // OAuth modal state
  const [showOAuthModal, setShowOAuthModal] = useState(false);
  const [editingOAuth, setEditingOAuth] = useState<OAuthConfig | null>(null);
  const [oauthName, setOauthName] = useState('');
  const [oauthClientId, setOauthClientId] = useState('');
  const [oauthClientSecret, setOauthClientSecret] = useState('');
  const [oauthIsDefault, setOauthIsDefault] = useState(false);

  // Fetch settings from server
  const { data: settings, isLoading: loadingSettings } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.list,
  });

  // Fetch recovery config
  const { data: recoveryConfig, isLoading: loadingRecoveryConfig } = useQuery({
    queryKey: ['recovery-config'],
    queryFn: settingsApi.getRecoveryConfig,
  });

  // Fetch OAuth configs
  const { data: oauthConfigs, isLoading: loadingOAuth } = useQuery({
    queryKey: ['oauth-configs'],
    queryFn: oauthApi.listConfigs,
  });

  // Update recovery config mutation
  const updateRecoveryMutation = useMutation({
    mutationFn: (config: { mode: 'fixed' | 'auto'; fixedEmail?: string; domain?: string }) =>
      settingsApi.setRecoveryConfig(config.mode, config.fixedEmail, config.domain),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recovery-config'] });
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      Alert.alert('Success', 'Recovery email configuration updated');
    },
    onError: (error: any) => {
      Alert.alert('Error', error.message || 'Failed to update');
    },
  });

  // Create OAuth config mutation
  const createOAuthMutation = useMutation({
    mutationFn: (data: OAuthConfigCreate) => oauthApi.createConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['oauth-configs'] });
      setShowOAuthModal(false);
      resetOAuthForm();
      Alert.alert('Success', 'OAuth configuration created');
    },
    onError: (error: any) => {
      Alert.alert('Error', error.response?.data?.detail || error.message);
    },
  });

  // Update OAuth config mutation
  const updateOAuthMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<OAuthConfigCreate> }) =>
      oauthApi.updateConfig(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['oauth-configs'] });
      setShowOAuthModal(false);
      resetOAuthForm();
      Alert.alert('Success', 'OAuth configuration updated');
    },
    onError: (error: any) => {
      Alert.alert('Error', error.response?.data?.detail || error.message);
    },
  });

  // Delete OAuth config mutation
  const deleteOAuthMutation = useMutation({
    mutationFn: (id: number) => oauthApi.deleteConfig(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['oauth-configs'] });
      Alert.alert('Success', 'OAuth configuration deleted');
    },
    onError: (error: any) => {
      Alert.alert('Error', error.response?.data?.detail || error.message);
    },
  });

  useEffect(() => {
    loadLocalSettings();
  }, []);

  useEffect(() => {
    if (recoveryConfig) {
      setRecoveryMode(recoveryConfig.mode);
      setFixedEmail(recoveryConfig.fixed_email || '');
      setRecoveryDomain(recoveryConfig.domain || '');
    }
  }, [recoveryConfig]);

  const loadLocalSettings = async () => {
    try {
      const storedUrl = await AsyncStorage.getItem(API_URL_KEY);
      if (storedUrl) {
        setApiUrl(storedUrl);
        setApiBaseUrl(storedUrl);
      }
    } catch (e) {
      console.error('Failed to load settings');
    }
  };

  const saveApiUrl = async () => {
    try {
      await AsyncStorage.setItem(API_URL_KEY, apiUrl);
      setApiBaseUrl(apiUrl);
      Alert.alert('Success', 'API URL saved');
      queryClient.invalidateQueries();
    } catch (e) {
      Alert.alert('Error', 'Failed to save API URL');
    }
  };

  const testConnection = async () => {
    setIsTesting(true);
    try {
      const response = await fetch(apiUrl.replace('/api', '/health'));
      if (response.ok) {
        Alert.alert('Success', 'Connection successful!');
      } else {
        Alert.alert('Error', `Server returned status ${response.status}`);
      }
    } catch (e: any) {
      Alert.alert('Error', `Connection failed: ${e.message}`);
    } finally {
      setIsTesting(false);
    }
  };

  const saveRecoveryConfig = () => {
    if (recoveryMode === 'fixed') {
      if (!fixedEmail.trim() || !fixedEmail.includes('@')) {
        Alert.alert('Error', 'Please enter a valid email address');
        return;
      }
      updateRecoveryMutation.mutate({
        mode: 'fixed',
        fixedEmail: fixedEmail.trim(),
      });
    } else {
      if (!recoveryDomain.trim() || !recoveryDomain.includes('.')) {
        Alert.alert('Error', 'Please enter a valid domain (e.g., lab.shsai.fr)');
        return;
      }
      updateRecoveryMutation.mutate({
        mode: 'auto',
        domain: recoveryDomain.trim(),
      });
    }
  };

  const resetOAuthForm = () => {
    setEditingOAuth(null);
    setOauthName('');
    setOauthClientId('');
    setOauthClientSecret('');
    setOauthIsDefault(false);
  };

  const openOAuthModal = (config?: OAuthConfig) => {
    if (config) {
      setEditingOAuth(config);
      setOauthName(config.name);
      setOauthClientId(config.client_id);
      setOauthClientSecret(''); // Don't show existing secret
      setOauthIsDefault(config.is_default);
    } else {
      resetOAuthForm();
    }
    setShowOAuthModal(true);
  };

  const handleSaveOAuth = () => {
    if (!oauthName.trim()) {
      Alert.alert('Error', 'Name is required');
      return;
    }
    if (!oauthClientId.trim()) {
      Alert.alert('Error', 'Client ID is required');
      return;
    }
    if (!editingOAuth && !oauthClientSecret.trim()) {
      Alert.alert('Error', 'Client Secret is required');
      return;
    }

    if (editingOAuth) {
      const updateData: Partial<OAuthConfigCreate> = {
        name: oauthName.trim(),
        client_id: oauthClientId.trim(),
        is_default: oauthIsDefault,
      };
      if (oauthClientSecret.trim()) {
        updateData.client_secret = oauthClientSecret.trim();
      }
      updateOAuthMutation.mutate({ id: editingOAuth.id, data: updateData });
    } else {
      createOAuthMutation.mutate({
        name: oauthName.trim(),
        client_id: oauthClientId.trim(),
        client_secret: oauthClientSecret.trim(),
        is_default: oauthIsDefault,
      });
    }
  };

  const handleDeleteOAuth = (config: OAuthConfig) => {
    Alert.alert(
      'Delete OAuth Config',
      `Are you sure you want to delete "${config.name}"?${config.channels_count > 0 ? `\n\nWarning: ${config.channels_count} channel(s) are using this config.` : ''}`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deleteOAuthMutation.mutate(config.id),
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container}>
      {/* Server Configuration */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Ionicons name="server-outline" size={22} color="#3b82f6" />
          <Text style={styles.sectionTitle}>Server Configuration</Text>
        </View>

        <Text style={styles.label}>API Base URL</Text>
        <TextInput
          style={styles.input}
          value={apiUrl}
          onChangeText={setApiUrl}
          placeholder="http://192.168.1.100:8001/api"
          placeholderTextColor="#6b7280"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
        />
        <Text style={styles.hint}>
          The IP address of your server running the Lab backend
        </Text>

        <View style={styles.buttons}>
          <TouchableOpacity
            style={styles.testButton}
            onPress={testConnection}
            disabled={isTesting}
          >
            {isTesting ? (
              <ActivityIndicator size="small" color="#60a5fa" />
            ) : (
              <>
                <Ionicons name="wifi" size={18} color="#60a5fa" />
                <Text style={styles.testButtonText}>Test</Text>
              </>
            )}
          </TouchableOpacity>
          <TouchableOpacity style={styles.saveSmallButton} onPress={saveApiUrl}>
            <Ionicons name="save" size={18} color="#22c55e" />
            <Text style={styles.saveSmallButtonText}>Save</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* OAuth Configurations */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Ionicons name="key-outline" size={22} color="#8b5cf6" />
          <Text style={styles.sectionTitle}>OAuth Configurations</Text>
        </View>

        <Text style={styles.hint}>
          Configure Google Cloud OAuth credentials for YouTube API access.
          Create a project at console.cloud.google.com
        </Text>

        {loadingOAuth ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator size="small" color="#6b7280" />
            <Text style={styles.loadingText}>Loading OAuth configs...</Text>
          </View>
        ) : (
          <>
            {oauthConfigs?.configs.map((config) => (
              <View key={config.id} style={styles.oauthCard}>
                <View style={styles.oauthCardHeader}>
                  <View style={styles.oauthCardTitle}>
                    <Ionicons
                      name={config.is_default ? 'star' : 'star-outline'}
                      size={16}
                      color={config.is_default ? '#f59e0b' : '#6b7280'}
                    />
                    <Text style={styles.oauthName}>{config.name}</Text>
                    {config.is_default && (
                      <View style={styles.defaultBadge}>
                        <Text style={styles.defaultBadgeText}>Default</Text>
                      </View>
                    )}
                  </View>
                  <View style={styles.oauthCardActions}>
                    <TouchableOpacity
                      style={styles.oauthCardAction}
                      onPress={() => openOAuthModal(config)}
                    >
                      <Ionicons name="pencil" size={18} color="#60a5fa" />
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.oauthCardAction}
                      onPress={() => handleDeleteOAuth(config)}
                    >
                      <Ionicons name="trash" size={18} color="#ef4444" />
                    </TouchableOpacity>
                  </View>
                </View>
                <Text style={styles.oauthClientId} numberOfLines={1}>
                  {config.client_id}
                </Text>
                <Text style={styles.oauthChannels}>
                  {config.channels_count} channel{config.channels_count !== 1 ? 's' : ''} connected
                </Text>
              </View>
            ))}

            {(!oauthConfigs || oauthConfigs.configs.length === 0) && (
              <View style={styles.emptyOAuth}>
                <Ionicons name="key-outline" size={40} color="#374151" />
                <Text style={styles.emptyOAuthText}>No OAuth configs</Text>
                <Text style={styles.emptyOAuthHint}>
                  Add your Google Cloud OAuth credentials to use YouTube API
                </Text>
              </View>
            )}

            <TouchableOpacity
              style={styles.addOAuthButton}
              onPress={() => openOAuthModal()}
            >
              <Ionicons name="add-circle" size={20} color="#8b5cf6" />
              <Text style={styles.addOAuthButtonText}>Add OAuth Config</Text>
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* Recovery Email Configuration */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Ionicons name="mail-outline" size={22} color="#f59e0b" />
          <Text style={styles.sectionTitle}>Recovery Email</Text>
        </View>

        <Text style={styles.label}>Mode</Text>
        <View style={styles.modeSelector}>
          <TouchableOpacity
            style={[
              styles.modeOption,
              recoveryMode === 'fixed' && styles.modeOptionSelected,
            ]}
            onPress={() => setRecoveryMode('fixed')}
          >
            <Ionicons
              name="mail"
              size={18}
              color={recoveryMode === 'fixed' ? '#fff' : '#9ca3af'}
            />
            <Text
              style={[
                styles.modeOptionText,
                recoveryMode === 'fixed' && styles.modeOptionTextSelected,
              ]}
            >
              Fixed Email
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.modeOption,
              recoveryMode === 'auto' && styles.modeOptionSelected,
            ]}
            onPress={() => setRecoveryMode('auto')}
          >
            <Ionicons
              name="at"
              size={18}
              color={recoveryMode === 'auto' ? '#fff' : '#9ca3af'}
            />
            <Text
              style={[
                styles.modeOptionText,
                recoveryMode === 'auto' && styles.modeOptionTextSelected,
              ]}
            >
              Auto (per account)
            </Text>
          </TouchableOpacity>
        </View>

        {recoveryMode === 'fixed' ? (
          <>
            <Text style={styles.label}>Recovery Email Address</Text>
            <View style={styles.inputRow}>
              <TextInput
                style={[styles.input, styles.inputFlex]}
                value={fixedEmail}
                onChangeText={setFixedEmail}
                placeholder="recovery@lab.shsai.fr"
                placeholderTextColor="#6b7280"
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="email-address"
              />
              <TouchableOpacity
                style={styles.inputButton}
                onPress={saveRecoveryConfig}
                disabled={updateRecoveryMutation.isPending}
              >
                {updateRecoveryMutation.isPending ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Ionicons name="save" size={20} color="#fff" />
                )}
              </TouchableOpacity>
            </View>
            <Text style={styles.hint}>
              This single email will be used as recovery for ALL Google accounts.
            </Text>
          </>
        ) : (
          <>
            <Text style={styles.label}>Email Domain</Text>
            <View style={styles.inputRow}>
              <TextInput
                style={[styles.input, styles.inputFlex]}
                value={recoveryDomain}
                onChangeText={setRecoveryDomain}
                placeholder="lab.shsai.fr"
                placeholderTextColor="#6b7280"
                autoCapitalize="none"
                autoCorrect={false}
              />
              <TouchableOpacity
                style={styles.inputButton}
                onPress={saveRecoveryConfig}
                disabled={updateRecoveryMutation.isPending}
              >
                {updateRecoveryMutation.isPending ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Ionicons name="save" size={20} color="#fff" />
                )}
              </TouchableOpacity>
            </View>
            <Text style={styles.hint}>
              Each account will have its own recovery email: username@{recoveryDomain || 'domain.com'}
            </Text>
          </>
        )}

        {recoveryConfig && (
          <View style={styles.currentConfig}>
            <Ionicons name="information-circle" size={16} color="#60a5fa" />
            <Text style={styles.currentConfigText}>
              Current: {recoveryConfig.mode === 'fixed'
                ? `Fixed (${recoveryConfig.fixed_email})`
                : `Auto (@${recoveryConfig.domain})`}
            </Text>
          </View>
        )}
      </View>

      {/* About */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Ionicons name="information-circle-outline" size={22} color="#6b7280" />
          <Text style={styles.sectionTitle}>About</Text>
        </View>

        <View style={styles.aboutItem}>
          <Text style={styles.aboutLabel}>Version</Text>
          <Text style={styles.aboutValue}>2.0.0</Text>
        </View>
        <View style={styles.aboutItem}>
          <Text style={styles.aboutLabel}>App</Text>
          <Text style={styles.aboutValue}>Lab Account Manager</Text>
        </View>
        <View style={styles.aboutItem}>
          <Text style={styles.aboutLabel}>Features</Text>
          <Text style={styles.aboutValue}>Google, YouTube, TikTok, Mail</Text>
        </View>
      </View>

      <View style={styles.footer} />

      {/* OAuth Modal */}
      <Modal
        visible={showOAuthModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowOAuthModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                {editingOAuth ? 'Edit OAuth Config' : 'New OAuth Config'}
              </Text>
              <TouchableOpacity onPress={() => setShowOAuthModal(false)}>
                <Ionicons name="close" size={24} color="#9ca3af" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalScroll}>
              <Text style={styles.modalLabel}>Name</Text>
              <TextInput
                style={styles.modalInput}
                value={oauthName}
                onChangeText={setOauthName}
                placeholder="Lab, Production, etc."
                placeholderTextColor="#6b7280"
              />

              <Text style={styles.modalLabel}>Client ID</Text>
              <TextInput
                style={styles.modalInput}
                value={oauthClientId}
                onChangeText={setOauthClientId}
                placeholder="xxxxx.apps.googleusercontent.com"
                placeholderTextColor="#6b7280"
                autoCapitalize="none"
                autoCorrect={false}
              />

              <Text style={styles.modalLabel}>
                Client Secret {editingOAuth && '(leave empty to keep current)'}
              </Text>
              <TextInput
                style={styles.modalInput}
                value={oauthClientSecret}
                onChangeText={setOauthClientSecret}
                placeholder="GOCSPX-xxxxx"
                placeholderTextColor="#6b7280"
                autoCapitalize="none"
                autoCorrect={false}
                secureTextEntry
              />

              <TouchableOpacity
                style={styles.checkboxRow}
                onPress={() => setOauthIsDefault(!oauthIsDefault)}
              >
                <Ionicons
                  name={oauthIsDefault ? 'checkbox' : 'square-outline'}
                  size={24}
                  color={oauthIsDefault ? '#8b5cf6' : '#6b7280'}
                />
                <Text style={styles.checkboxLabel}>Set as default</Text>
              </TouchableOpacity>

              <View style={styles.infoBox}>
                <Ionicons name="information-circle" size={20} color="#60a5fa" />
                <Text style={styles.infoText}>
                  Get these credentials from Google Cloud Console:{'\n'}
                  APIs & Services → Credentials → OAuth 2.0 Client IDs
                </Text>
              </View>
            </ScrollView>

            <TouchableOpacity
              style={[
                styles.saveButton,
                (createOAuthMutation.isPending || updateOAuthMutation.isPending) && styles.saveButtonDisabled,
              ]}
              onPress={handleSaveOAuth}
              disabled={createOAuthMutation.isPending || updateOAuthMutation.isPending}
            >
              {createOAuthMutation.isPending || updateOAuthMutation.isPending ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Ionicons name="save" size={20} color="#fff" />
                  <Text style={styles.saveButtonText}>
                    {editingOAuth ? 'Update' : 'Create'}
                  </Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  section: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#1f2937',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#9ca3af',
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    backgroundColor: '#1f2937',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#374151',
  },
  inputRow: {
    flexDirection: 'row',
    gap: 10,
  },
  inputFlex: {
    flex: 1,
  },
  inputButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 10,
    paddingHorizontal: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  hint: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 8,
    lineHeight: 18,
  },
  buttons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 16,
  },
  testButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
    backgroundColor: '#1f2937',
    borderWidth: 1,
    borderColor: '#60a5fa',
    minWidth: 90,
  },
  testButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#60a5fa',
  },
  saveSmallButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
    backgroundColor: '#1f2937',
    borderWidth: 1,
    borderColor: '#22c55e',
  },
  saveSmallButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#22c55e',
  },
  modeSelector: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 8,
  },
  modeOption: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    backgroundColor: '#1f2937',
    borderWidth: 1,
    borderColor: '#374151',
  },
  modeOptionSelected: {
    backgroundColor: '#f59e0b',
    borderColor: '#f59e0b',
  },
  modeOptionText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#9ca3af',
  },
  modeOptionTextSelected: {
    color: '#fff',
  },
  currentConfig: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 16,
    padding: 12,
    backgroundColor: '#1e3a5f',
    borderRadius: 8,
  },
  currentConfigText: {
    fontSize: 13,
    color: '#93c5fd',
    flex: 1,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 12,
  },
  loadingText: {
    fontSize: 13,
    color: '#6b7280',
  },
  // OAuth styles
  oauthCard: {
    backgroundColor: '#1f2937',
    borderRadius: 10,
    padding: 14,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  oauthCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  oauthCardTitle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  oauthName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  defaultBadge: {
    backgroundColor: '#f59e0b',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  defaultBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#fff',
  },
  oauthCardActions: {
    flexDirection: 'row',
    gap: 12,
  },
  oauthCardAction: {
    padding: 4,
  },
  oauthClientId: {
    fontSize: 12,
    color: '#6b7280',
    fontFamily: 'monospace',
  },
  oauthChannels: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 6,
  },
  emptyOAuth: {
    alignItems: 'center',
    padding: 24,
  },
  emptyOAuthText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6b7280',
    marginTop: 12,
  },
  emptyOAuthHint: {
    fontSize: 13,
    color: '#4b5563',
    marginTop: 4,
    textAlign: 'center',
  },
  addOAuthButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    marginTop: 16,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#8b5cf6',
    borderStyle: 'dashed',
  },
  addOAuthButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#8b5cf6',
  },
  aboutItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1f2937',
  },
  aboutLabel: {
    fontSize: 15,
    color: '#9ca3af',
  },
  aboutValue: {
    fontSize: 15,
    color: '#fff',
  },
  footer: {
    height: 40,
  },
  // Modal styles
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
    maxHeight: '85%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  modalScroll: {
    maxHeight: 400,
  },
  modalLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#9ca3af',
    marginBottom: 8,
    marginTop: 16,
  },
  modalInput: {
    backgroundColor: '#374151',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#fff',
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginTop: 20,
  },
  checkboxLabel: {
    fontSize: 15,
    color: '#fff',
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#1e3a5f',
    padding: 12,
    borderRadius: 10,
    marginTop: 20,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#93c5fd',
    lineHeight: 20,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#8b5cf6',
    borderRadius: 10,
    paddingVertical: 16,
    marginTop: 20,
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
