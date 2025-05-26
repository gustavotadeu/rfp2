import React from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import LoginPage from './features/auth/LoginPage';
import DashboardLayout from './components/layout/DashboardLayout';
import RFPListPage from './features/rfps/RFPListPage';
import RFPDetailPage from './features/rfps/RFPDetailPage';
import VendorsListPage from './features/vendors/VendorsListPage';
import ProfilePage from './features/users/ProfilePage';
import UsersAdminPage from './features/users/UsersAdminPage';
import ProvidersPage from './features/admin/ProvidersPage';
import { useAuth } from './hooks/useAuth';

function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}> {/* Rotas protegidas */}
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<RFPListPage />} />
          <Route path="rfps/:id" element={<RFPDetailPage />} />
          <Route path="fornecedores" element={<VendorsListPage />} />
          <Route path="perfil" element={<ProfilePage />} />
          <Route path="usuarios" element={<UsersAdminPage />} />
          <Route path="admin/config/providers" element={<ProvidersPage />} />
          {/* Outras rotas: propostas, usuários, etc */}
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

export default App;
