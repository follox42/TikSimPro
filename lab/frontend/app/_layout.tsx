import { Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { setApiBaseUrl } from '../src/api/client';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      refetchInterval: 30000,
    },
  },
});

export default function RootLayout() {
  useEffect(() => {
    // Load saved API URL on app start
    const loadApiUrl = async () => {
      const stored = await AsyncStorage.getItem('lab_api_url');
      if (stored) {
        setApiBaseUrl(stored);
      }
    };
    loadApiUrl();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <View style={{ flex: 1, backgroundColor: '#111827' }}>
        <StatusBar style="light" />
        <Stack
          screenOptions={{
            headerStyle: {
              backgroundColor: '#1f2937',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
            contentStyle: {
              backgroundColor: '#111827',
            },
          }}
        >
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="email/[id]" options={{ title: 'Email' }} />
        </Stack>
      </View>
    </QueryClientProvider>
  );
}
