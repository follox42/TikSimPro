import axios from 'axios';

// ============== CONFIGURATION ==============

// API Base URL - Change this to your server IP
const API_BASE_URL = __DEV__
  ? 'http://192.168.1.100:8001/api'
  : 'https://your-production-server.com/api';

// VNC URL - Direct access to Selenium VNC
export const VNC_BASE_URL = __DEV__
  ? 'http://192.168.1.100:7901'
  : 'https://your-production-server.com:7901';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request/Response logging
api.interceptors.request.use((config) => {
  console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.params || config.data || '');
  return config;
});

api.interceptors.response.use(
  (response) => {
    console.log(`[API] ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`[API] ERROR ${error.config?.url}:`, error.response?.data || error.message);
    return Promise.reject(error);
  }
);


// ============== ENUMS ==============

export type AccountStatus = 'pending' | 'active' | 'expired' | 'error' | 'disabled';
export type AccountType = 'google' | 'tiktok';

// Legacy
export type Platform = 'tiktok' | 'youtube';


// ============== SETTINGS TYPES ==============

export interface Setting {
  key: string;
  value: string | null;
  updated_at: string;
}


// ============== GOOGLE ACCOUNT TYPES ==============

export interface GoogleAccount {
  id: number;
  email: string;
  password: string | null;
  recovery_email: string | null;
  first_name: string | null;
  last_name: string | null;
  status: AccountStatus;
  status_message: string | null;
  avatar_url: string | null;
  created_at: string;
  last_login_at: string | null;
  youtube_channels_count: number;
  has_cookies: boolean;
  cookies_expires_at: string | null;
}

export interface GoogleAccountList {
  accounts: GoogleAccount[];
  total: number;
}

export interface GoogleSignupResponse {
  account_id: number;
  email: string;
  recovery_email: string;
  password: string;
  first_name: string;
  last_name: string;
  status: string;
  message: string;
  current_step: string;
}


// ============== YOUTUBE CHANNEL TYPES ==============

export interface YouTubeChannel {
  id: number;
  google_account_id: number;
  google_email: string | null;
  channel_id: string | null;
  channel_name: string | null;
  handle: string | null;
  description: string | null;
  thumbnail_url: string | null;
  subscriber_count: number;
  video_count: number;
  view_count: number;
  created_at: string;
  channel_created_at: string | null;
  has_oauth: boolean;
}

export interface YouTubeChannelList {
  channels: YouTubeChannel[];
  total: number;
}

export interface YouTubeVideo {
  id: string;
  title: string;
  description: string;
  published_at: string;
  thumbnail: string;
}


// ============== TIKTOK ACCOUNT TYPES ==============

export interface TikTokAccount {
  id: number;
  email: string | null;
  password: string | null;
  username: string | null;
  display_name: string | null;
  status: AccountStatus;
  status_message: string | null;
  avatar_url: string | null;
  bio: string | null;
  follower_count: number;
  following_count: number;
  likes_count: number;
  created_at: string;
  last_login_at: string | null;
  has_cookies: boolean;
  cookies_expires_at: string | null;
}

export interface TikTokAccountList {
  accounts: TikTokAccount[];
  total: number;
}

export interface TikTokSignupResponse {
  account_id: number;
  email: string;
  password: string;
  status: string;
  message: string;
}


// ============== COOKIE TYPES ==============

export interface CookieInfo {
  id: number;
  account_type: AccountType;
  account_id: number;
  domain: string | null;
  created_at: string;
  expires_at: string | null;
  cookies_count: number;
}


// ============== BROWSER STATE ==============

export interface BrowserState {
  account_id: number;
  has_session: boolean;
  current_url: string | null;
  screenshot: string | null;
}


// ============== MAIL TYPES ==============

export interface EmailAlias {
  id: number;
  alias: string;
  description: string | null;
  created_at: string;
  is_active: boolean;
  email_count: number;
}

export interface EmailSummary {
  id: number;
  mail_from: string;
  subject: string | null;
  received_at: string;
  is_read: boolean;
  is_starred: boolean;
  alias_prefix: string | null;
}

export interface EmailDetail extends EmailSummary {
  rcpt_to: string;
  date: string | null;
  body_text: string | null;
  body_html: string | null;
}

export interface EmailList {
  emails: EmailSummary[];
  total: number;
  unread: number;
}

export interface MailStats {
  total_emails: number;
  unread_emails: number;
  total_aliases: number;
  emails_today: number;
}


// ============== SETTINGS TYPES ==============

export interface RecoveryEmailConfig {
  mode: 'fixed' | 'auto';
  fixed_email: string;
  domain: string;
}


// ============== SETTINGS API ==============

export const settingsApi = {
  list: async (): Promise<Setting[]> => {
    const response = await api.get('/settings');
    return response.data;
  },

  get: async (key: string): Promise<Setting> => {
    const response = await api.get(`/settings/${key}`);
    return response.data;
  },

  update: async (key: string, value: string | null): Promise<Setting> => {
    const response = await api.put(`/settings/${key}`, { value });
    return response.data;
  },

  // Recovery email configuration
  getRecoveryConfig: async (): Promise<RecoveryEmailConfig> => {
    const response = await api.get('/settings/recovery-email/config');
    return response.data;
  },

  setRecoveryConfig: async (
    mode: 'fixed' | 'auto',
    fixedEmail?: string,
    domain?: string
  ): Promise<RecoveryEmailConfig> => {
    const params = new URLSearchParams({ mode });
    if (fixedEmail) params.append('fixed_email', fixedEmail);
    if (domain) params.append('domain', domain);
    const response = await api.put(`/settings/recovery-email/config?${params}`);
    return response.data;
  },

  // Legacy - kept for backward compatibility
  getRecoveryDomain: async (): Promise<string> => {
    const config = await settingsApi.getRecoveryConfig();
    return config.domain;
  },

  setRecoveryDomain: async (domain: string): Promise<string> => {
    const config = await settingsApi.setRecoveryConfig('auto', undefined, domain);
    return config.domain;
  },
};


// ============== OAUTH CONFIG TYPES ==============

export interface OAuthConfig {
  id: number;
  name: string;
  description: string | null;
  client_id: string;
  client_secret_masked: string;
  redirect_uri: string | null;
  is_default: boolean;
  channels_count: number;
  created_at: string;
  updated_at: string;
}

export interface OAuthConfigCreate {
  name: string;
  description?: string;
  client_id: string;
  client_secret: string;
  redirect_uri?: string;
  is_default?: boolean;
}

export interface OAuthConfigList {
  configs: OAuthConfig[];
  total: number;
}


// ============== OAUTH API ==============

export const oauthApi = {
  // List OAuth configs
  listConfigs: async (): Promise<OAuthConfigList> => {
    const response = await api.get('/oauth/configs');
    return response.data;
  },

  // Get single config
  getConfig: async (id: number): Promise<OAuthConfig> => {
    const response = await api.get(`/oauth/configs/${id}`);
    return response.data;
  },

  // Create config
  createConfig: async (data: OAuthConfigCreate): Promise<OAuthConfig> => {
    const response = await api.post('/oauth/configs', data);
    return response.data;
  },

  // Update config
  updateConfig: async (id: number, data: Partial<OAuthConfigCreate>): Promise<OAuthConfig> => {
    const response = await api.put(`/oauth/configs/${id}`, data);
    return response.data;
  },

  // Delete config
  deleteConfig: async (id: number): Promise<void> => {
    await api.delete(`/oauth/configs/${id}`);
  },

  // Start OAuth authorization for a channel
  startAuthorization: async (channelId: number, oauthConfigId?: number): Promise<{
    auth_url: string;
    state: string;
    oauth_config: string;
    channel: string;
  }> => {
    const params = oauthConfigId ? `?oauth_config_id=${oauthConfigId}` : '';
    const response = await api.get(`/oauth/authorize/${channelId}${params}`);
    return response.data;
  },

  // Save OAuth token from native auth (Expo AuthSession)
  saveToken: async (channelId: number, oauthConfigId: number, tokenData: {
    access_token: string;
    refresh_token?: string;
    expires_in?: number;
    scope?: string;
  }): Promise<{ status: string }> => {
    const response = await api.post(`/oauth/tokens/${channelId}`, {
      oauth_config_id: oauthConfigId,
      ...tokenData,
    });
    return response.data;
  },

  // Revoke token
  revokeToken: async (channelId: number): Promise<void> => {
    await api.delete(`/oauth/tokens/${channelId}`);
  },

  // YouTube API operations
  getChannelInfo: async (channelId: number): Promise<any> => {
    const response = await api.get(`/oauth/channels/${channelId}/info`);
    return response.data;
  },

  listVideos: async (channelId: number, maxResults = 50): Promise<{ videos: any[]; count: number }> => {
    const response = await api.get(`/oauth/channels/${channelId}/videos?max_results=${maxResults}`);
    return response.data;
  },

  uploadVideo: async (channelId: number, formData: FormData): Promise<any> => {
    const response = await api.post(`/oauth/channels/${channelId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000, // 10 minutes for upload
    });
    return response.data;
  },

  deleteVideo: async (channelId: number, videoId: string): Promise<void> => {
    await api.delete(`/oauth/channels/${channelId}/videos/${videoId}`);
  },
};


