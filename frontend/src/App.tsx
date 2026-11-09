import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { ResearchPage } from '@/pages/ResearchPage';
import { VideoProductionPage } from '@/pages/VideoProductionPage';
import { CharacterLibraryPage } from '@/pages/CharacterLibraryPage';
import { YouTubePage } from '@/pages/YouTubePage';
import { AnalyticsPage } from '@/pages/AnalyticsPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { PlaceholderPage } from '@/pages/PlaceholderPage';
import { useAuthStore } from '@/store/authStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30000 },
    mutations: { retry: 0 },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  const { isAuthenticated, fetchMe } = useAuthStore();

  useEffect(() => {
    if (localStorage.getItem('access_token') && !isAuthenticated) {
      fetchMe();
    }
  }, []);

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />} />
      <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="research" element={<ResearchPage />} />
        <Route path="ideas" element={<PlaceholderPage title="Video Ideas" icon="💡" description="Browse and manage all generated video ideas. Use the AI Research module to generate new ones." />} />
        <Route path="scripts" element={<PlaceholderPage title="Script Generator" icon="📝" description="Scripts are auto-generated during the production pipeline. Manual script editing coming soon." />} />
        <Route path="storyboards" element={<PlaceholderPage title="Storyboard Editor" icon="🎞️" description="Visual storyboard editor for reviewing and editing scenes before production." />} />
        <Route path="characters" element={<CharacterLibraryPage />} />
        <Route path="audio" element={<PlaceholderPage title="Audio Library" icon="🎵" description="Manage generated voiceovers, background music, and sound effects." />} />
        <Route path="production" element={<VideoProductionPage />} />
        <Route path="preview" element={<PlaceholderPage title="Video Preview" icon="▶️" description="Preview generated videos before approval. Available once production is complete." />} />
        <Route path="approval" element={<VideoProductionPage />} />
        <Route path="youtube" element={<YouTubePage />} />
        <Route path="calendar" element={<PlaceholderPage title="Publishing Calendar" icon="📅" description="Schedule and manage video publishing dates on YouTube." />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="api-config" element={<SettingsPage />} />
        <Route path="costs" element={<AnalyticsPage />} />
        <Route path="users" element={<PlaceholderPage title="User Management" icon="👥" description="Manage admin users, roles, and permissions." />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="audit-logs" element={<PlaceholderPage title="Audit Logs" icon="📋" description="View all system actions and audit trail." />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" />} />
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: '#ea580c',
            borderRadius: 8,
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          },
        }}
      >
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  );
}
