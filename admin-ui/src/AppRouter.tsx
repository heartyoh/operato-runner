import * as React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import ModuleList from "./components/ModuleList";
import ModuleUpload from "./components/ModuleUpload";
import ModuleDetail from "./pages/ModuleDetail";
import Layout from "./components/Layout";
import ErrorLogViewer from "./pages/ErrorLogViewer";
import AuditLogViewer from "./pages/AuditLogViewer";
import LoginPage from "./pages/LoginPage";
import UserManagement from "./pages/UserManagement";

function ProtectedRoute({
  children,
}: {
  children: React.ReactElement;
}): React.ReactElement | null {
  const token = localStorage.getItem("access_token");
  return token ? children : <Navigate to="/login" replace />;
}

const AppRouter: React.FC = () => (
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/" element={<Navigate to="/admin/dashboard" replace />} />
    <Route
      path="/admin"
      element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }
    >
      <Route index element={<Navigate to="dashboard" replace />} />
      <Route path="dashboard" element={<Dashboard />} />
      <Route path="modules" element={<ModuleList />} />
      <Route path="modules/upload" element={<ModuleUpload />} />
      <Route path="modules/:name" element={<ModuleDetail />} />
      <Route path="error-logs" element={<ErrorLogViewer />} />
      <Route path="audit-logs" element={<AuditLogViewer />} />
      <Route path="users" element={<UserManagement />} />
    </Route>
    <Route path="*" element={<Navigate to="/admin/dashboard" replace />} />
  </Routes>
);

export default AppRouter;