// ============== GOOGLE ACCOUNTS API ==============

export const googleApi = {
  // List accounts
  list: async (params?: { status?: AccountStatus }): Promise<GoogleAccountList> => {
    const response = await api.get('/google/accounts', { params });
    return response.data;
  },

  // Get single account
  get: async (id: number): Promise<GoogleAccount> => {
    const response = await api.get(`/google/accounts/${id}`);
    return response.data;
  },

  // Delete account
  delete: async (id: number): Promise<void> => {
    await api.delete(`/google/accounts/${id}`);
  },

  // Get cookies info
  getCookies: async (id: number): Promise<CookieInfo[]> => {
    const response = await api.get(`/google/accounts/${id}/cookies`);
    return response.data;
  },

  // Start signup
  startSignup: async (emailPrefix?: string): Promise<GoogleSignupResponse> => {
    const response = await api.post('/google/accounts/signup', { email_prefix: emailPrefix });
    return response.data;
  },

  // Signup flow steps
  signupNext: async (id: number): Promise<{ status: string; current_step: string; message: string }> => {
    const response = await api.post(`/google/accounts/${id}/next`);
    return response.data;
  },

  signupBirthday: async (id: number, month: number, day: number, year: number, gender?: string): Promise<any> => {
    const params = new URLSearchParams({ month: String(month), day: String(day), year: String(year) });
    if (gender) params.append('gender', gender);
    const response = await api.post(`/google/accounts/${id}/birthday?${params}`);
    return response.data;
  },

  signupUsername: async (id: number, username: string): Promise<any> => {
    const response = await api.post(`/google/accounts/${id}/username?username=${encodeURIComponent(username)}`);
    return response.data;
  },

  signupPassword: async (id: number, password: string): Promise<any> => {
    const response = await api.post(`/google/accounts/${id}/password?password=${encodeURIComponent(password)}`);
    return response.data;
  },

  signupRecoveryEmail: async (id: number): Promise<{ status: string; recovery_email?: string }> => {
    const response = await api.post(`/google/accounts/${id}/recovery-email`);
    return response.data;
  },

  signupPhone: async (id: number, phone: string): Promise<any> => {
    const response = await api.post(`/google/accounts/${id}/phone?phone=${encodeURIComponent(phone)}`);
    return response.data;
  },

  signupVerify: async (id: number, code: string): Promise<any> => {
    const response = await api.post(`/google/accounts/${id}/verify?code=${encodeURIComponent(code)}`);
    return response.data;
  },

  signupTerms: async (id: number): Promise<any> => {
    const response = await api.post(`/google/accounts/${id}/terms`);
    return response.data;
  },

  signupFinalize: async (id: number): Promise<{ status: string; email?: string; cookies_count?: number }> => {
    const response = await api.post(`/google/accounts/${id}/finalize`);
    return response.data;
  },

  getSignupStep: async (id: number): Promise<{ current_step: string; screenshot: string | null; current_url: string | null }> => {
    const response = await api.get(`/google/accounts/${id}/step`);
    return response.data;
  },

  // Browser management
  getBrowserState: async (id: number): Promise<BrowserState> => {
    const response = await api.get(`/google/browser/${id}`);
    return response.data;
  },

  closeBrowser: async (id: number): Promise<{ status: string }> => {
    const response = await api.post(`/google/browser/${id}/close`);
    return response.data;
  },

  listSessions: async (): Promise<{ sessions: any[]; count: number }> => {
    const response = await api.get('/google/sessions');
    return response.data;
  },
};


