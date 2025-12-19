/**
 * Native Google OAuth hook using Expo AuthSession
 *
 * This hook handles the OAuth 2.0 flow for YouTube API access
 * directly from the mobile app without needing a web callback.
 */

import { useCallback, useEffect, useState } from 'react';
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import { oauthApi, OAuthConfig } from '../api/client';

// Required for WebBrowser.maybeCompleteAuthSession()
WebBrowser.maybeCompleteAuthSession();

// YouTube API scopes
const YOUTUBE_SCOPES = [
  'https://www.googleapis.com/auth/youtube',
  'https://www.googleapis.com/auth/youtube.upload',
  'https://www.googleapis.com/auth/youtube.readonly',
  'https://www.googleapis.com/auth/youtube.force-ssl',
].join(' ');

// Google OAuth endpoints
const discovery = {
  authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenEndpoint: 'https://oauth2.googleapis.com/token',
  revocationEndpoint: 'https://oauth2.googleapis.com/revoke',
};

interface UseGoogleAuthOptions {
  channelId: number;
  oauthConfig?: OAuthConfig | null;
  onSuccess?: (tokenData: { access_token: string; refresh_token?: string }) => void;
  onError?: (error: Error) => void;
}

interface UseGoogleAuthReturn {
  isLoading: boolean;
  isAuthorizing: boolean;
  error: string | null;
  promptAsync: () => Promise<void>;
  reset: () => void;
}

export function useGoogleAuth({
  channelId,
  oauthConfig,
  onSuccess,
  onError,
}: UseGoogleAuthOptions): UseGoogleAuthReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate redirect URI for the app
  const redirectUri = AuthSession.makeRedirectUri({
    scheme: 'lab', // app scheme - should match app.json
    path: 'oauth/callback',
  });

  // Create auth request
  const [request, response, promptAsyncBase] = AuthSession.useAuthRequest(
    oauthConfig
      ? {
          clientId: oauthConfig.client_id,
          scopes: YOUTUBE_SCOPES.split(' '),
          redirectUri,
          responseType: AuthSession.ResponseType.Code,
          usePKCE: true,
          extraParams: {
            access_type: 'offline', // Get refresh token
            prompt: 'consent', // Force consent to get refresh token
          },
        }
      : null as any, // Null if no config
    discovery
  );

  // Handle auth response
  useEffect(() => {
    if (!response || !oauthConfig) return;

    const handleResponse = async () => {
      if (response.type === 'success') {
        setIsLoading(true);
        setError(null);

        try {
          // Exchange code for tokens
          const { code } = response.params;

          // Exchange the authorization code for tokens
          const tokenResponse = await AuthSession.exchangeCodeAsync(
            {
              clientId: oauthConfig.client_id,
              code,
              redirectUri,
              extraParams: {
                code_verifier: request?.codeVerifier || '',
              },
            },
            discovery
          );

          // Save token to backend
          await oauthApi.saveToken(channelId, oauthConfig.id, {
            access_token: tokenResponse.accessToken,
            refresh_token: tokenResponse.refreshToken || undefined,
            expires_in: tokenResponse.expiresIn || undefined,
            scope: tokenResponse.scope || undefined,
          });

          onSuccess?.({
            access_token: tokenResponse.accessToken,
            refresh_token: tokenResponse.refreshToken || undefined,
          });
        } catch (err) {
          const error = err as Error;
          setError(error.message);
          onError?.(error);
        } finally {
          setIsLoading(false);
          setIsAuthorizing(false);
        }
      } else if (response.type === 'error') {
        const errorMsg = response.params?.error_description || response.params?.error || 'OAuth failed';
        setError(errorMsg);
        setIsAuthorizing(false);
        onError?.(new Error(errorMsg));
      } else if (response.type === 'cancel' || response.type === 'dismiss') {
        setIsAuthorizing(false);
        setError('Authorization cancelled');
      }
    };

    handleResponse();
  }, [response, oauthConfig, channelId, redirectUri, request?.codeVerifier, onSuccess, onError]);

  const promptAsync = useCallback(async () => {
    if (!oauthConfig) {
      setError('No OAuth configuration available');
      return;
    }

    if (!request) {
      setError('Auth request not ready');
      return;
    }

    setError(null);
    setIsAuthorizing(true);

    try {
      await promptAsyncBase();
    } catch (err) {
      const error = err as Error;
      setError(error.message);
      setIsAuthorizing(false);
      onError?.(error);
    }
  }, [oauthConfig, request, promptAsyncBase, onError]);

  const reset = useCallback(() => {
    setError(null);
    setIsLoading(false);
    setIsAuthorizing(false);
  }, []);

  return {
    isLoading,
    isAuthorizing,
    error,
    promptAsync,
    reset,
  };
}

/**
 * Hook to get the default OAuth config
 */
export function useDefaultOAuthConfig() {
  const [config, setConfig] = useState<OAuthConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const result = await oauthApi.listConfigs();
        const defaultConfig = result.configs.find((c) => c.is_default) || result.configs[0] || null;
        setConfig(defaultConfig);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchConfig();
  }, []);

  return { config, isLoading, error };
}
