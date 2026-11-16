import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Health } from './pages/Health';
import { Assets } from './pages/Assets';
import { Finances } from './pages/Finances';
import { Insights } from './pages/Insights';
import { Goals } from './pages/Goals';
import { Advisor } from './pages/Advisor';
import { Onboarding } from './pages/Onboarding';
import { Login } from './pages/Login';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="onboarding" element={<Onboarding />} />
            <Route path="health" element={<Health />} />
            <Route path="assets" element={<Assets />} />
            <Route path="finances" element={<Finances />} />
            <Route path="insights" element={<Insights />} />
            <Route path="goals" element={<Goals />} />
            <Route path="advisor" element={<Advisor />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
