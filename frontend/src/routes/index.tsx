import AuthGuard from '@/components/AuthGuard';
import ProtectedRoute from '@/components/ProtectedRoute';
import MainLayout from '@/layouts/MainLayout';
import { Box, CircularProgress, Typography } from '@mui/material';
import { Suspense, lazy } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

// Lazy load page components for better performance
const HomePage = lazy(() => import('@/pages/HomePage'));
const HaikuGeneratorPage = lazy(
  () => import('@/features/HaikuGenerator/HaikuGeneratorPage')
);
const LlmSettingsPage = lazy(() => import('@/features/LlmSettings/LlmSettingsPage'));
const ApiKeysPage = lazy(() => import('@/features/ApiKeys/ApiKeysPage'));
const ComponentShowcasePage = lazy(() => import('@/pages/ComponentShowcasePage'));
const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const ProfilePage = lazy(() => import('@/pages/ProfilePage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

// Admin pages
const AdminUsersPage = lazy(() => import('@/features/Admin/AdminUsersPage'));

// Improved loading fallback component
const LoadingFallback = () => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      width: '100%',
      gap: 2,
    }}
  >
    <CircularProgress size={40} />
    <Typography variant="body1" color="text.secondary">
      Loading...
    </Typography>
  </Box>
);

const AppRoutes = () => {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <AuthGuard>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            {/* Auth routes (outside main layout) */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Main application routes */}
            <Route path="/" element={<MainLayout />}>
              <Route index element={<HomePage />} />
              <Route path="haiku" element={<HaikuGeneratorPage />} />
              <Route path="components" element={<ComponentShowcasePage />} />

              {/* Admin-only routes */}
              <Route
                path="settings/llm"
                element={
                  <ProtectedRoute roles={['admin']}>
                    <LlmSettingsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="admin/users"
                element={
                  <ProtectedRoute roles={['admin']}>
                    <AdminUsersPage />
                  </ProtectedRoute>
                }
              />

              {/* Protected routes */}
              <Route
                path="profile"
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="settings/api-keys"
                element={
                  <ProtectedRoute>
                    <ApiKeysPage />
                  </ProtectedRoute>
                }
              />

              <Route path="404" element={<NotFoundPage />} />
              <Route path="*" element={<Navigate to="/404" replace />} />
            </Route>
          </Routes>
        </Suspense>
      </AuthGuard>
    </BrowserRouter>
  );
};

export default AppRoutes;