// ============== YOUTUBE CHANNELS API ==============

export const youtubeChannelsApi = {
  // List channels
  list: async (params?: { google_account_id?: number }): Promise<YouTubeChannelList> => {
    const response = await api.get('/youtube/channels', { params });
    return response.data;
  },

  // Get single channel
  get: async (id: number): Promise<YouTubeChannel> => {
    const response = await api.get(`/youtube/channels/${id}`);
    return response.data;
  },

  // Create channel
  create: async (googleAccountId: number, channelName: string, handle?: string): Promise<YouTubeChannel> => {
    const response = await api.post('/youtube/channels', {
      google_account_id: googleAccountId,
      channel_name: channelName,
      handle,
    });
    return response.data;
  },

  // Delete channel
  delete: async (id: number): Promise<void> => {
    await api.delete(`/youtube/channels/${id}`);
  },

  // OAuth
  startOAuth: async (channelId: number): Promise<{ auth_url: string; state: string }> => {
    const response = await api.get(`/youtube/channels/${channelId}/oauth/start`);
    return response.data;
  },

  // Channel info from API
  getChannelInfo: async (channelId: number): Promise<any> => {
    const response = await api.get(`/youtube/channels/${channelId}/info`);
    return response.data;
  },

  // Videos
  listVideos: async (channelId: number, maxResults?: number): Promise<{ videos: YouTubeVideo[] }> => {
    const params = maxResults ? `?max_results=${maxResults}` : '';
    const response = await api.get(`/youtube/channels/${channelId}/videos${params}`);
    return response.data;
  },

  getVideo: async (channelId: number, videoId: string): Promise<YouTubeVideo> => {
    const response = await api.get(`/youtube/channels/${channelId}/videos/${videoId}`);
    return response.data;
  },

  deleteVideo: async (channelId: number, videoId: string): Promise<{ status: string }> => {
    const response = await api.delete(`/youtube/channels/${channelId}/videos/${videoId}`);
    return response.data;
  },

  // Browser
  getBrowserState: async (googleAccountId: number): Promise<BrowserState> => {
    const response = await api.get(`/youtube/browser/${googleAccountId}`);
    return response.data;
  },

  closeBrowser: async (googleAccountId: number): Promise<{ status: string }> => {
    const response = await api.post(`/youtube/browser/${googleAccountId}/close`);
    return response.data;
  },

  listSessions: async (): Promise<{ sessions: any[]; count: number }> => {
    const response = await api.get('/youtube/sessions');
    return response.data;
  },
};


