import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Health } from './pages/Health';
import { Assets } from './pages/Assets';
import { Finances } from './pages/Finances';
import { Goals } from './pages/Goals';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="health" element={<Health />} />
          <Route path="assets" element={<Assets />} />
          <Route path="finances" element={<Finances />} />
          <Route path="goals" element={<Goals />} />
          <Route
            path="advisor"
            element={
              <div className="p-8 text-center text-slate-500 bg-white rounded-xl border border-slate-200">
                Explainable Advisor will be implemented in Phase 4.
              </div>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
