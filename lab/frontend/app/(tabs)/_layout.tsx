import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useMailStats } from '../../src/hooks/useMail';
import { View, Text, StyleSheet } from 'react-native';

function MailTabBadge() {
  const { data: stats } = useMailStats();
  const unread = stats?.unread_emails || 0;

  if (unread === 0) return null;

  return (
    <View style={styles.badge}>
      <Text style={styles.badgeText}>{unread > 99 ? '99+' : unread}</Text>
    </View>
  );
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#3b82f6',
        tabBarInactiveTintColor: '#6b7280',
        tabBarStyle: {
          backgroundColor: '#1f2937',
          borderTopColor: '#374151',
        },
        headerStyle: {
          backgroundColor: '#1f2937',
        },
        headerTintColor: '#fff',
        tabBarLabelStyle: {
          fontSize: 10,
        },
      }}
    >
      <Tabs.Screen
        name="google"
        options={{
          title: 'Google',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="logo-google" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="youtube"
        options={{
          title: 'YouTube',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="logo-youtube" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="tiktok"
        options={{
          title: 'TikTok',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="musical-notes" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="mail"
        options={{
          title: 'Mail',
          tabBarIcon: ({ color, size }) => (
            <View>
              <Ionicons name="mail-outline" size={size} color={color} />
              <MailTabBadge />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="browser"
        options={{
          title: 'Browser',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="desktop-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: 'Settings',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings-outline" size={size} color={color} />
          ),
        }}
      />
      {/* Hidden legacy tabs */}
      <Tabs.Screen
        name="index"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="aliases"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="automation"
        options={{
          href: null,
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  badge: {
    position: 'absolute',
    top: -5,
    right: -10,
    backgroundColor: '#ef4444',
    borderRadius: 10,
    minWidth: 18,
    height: 18,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  badgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
});
