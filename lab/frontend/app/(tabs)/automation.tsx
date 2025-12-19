import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Image,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { tiktokApi, youtubeApi, SignupResponse, GoogleSignupResponse, BrowserState } from '../../src/api/client';

type Platform = 'tiktok' | 'youtube';
type SignupStep = 'idle' | 'filling' | 'captcha' | 'verifying' | 'success' | 'error';

export default function AutomationScreen() {
  const [platform, setPlatform] = useState<Platform>('tiktok');
  const [emailPrefix, setEmailPrefix] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [step, setStep] = useState<SignupStep>('idle');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // TikTok state
  const [tiktokData, setTiktokData] = useState<SignupResponse | null>(null);

  // Google/YouTube state
  const [googleData, setGoogleData] = useState<GoogleSignupResponse | null>(null);
  const [currentGoogleStep, setCurrentGoogleStep] = useState('');
  const [channelName, setChannelName] = useState('');

  // Browser state
  const [browserState, setBrowserState] = useState<BrowserState | null>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-refresh screenshot
  useEffect(() => {
    const accountId = platform === 'tiktok' ? tiktokData?.account_id : googleData?.account_id;

    if (accountId && step !== 'idle' && step !== 'success' && step !== 'error') {
      refreshIntervalRef.current = setInterval(async () => {
        try {
          const state = platform === 'tiktok'
            ? await tiktokApi.getBrowserState(accountId)
            : await youtubeApi.getBrowserState(accountId);
          setBrowserState(state);

          // Update Google step
          if (platform === 'youtube' && googleData) {
            const stepInfo = await youtubeApi.getSignupStep(accountId);
            setCurrentGoogleStep(stepInfo.current_step);
          }
        } catch (e) {
          // Ignore errors during refresh
        }
      }, 2000);
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [tiktokData, googleData, step, platform]);

  // ==================== TikTok Functions ====================

  const startTiktokSignup = async () => {
    if (!emailPrefix.trim()) {
      Alert.alert('Error', 'Enter an email prefix');
      return;
    }

    setLoading(true);
    setMessage('Starting TikTok signup...');
    try {
      const result = await tiktokApi.startSignup(emailPrefix.trim());
      setTiktokData(result);
      setStep('filling');
      setMessage('Form filled. Complete the captcha then tap Submit.');

      const state = await tiktokApi.getBrowserState(result.account_id);
      setBrowserState(state);
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const submitTiktokForm = async () => {
    if (!tiktokData) return;

    setLoading(true);
    setMessage('Submitting form...');
    try {
      const result = await tiktokApi.submitSignup(tiktokData.account_id);
      if (result.status === 'submitted') {
        setStep('verifying');
        setMessage('Check your email for the verification code.');
      } else {
        setMessage(result.message);
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const verifyTiktokCode = async () => {
    if (!tiktokData || !verificationCode.trim()) return;

    setLoading(true);
    setMessage('Verifying code...');
    try {
      const result = await tiktokApi.verifyCode(tiktokData.account_id, verificationCode.trim());
      if (result.status === 'success') {
        setStep('success');
        setMessage('TikTok account created successfully!');
      } else {
        setMessage(result.message);
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ==================== Google/YouTube Functions ====================

  const startGoogleSignup = async () => {
    setLoading(true);
    setMessage('Starting Google account signup...');
    try {
      const result = await youtubeApi.startGoogleSignup(emailPrefix.trim() || undefined);
      setGoogleData(result);
      setCurrentGoogleStep(result.current_step);
      setStep('filling');
      setMessage(result.message);

      const state = await youtubeApi.getBrowserState(result.account_id);
      setBrowserState(state);
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const googleNext = async () => {
    if (!googleData) return;

    setLoading(true);
    try {
      const result = await youtubeApi.signupNext(googleData.account_id);
      setCurrentGoogleStep(result.current_step);
      setMessage(result.message);

      if (result.current_step === 'done') {
        setStep('success');
        setMessage('Google account created! Now create a YouTube channel.');
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const googleAcceptTerms = async () => {
    if (!googleData) return;

    setLoading(true);
    try {
      const result = await youtubeApi.signupTerms(googleData.account_id);
      setCurrentGoogleStep(result.current_step);
      setMessage(result.message);

      if (result.status === 'success' || result.current_step === 'done') {
        setStep('success');
        setMessage('Google account created! Now create a YouTube channel.');
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const createYouTubeChannel = async () => {
    if (!googleData || !channelName.trim()) {
      Alert.alert('Error', 'Enter a channel name');
      return;
    }

    setLoading(true);
    setMessage('Creating YouTube channel...');
    try {
      const result = await youtubeApi.createChannel(googleData.account_id, channelName.trim());
      if (result.status === 'success') {
        setMessage(`YouTube channel "${result.channel_name}" created!`);
      } else {
        setMessage(result.message);
      }
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ==================== Common Functions ====================

  const closeBrowser = async () => {
    const accountId = platform === 'tiktok' ? tiktokData?.account_id : googleData?.account_id;
    if (!accountId) return;

    try {
      if (platform === 'tiktok') {
        await tiktokApi.closeBrowser(accountId);
      } else {
        await youtubeApi.closeBrowser(accountId);
      }
    } catch (e) {
      // Ignore
    }
  };

  const reset = () => {
    closeBrowser();
    setStep('idle');
    setTiktokData(null);
    setGoogleData(null);
    setBrowserState(null);
    setEmailPrefix('');
    setVerificationCode('');
    setChannelName('');
    setCurrentGoogleStep('');
    setMessage('');
  };

  const refreshScreenshot = async () => {
    const accountId = platform === 'tiktok' ? tiktokData?.account_id : googleData?.account_id;
    if (!accountId) return;

    try {
      const state = platform === 'tiktok'
        ? await tiktokApi.getBrowserState(accountId)
        : await youtubeApi.getBrowserState(accountId);
      setBrowserState(state);
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Platform Selector */}
      <View style={styles.platformSelector}>
        <TouchableOpacity
          style={[styles.platformButton, platform === 'tiktok' && styles.platformButtonActive]}
          onPress={() => { setPlatform('tiktok'); reset(); }}
        >
          <Ionicons name="logo-tiktok" size={20} color={platform === 'tiktok' ? '#fff' : '#ec4899'} />
          <Text style={[styles.platformText, platform === 'tiktok' && styles.platformTextActive]}>TikTok</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.platformButton, platform === 'youtube' && styles.platformButtonActiveYT]}
          onPress={() => { setPlatform('youtube'); reset(); }}
        >
          <Ionicons name="logo-youtube" size={20} color={platform === 'youtube' ? '#fff' : '#ef4444'} />
          <Text style={[styles.platformText, platform === 'youtube' && styles.platformTextActive]}>YouTube</Text>
        </TouchableOpacity>
      </View>

      {/* Header */}
      <View style={styles.header}>
        {platform === 'tiktok' ? (
          <>
            <Ionicons name="logo-tiktok" size={32} color="#ec4899" />
            <Text style={styles.title}>TikTok Account Creator</Text>
          </>
        ) : (
          <>
            <Ionicons name="logo-google" size={32} color="#4285f4" />
            <Text style={styles.title}>Google/YouTube Creator</Text>
          </>
        )}
      </View>

      {/* Status Message */}
      {message ? (
        <View style={[styles.messageBox, step === 'error' && styles.errorBox, step === 'success' && styles.successBox]}>
          <Text style={styles.messageText}>{message}</Text>
        </View>
      ) : null}

      {/* Google Step Indicator */}
      {platform === 'youtube' && currentGoogleStep && step !== 'idle' && (
        <View style={styles.stepIndicator}>
          <Text style={styles.stepText}>Current step: {currentGoogleStep}</Text>
        </View>
      )}

      {/* Step 1: Enter email prefix (idle state) */}
      {step === 'idle' && (
        <View style={styles.section}>
          <Text style={styles.label}>
            {platform === 'tiktok' ? 'Email Prefix' : 'Gmail Username (optional)'}
          </Text>
          <TextInput
            style={styles.input}
            value={emailPrefix}
            onChangeText={setEmailPrefix}
            placeholder={platform === 'tiktok' ? 'myaccount' : 'Leave empty for random'}
            placeholderTextColor="#6b7280"
            autoCapitalize="none"
            autoCorrect={false}
          />
          {platform === 'tiktok' && (
            <Text style={styles.hint}>Will create: {emailPrefix || 'prefix'}@yourmail.domain</Text>
          )}

          <TouchableOpacity
            style={[styles.button, platform === 'youtube' && styles.buttonYT]}
            onPress={platform === 'tiktok' ? startTiktokSignup : startGoogleSignup}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="play" size={20} color="#fff" />
                <Text style={styles.buttonText}>Start Signup</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* Show credentials */}
      {(tiktokData || googleData) && step !== 'idle' && (
        <View style={styles.credentials}>
          {platform === 'tiktok' && tiktokData ? (
            <>
              <Text style={styles.credLabel}>Email:</Text>
              <Text style={styles.credValue}>{tiktokData.email}</Text>
              <Text style={styles.credLabel}>Password:</Text>
              <Text style={styles.credValue}>{tiktokData.password}</Text>
            </>
          ) : googleData ? (
            <>
              <Text style={styles.credLabel}>Name:</Text>
              <Text style={styles.credValue}>{googleData.first_name} {googleData.last_name}</Text>
              <Text style={styles.credLabel}>Email:</Text>
              <Text style={styles.credValue}>{googleData.email}</Text>
              <Text style={styles.credLabel}>Password:</Text>
              <Text style={styles.credValue}>{googleData.password}</Text>
            </>
          ) : null}
        </View>
      )}

      {/* Browser Screenshot */}
      {browserState?.screenshot && (
        <View style={styles.browserSection}>
          <View style={styles.browserHeader}>
            <Text style={styles.browserTitle}>Browser View</Text>
            <TouchableOpacity onPress={refreshScreenshot}>
              <Ionicons name="refresh" size={20} color="#9ca3af" />
            </TouchableOpacity>
          </View>
          <Image
            source={{ uri: `data:image/png;base64,${browserState.screenshot}` }}
            style={styles.screenshot}
            resizeMode="contain"
          />
          {browserState.current_url && (
            <Text style={styles.urlText} numberOfLines={1}>
              {browserState.current_url}
            </Text>
          )}
        </View>
      )}

      {/* TikTok: Submit after captcha */}
      {platform === 'tiktok' && step === 'filling' && (
        <View style={styles.section}>
          <Text style={styles.instructions}>
            Complete the captcha in the browser above, then tap Submit.
          </Text>
          <TouchableOpacity style={styles.button} onPress={submitTiktokForm} disabled={loading}>
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="checkmark" size={20} color="#fff" />
                <Text style={styles.buttonText}>Submit Form</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* TikTok: Enter verification code */}
      {platform === 'tiktok' && step === 'verifying' && (
        <View style={styles.section}>
          <Text style={styles.label}>Verification Code</Text>
          <TextInput
            style={styles.input}
            value={verificationCode}
            onChangeText={setVerificationCode}
            placeholder="123456"
            placeholderTextColor="#6b7280"
            keyboardType="number-pad"
            maxLength={6}
          />
          <Text style={styles.hint}>Check the Mail tab for your code</Text>

          <TouchableOpacity style={styles.button} onPress={verifyTiktokCode} disabled={loading}>
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="shield-checkmark" size={20} color="#fff" />
                <Text style={styles.buttonText}>Verify Code</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* Google: Navigation buttons */}
      {platform === 'youtube' && step === 'filling' && (
        <View style={styles.section}>
          <Text style={styles.instructions}>
            Follow the Google signup steps. Use Next to proceed, or Accept Terms when prompted.
          </Text>

          <View style={styles.buttonRow}>
            <TouchableOpacity
              style={[styles.button, styles.buttonYT, styles.buttonHalf]}
              onPress={googleNext}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Ionicons name="arrow-forward" size={20} color="#fff" />
                  <Text style={styles.buttonText}>Next</Text>
                </>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, styles.buttonGreen, styles.buttonHalf]}
              onPress={googleAcceptTerms}
              disabled={loading}
            >
              <Ionicons name="checkmark-done" size={20} color="#fff" />
              <Text style={styles.buttonText}>Accept Terms</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Success state */}
      {step === 'success' && (
        <View style={styles.section}>
          <View style={styles.successIcon}>
            <Ionicons name="checkmark-circle" size={64} color="#22c55e" />
          </View>
          <Text style={styles.successText}>
            {platform === 'tiktok' ? 'TikTok account created!' : 'Google account created!'}
          </Text>

          {/* YouTube channel creation after Google success */}
          {platform === 'youtube' && googleData && (
            <View style={styles.channelSection}>
              <Text style={styles.label}>Create YouTube Channel</Text>
              <TextInput
                style={styles.input}
                value={channelName}
                onChangeText={setChannelName}
                placeholder="My Channel Name"
                placeholderTextColor="#6b7280"
              />
              <TouchableOpacity
                style={[styles.button, styles.buttonYT]}
                onPress={createYouTubeChannel}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <>
                    <Ionicons name="logo-youtube" size={20} color="#fff" />
                    <Text style={styles.buttonText}>Create Channel</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          )}

          <TouchableOpacity style={[styles.button, styles.secondaryButton]} onPress={reset}>
            <Ionicons name="add" size={20} color="#3b82f6" />
            <Text style={[styles.buttonText, styles.secondaryButtonText]}>Create Another</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Error state */}
      {step === 'error' && (
        <View style={styles.section}>
          <TouchableOpacity style={[styles.button, styles.secondaryButton]} onPress={reset}>
            <Ionicons name="refresh" size={20} color="#3b82f6" />
            <Text style={[styles.buttonText, styles.secondaryButtonText]}>Try Again</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Cancel button */}
      {step !== 'idle' && step !== 'success' && step !== 'error' && (
        <TouchableOpacity style={styles.cancelButton} onPress={reset}>
          <Ionicons name="close" size={18} color="#ef4444" />
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>
      )}
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
  platformSelector: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  platformButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 10,
    backgroundColor: '#1f2937',
    borderWidth: 2,
    borderColor: '#374151',
  },
  platformButtonActive: {
    backgroundColor: '#ec4899',
    borderColor: '#ec4899',
  },
  platformButtonActiveYT: {
    backgroundColor: '#ef4444',
    borderColor: '#ef4444',
  },
  platformText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#9ca3af',
  },
  platformTextActive: {
    color: '#fff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 24,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  messageBox: {
    backgroundColor: '#1f2937',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    borderLeftWidth: 3,
    borderLeftColor: '#3b82f6',
  },
  errorBox: {
    borderLeftColor: '#ef4444',
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
  },
  successBox: {
    borderLeftColor: '#22c55e',
    backgroundColor: 'rgba(34, 197, 94, 0.1)',
  },
  messageText: {
    color: '#d1d5db',
    fontSize: 14,
  },
  stepIndicator: {
    backgroundColor: '#1e3a5f',
    borderRadius: 8,
    padding: 10,
    marginBottom: 16,
  },
  stepText: {
    color: '#60a5fa',
    fontSize: 13,
    fontWeight: '500',
  },
  section: {
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#9ca3af',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#1f2937',
    borderRadius: 8,
    padding: 14,
    fontSize: 16,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#374151',
  },
  hint: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 6,
    marginBottom: 16,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#ec4899',
    padding: 14,
    borderRadius: 10,
  },
  buttonYT: {
    backgroundColor: '#ef4444',
  },
  buttonGreen: {
    backgroundColor: '#22c55e',
  },
  buttonHalf: {
    flex: 1,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#3b82f6',
  },
  secondaryButtonText: {
    color: '#3b82f6',
  },
  credentials: {
    backgroundColor: '#1f2937',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  credLabel: {
    fontSize: 12,
    color: '#6b7280',
  },
  credValue: {
    fontSize: 14,
    color: '#fff',
    fontFamily: 'monospace',
    marginBottom: 8,
  },
  browserSection: {
    marginBottom: 16,
  },
  browserHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  browserTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#9ca3af',
  },
  screenshot: {
    width: '100%',
    height: 300,
    backgroundColor: '#000',
    borderRadius: 8,
  },
  urlText: {
    fontSize: 11,
    color: '#6b7280',
    marginTop: 4,
  },
  instructions: {
    fontSize: 14,
    color: '#d1d5db',
    marginBottom: 16,
    lineHeight: 20,
  },
  successIcon: {
    alignItems: 'center',
    marginBottom: 16,
  },
  successText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#22c55e',
    textAlign: 'center',
    marginBottom: 24,
  },
  channelSection: {
    backgroundColor: '#1f2937',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  cancelButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: 12,
  },
  cancelText: {
    color: '#ef4444',
    fontSize: 14,
  },
});
