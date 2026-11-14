import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Health } from './pages/Health';
import { Assets } from './pages/Assets';
import { Finances } from './pages/Finances';
import { Goals } from './pages/Goals';
import { Advisor } from './pages/Advisor';
import { Onboarding } from './pages/Onboarding';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="onboarding" element={<Onboarding />} />
          <Route path="health" element={<Health />} />
          <Route path="assets" element={<Assets />} />
          <Route path="finances" element={<Finances />} />
          <Route path="goals" element={<Goals />} />
          <Route path="advisor" element={<Advisor />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
