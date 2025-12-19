import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  RefreshControl,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { WebView } from 'react-native-webview';
import { Ionicons } from '@expo/vector-icons';
import { tiktokApi, youtubeApi, automationApi, BrowserState, VNC_BASE_URL } from '../../src/api/client';

interface Session {
  account_id: number;
  type: 'tiktok' | 'google' | 'youtube';
  current_url: string | null;
  has_driver: boolean;
}

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

type ViewMode = 'screenshots' | 'vnc';

export default function BrowserScreen() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [browserState, setBrowserState] = useState<BrowserState | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('screenshots');
  const [vncLoading, setVncLoading] = useState(true);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const webViewRef = useRef<WebView>(null);

  // Load sessions
  const loadSessions = useCallback(async () => {
    try {
      const [tiktokRes, youtubeRes] = await Promise.all([
        tiktokApi.listSessions(),
        youtubeApi.listSessions(),
      ]);

      const allSessions: Session[] = [
        ...tiktokRes.sessions.map(s => ({ ...s, type: 'tiktok' as const })),
        ...youtubeRes.sessions.map(s => ({ ...s, type: s.type as 'google' | 'youtube' })),
      ];

      setSessions(allSessions);

      // Auto-select first session if none selected
      if (allSessions.length > 0 && !selectedSession) {
        setSelectedSession(allSessions[0].account_id);
      }
    } catch (e) {
      console.error('Failed to load sessions:', e);
    }
  }, [selectedSession]);

  // VNC URL with noVNC web client
  const vncUrl = `${VNC_BASE_URL}/?autoconnect=true&resize=scale`;

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Auto-refresh screenshot
  useEffect(() => {
    if (selectedSession && autoRefresh) {
      refreshIntervalRef.current = setInterval(async () => {
        try {
          const session = sessions.find(s => s.account_id === selectedSession);
          if (!session) return;

          let state: BrowserState;
          if (session.type === 'tiktok') {
            state = await tiktokApi.getBrowserState(selectedSession);
          } else {
            state = await youtubeApi.getBrowserState(selectedSession);
          }
          setBrowserState(state);
        } catch (e) {
          // Ignore
        }
      }, 1500);
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [selectedSession, autoRefresh, sessions]);

  // Load screenshot when session changes
  useEffect(() => {
    if (selectedSession) {
      loadScreenshot();
    }
  }, [selectedSession]);

  const loadScreenshot = async () => {
    if (!selectedSession) return;

    setLoading(true);
    try {
      const session = sessions.find(s => s.account_id === selectedSession);
      if (!session) return;

      let state: BrowserState;
      if (session.type === 'tiktok') {
        state = await tiktokApi.getBrowserState(selectedSession);
      } else {
        state = await youtubeApi.getBrowserState(selectedSession);
      }
      setBrowserState(state);
    } catch (e) {
      console.error('Failed to load screenshot:', e);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadSessions();
    if (selectedSession) {
      await loadScreenshot();
    }
    setRefreshing(false);
  };

  const closeSession = async (accountId: number) => {
    const session = sessions.find(s => s.account_id === accountId);
    if (!session) return;

    try {
      if (session.type === 'tiktok') {
        await tiktokApi.closeBrowser(accountId);
      } else {
        await youtubeApi.closeBrowser(accountId);
      }

      // Refresh sessions
      await loadSessions();

      if (selectedSession === accountId) {
        setSelectedSession(null);
        setBrowserState(null);
      }
    } catch (e) {
      console.error('Failed to close session:', e);
    }
  };

  const reloadVnc = () => {
    setVncLoading(true);
    webViewRef.current?.reload();
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'tiktok': return '#ec4899';
      case 'google': return '#4285f4';
      case 'youtube': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'tiktok': return 'logo-tiktok';
      case 'google': return 'logo-google';
      case 'youtube': return 'logo-youtube';
      default: return 'globe-outline';
    }
  };

  // Render VNC mode
  if (viewMode === 'vnc') {
    return (
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.headerBar}>
          <TouchableOpacity onPress={() => setViewMode('screenshots')} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>VNC Remote Control</Text>
          <TouchableOpacity onPress={reloadVnc} style={styles.refreshButton}>
            <Ionicons name="refresh" size={22} color="#9ca3af" />
          </TouchableOpacity>
        </View>

        {/* VNC WebView */}
        <View style={styles.vncContainer}>
          {vncLoading && (
            <View style={styles.vncLoading}>
              <ActivityIndicator size="large" color="#3b82f6" />
              <Text style={styles.vncLoadingText}>Connecting to VNC...</Text>
            </View>
          )}
          <WebView
            ref={webViewRef}
            source={{ uri: vncUrl }}
            style={styles.webview}
            javaScriptEnabled={true}
            domStorageEnabled={true}
            startInLoadingState={true}
            scalesPageToFit={true}
            onLoadStart={() => setVncLoading(true)}
            onLoadEnd={() => setVncLoading(false)}
            onError={(e) => console.log('WebView error:', e.nativeEvent)}
            allowsFullscreenVideo={true}
            mediaPlaybackRequiresUserAction={false}
          />
        </View>

        {/* VNC Help */}
        <View style={styles.vncHelp}>
          <Ionicons name="information-circle-outline" size={16} color="#6b7280" />
          <Text style={styles.vncHelpText}>
            Full mouse & keyboard control. Rotate device for better view.
          </Text>
        </View>
      </View>
    );
  }

  // Render screenshots mode
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3b82f6" />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="desktop-outline" size={28} color="#3b82f6" />
        <Text style={styles.title}>Browser Sessions</Text>
        <TouchableOpacity onPress={onRefresh} style={styles.refreshButton}>
          <Ionicons name="refresh" size={22} color="#9ca3af" />
        </TouchableOpacity>
      </View>

      {/* VNC Button */}
      <TouchableOpacity style={styles.vncButton} onPress={() => setViewMode('vnc')}>
        <Ionicons name="tv-outline" size={20} color="#fff" />
        <Text style={styles.vncButtonText}>Open VNC Remote Control</Text>
      </TouchableOpacity>

      {/* Sessions List */}
      <View style={styles.sessionsSection}>
        <Text style={styles.sectionTitle}>Active Sessions ({sessions.length})</Text>

        {sessions.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="browsers-outline" size={48} color="#374151" />
            <Text style={styles.emptyText}>No active browser sessions</Text>
            <Text style={styles.emptyHint}>Start a signup from the Create tab</Text>
          </View>
        ) : (
          <View style={styles.sessionsList}>
            {sessions.map(session => (
              <TouchableOpacity
                key={`${session.type}-${session.account_id}`}
                style={[
                  styles.sessionCard,
                  selectedSession === session.account_id && styles.sessionCardSelected
                ]}
                onPress={() => setSelectedSession(session.account_id)}
              >
                <View style={styles.sessionInfo}>
                  <Ionicons
                    name={getTypeIcon(session.type) as any}
                    size={24}
                    color={getTypeColor(session.type)}
                  />
                  <View style={styles.sessionDetails}>
                    <Text style={styles.sessionType}>
                      {session.type.charAt(0).toUpperCase() + session.type.slice(1)} #{session.account_id}
                    </Text>
                    <Text style={styles.sessionUrl} numberOfLines={1}>
                      {session.current_url || 'No URL'}
                    </Text>
                  </View>
                </View>
                <TouchableOpacity
                  style={styles.closeButton}
                  onPress={() => closeSession(session.account_id)}
                >
                  <Ionicons name="close-circle" size={24} color="#ef4444" />
                </TouchableOpacity>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>

      {/* Screenshot Viewer */}
      {selectedSession && (
        <View style={styles.viewerSection}>
          <View style={styles.viewerHeader}>
            <Text style={styles.sectionTitle}>Live View</Text>
            <TouchableOpacity
              style={[styles.autoRefreshButton, autoRefresh && styles.autoRefreshActive]}
              onPress={() => setAutoRefresh(!autoRefresh)}
            >
              <Ionicons
                name={autoRefresh ? 'pause' : 'play'}
                size={16}
                color={autoRefresh ? '#22c55e' : '#9ca3af'}
              />
              <Text style={[styles.autoRefreshText, autoRefresh && styles.autoRefreshTextActive]}>
                {autoRefresh ? 'Auto' : 'Paused'}
              </Text>
            </TouchableOpacity>
          </View>

          {loading && !browserState?.screenshot ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#3b82f6" />
            </View>
          ) : browserState?.screenshot ? (
            <View style={styles.screenshotContainer}>
              <Image
                source={{ uri: `data:image/png;base64,${browserState.screenshot}` }}
                style={styles.screenshot}
                resizeMode="contain"
              />
              {browserState.current_url && (
                <View style={styles.urlBar}>
                  <Ionicons name="globe-outline" size={14} color="#6b7280" />
                  <Text style={styles.urlText} numberOfLines={1}>
                    {browserState.current_url}
                  </Text>
                </View>
              )}
            </View>
          ) : (
            <View style={styles.noScreenshot}>
              <Ionicons name="image-outline" size={48} color="#374151" />
              <Text style={styles.noScreenshotText}>No screenshot available</Text>
            </View>
          )}

          {/* Manual refresh button */}
          <TouchableOpacity style={styles.manualRefreshButton} onPress={loadScreenshot}>
            <Ionicons name="refresh" size={18} color="#3b82f6" />
            <Text style={styles.manualRefreshText}>Refresh Screenshot</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Help Text */}
      <View style={styles.helpSection}>
        <Ionicons name="information-circle-outline" size={18} color="#6b7280" />
        <Text style={styles.helpText}>
          Screenshots update automatically every 1.5s. For full keyboard/mouse control, open the VNC viewer.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 12,
    backgroundColor: '#1f2937',
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  headerTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginLeft: 12,
  },
  backButton: {
    padding: 4,
  },
  title: {
    flex: 1,
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  refreshButton: {
    padding: 8,
  },
  // VNC Styles
  vncContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  webview: {
    flex: 1,
    backgroundColor: '#000',
  },
  vncLoading: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#111827',
    zIndex: 10,
  },
  vncLoadingText: {
    color: '#9ca3af',
    marginTop: 12,
    fontSize: 14,
  },
  vncHelp: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    backgroundColor: '#1f2937',
  },
  vncHelpText: {
    flex: 1,
    fontSize: 12,
    color: '#6b7280',
  },
  vncButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#7c3aed',
    padding: 14,
    borderRadius: 10,
    marginBottom: 20,
  },
  vncButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  sessionsSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#9ca3af',
    marginBottom: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
    backgroundColor: '#1f2937',
    borderRadius: 12,
  },
  emptyText: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 12,
  },
  emptyHint: {
    fontSize: 13,
    color: '#4b5563',
    marginTop: 4,
  },
  sessionsList: {
    gap: 10,
  },
  sessionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#1f2937',
    padding: 14,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  sessionCardSelected: {
    borderColor: '#3b82f6',
  },
  sessionInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  sessionDetails: {
    flex: 1,
  },
  sessionType: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
  sessionUrl: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  closeButton: {
    padding: 4,
  },
  viewerSection: {
    marginBottom: 20,
  },
  viewerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  autoRefreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#1f2937',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  autoRefreshActive: {
    backgroundColor: 'rgba(34, 197, 94, 0.15)',
  },
  autoRefreshText: {
    fontSize: 13,
    color: '#9ca3af',
  },
  autoRefreshTextActive: {
    color: '#22c55e',
  },
  loadingContainer: {
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1f2937',
    borderRadius: 12,
  },
  screenshotContainer: {
    backgroundColor: '#000',
    borderRadius: 12,
    overflow: 'hidden',
  },
  screenshot: {
    width: '100%',
    height: 350,
  },
  urlBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#1f2937',
    padding: 10,
  },
  urlText: {
    flex: 1,
    fontSize: 12,
    color: '#9ca3af',
  },
  noScreenshot: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1f2937',
    borderRadius: 12,
  },
  noScreenshotText: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 12,
  },
  manualRefreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 12,
    padding: 10,
  },
  manualRefreshText: {
    fontSize: 14,
    color: '#3b82f6',
  },
  helpSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: '#1e293b',
    padding: 12,
    borderRadius: 8,
  },
  helpText: {
    flex: 1,
    fontSize: 12,
    color: '#6b7280',
    lineHeight: 18,
  },
});