// ============== TIKTOK ACCOUNTS API ==============

export const tiktokApi = {
  // List accounts
  list: async (params?: { status?: AccountStatus }): Promise<TikTokAccountList> => {
    const response = await api.get('/tiktok/accounts', { params });
    return response.data;
  },

  // Get single account
  get: async (id: number): Promise<TikTokAccount> => {
    const response = await api.get(`/tiktok/accounts/${id}`);
    return response.data;
  },

  // Delete account
  delete: async (id: number): Promise<void> => {
    await api.delete(`/tiktok/accounts/${id}`);
  },

  // Get cookies info
  getCookies: async (id: number): Promise<CookieInfo[]> => {
    const response = await api.get(`/tiktok/accounts/${id}/cookies`);
    return response.data;
  },

  // Start signup
  startSignup: async (emailPrefix: string): Promise<TikTokSignupResponse> => {
    const response = await api.post('/tiktok/accounts/signup', { email_prefix: emailPrefix });
    return response.data;
  },

  // Submit signup (after captcha)
  submitSignup: async (id: number): Promise<{ status: string; message: string }> => {
    const response = await api.post(`/tiktok/accounts/${id}/submit`);
    return response.data;
  },

  // Verify code
  verifyCode: async (id: number, code: string): Promise<{ status: string; message: string }> => {
    const response = await api.post(`/tiktok/accounts/${id}/verify`, { code });
    return response.data;
  },

  // Finalize account
  finalize: async (id: number): Promise<{ status: string; message: string; username?: string; cookies_count?: number }> => {
    const response = await api.post(`/tiktok/accounts/${id}/finalize`);
    return response.data;
  },

  // Browser management
  getBrowserState: async (id: number): Promise<BrowserState> => {
    const response = await api.get(`/tiktok/browser/${id}`);
    return response.data;
  },

  getScreenshot: async (id: number): Promise<{ screenshot: string }> => {
    const response = await api.get(`/tiktok/browser/${id}/screenshot`);
    return response.data;
  },

  closeBrowser: async (id: number): Promise<{ status: string }> => {
    const response = await api.post(`/tiktok/browser/${id}/close`);
    return response.data;
  },

  listSessions: async (): Promise<{ sessions: any[]; count: number }> => {
    const response = await api.get('/tiktok/sessions');
    return response.data;
  },
};


// ============== MAIL API ==============

export const mailApi = {
  // Aliases
  listAliases: async (): Promise<EmailAlias[]> => {
    const response = await api.get('/mail/aliases');
    return response.data;
  },

  createAlias: async (alias: string, description?: string): Promise<EmailAlias> => {
    const response = await api.post('/mail/aliases', { alias, description });
    return response.data;
  },

  deleteAlias: async (id: number): Promise<void> => {
    await api.delete(`/mail/aliases/${id}`);
  },

  // Emails
  listEmails: async (params?: {
    alias?: string;
    unread_only?: boolean;
    starred_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<EmailList> => {
    const response = await api.get('/mail/emails', { params });
    return response.data;
  },

  getEmail: async (id: number): Promise<EmailDetail> => {
    const response = await api.get(`/mail/emails/${id}`);
    return response.data;
  },

  toggleStar: async (id: number): Promise<{ is_starred: boolean }> => {
    const response = await api.post(`/mail/emails/${id}/star`);
    return response.data;
  },

  markRead: async (id: number, is_read: boolean = true): Promise<{ is_read: boolean }> => {
    const response = await api.post(`/mail/emails/${id}/read`, null, { params: { is_read } });
    return response.data;
  },

  deleteEmail: async (id: number): Promise<void> => {
    await api.delete(`/mail/emails/${id}`);
  },

  // Stats
  getStats: async (): Promise<MailStats> => {
    const response = await api.get('/mail/stats');
    return response.data;
  },

  markAllRead: async (alias?: string): Promise<void> => {
    await api.post('/mail/mark-all-read', null, { params: { alias } });
  },
};


// ============== AUTOMATION API ==============

export const automationApi = {
  getVncUrl: async (): Promise<{ vnc_url: string; vnc_direct: string; description: string }> => {
    const response = await api.get('/automation/vnc-url');
    return response.data;
  },
};


// ============== LEGACY API (backward compatibility) ==============

export interface AccountMetadata {
  real_username?: string;
  real_email?: string;
  display_name?: string;
  profile_url?: string;
  channel_id?: string;
  channel_name?: string;
  avatar_url?: string;
}

export interface Account {
  id: number;
  platform: Platform;
  username: string;
  email: string | null;
  password: string | null;
  status: AccountStatus;
  status_message: string | null;
  created_at: string;
  last_login_at: string | null;
  has_cookies: boolean;
  cookies_expires_at: string | null;
  metadata: AccountMetadata | null;
  credentials: Record<string, any> | null;
}

export interface AccountList {
  accounts: Account[];
  total: number;
}

export interface CreateAccount {
  platform: Platform;
  username: string;
  email?: string;
}

export interface LoginStatus {
  account_id: number;
  in_progress: boolean;
  message: string;
}

// Legacy Accounts API
export const accountsApi = {
  list: async (params?: { platform?: Platform; status?: AccountStatus }): Promise<AccountList> => {
    const response = await api.get('/accounts', { params });
    return response.data;
  },

  get: async (id: number): Promise<Account> => {
    const response = await api.get(`/accounts/${id}`);
    return response.data;
  },

  create: async (data: CreateAccount): Promise<Account> => {
    const response = await api.post('/accounts', data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/accounts/${id}`);
  },

  checkStatus: async (id: number): Promise<Account> => {
    const response = await api.post(`/accounts/${id}/check-status`);
    return response.data;
  },
};

// Legacy Auth API
export const authApi = {
  startLogin: async (accountId: number): Promise<{ account_id: number; message: string; status: string }> => {
    const response = await api.post('/auth/login', { account_id: accountId });
    return response.data;
  },

  getLoginStatus: async (accountId: number): Promise<LoginStatus> => {
    const response = await api.get(`/auth/login-status/${accountId}`);
    return response.data;
  },

  cancelLogin: async (accountId: number): Promise<{ message: string }> => {
    const response = await api.post(`/auth/cancel-login/${accountId}`);
    return response.data;
  },

  validateCookies: async (accountId: number): Promise<Account> => {
    const response = await api.post(`/auth/${accountId}/validate-cookies`);
    return response.data;
  },

  deleteCookies: async (accountId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/auth/${accountId}/cookies`);
    return response.data;
  },
};

// Legacy YouTube API
export const youtubeApi = {
  startGoogleSignup: async (emailPrefix?: string): Promise<any> => {
    const response = await api.post('/youtube/google/signup', { email_prefix: emailPrefix });
    return response.data;
  },

  signupNext: async (accountId: number): Promise<any> => {
    const response = await api.post(`/youtube/google/signup/${accountId}/next`);
    return response.data;
  },

  signupBirthday: async (accountId: number, month: number, day: number, year: number, gender?: string): Promise<any> => {
    const params = new URLSearchParams({ month: String(month), day: String(day), year: String(year) });
    if (gender) params.append('gender', gender);
    const response = await api.post(`/youtube/google/signup/${accountId}/birthday?${params}`);
    return response.data;
  },

  signupUsername: async (accountId: number, username: string): Promise<any> => {
    const response = await api.post(`/youtube/google/signup/${accountId}/username?username=${encodeURIComponent(username)}`);
    return response.data;
  },

  signupPassword: async (accountId: number, password: string): Promise<any> => {
    const response = await api.post(`/youtube/google/signup/${accountId}/password?password=${encodeURIComponent(password)}`);
    return response.data;
  },

  signupRecoveryEmail: async (accountId: number): Promise<any> => {
    const response = await api.post(`/youtube/google/signup/${accountId}/recovery-email`);
    return response.data;
  },

  signupPhone: async (accountId: number, phone: string): Promise<any> => {
    const response = await api.post(`/youtube/google/signup/${accountId}/phone?phone=${encodeURIComponent(phone)}`);
    return response.data;
  },

  signupVerify: async (accountId: number, code: string): Promise<any> => {
    const response = await api.post(`/youtube/google/signup/${accountId}/verify?code=${encodeURIComponent(code)}`);
    return response.data;
  },

  signupTerms: async (accountId: number): Promise<any> => {
    const response = await api.post(`/youtube/google/signup/${accountId}/terms`);
    return response.data;
  },

  getSignupStep: async (accountId: number): Promise<any> => {
    const response = await api.get(`/youtube/google/signup/${accountId}/step`);
    return response.data;
  },

  createChannel: async (accountId: number, channelName: string, handle?: string): Promise<any> => {
    const response = await api.post('/youtube/channel/create', {
      account_id: accountId,
      channel_name: channelName,
      handle,
    });
    return response.data;
  },

  startOAuth: async (accountId: number): Promise<{ auth_url: string; state: string }> => {
    const response = await api.get(`/youtube/oauth/start?account_id=${accountId}`);
    return response.data;
  },

  getChannel: async (accountId: number): Promise<any> => {
    const response = await api.get(`/youtube/channel/${accountId}`);
    return response.data;
  },

  listVideos: async (accountId: number, maxResults?: number): Promise<{ videos: YouTubeVideo[] }> => {
    const params = maxResults ? `?max_results=${maxResults}` : '';
    const response = await api.get(`/youtube/videos/${accountId}${params}`);
    return response.data;
  },

  getVideo: async (accountId: number, videoId: string): Promise<YouTubeVideo> => {
    const response = await api.get(`/youtube/video/${accountId}/${videoId}`);
    return response.data;
  },

  deleteVideo: async (accountId: number, videoId: string): Promise<{ status: string }> => {
    const response = await api.delete(`/youtube/video/${accountId}/${videoId}`);
    return response.data;
  },

  getBrowserState: async (accountId: number): Promise<BrowserState> => {
    const response = await api.get(`/youtube/browser/${accountId}`);
    return response.data;
  },

  closeBrowser: async (accountId: number): Promise<{ status: string }> => {
    const response = await api.post(`/youtube/browser/${accountId}/close`);
    return response.data;
  },

  listSessions: async (): Promise<{ sessions: any[]; count: number }> => {
    const response = await api.get('/youtube/sessions');
    return response.data;
  },

  finalizeGoogleAccount: async (accountId: number): Promise<any> => {
    const response = await api.post(`/youtube/google/signup/${accountId}/finalize`);
    return response.data;
  },
};


// ============== CONFIG ==============

export const setApiBaseUrl = (url: string) => {
  api.defaults.baseURL = url;
};
