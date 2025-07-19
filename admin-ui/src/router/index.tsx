import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "../components/Layout";
import LoginPage from "../pages/LoginPage";
import Dashboard from "../pages/Dashboard";
import ModuleList from "../pages/ModuleList";
import ModuleDetail from "../pages/ModuleDetail";
import ModuleUpload from "../pages/ModuleUpload";
import UserManagement from "../pages/UserManagement";
import ErrorLogViewer from "../pages/ErrorLogViewer";
import AuditLogViewer from "../pages/AuditLogViewer";
import ValidationLogViewer from "../pages/ValidationLogViewer";
import Profile from "../pages/Profile";
import ExecutableModules from "../pages/ExecutableModules";

// 인증 보호 컴포넌트
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const token = localStorage.getItem("access_token");

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const AppRouter: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
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
        <Route path="modules/:name" element={<ModuleDetail />} />
        <Route
          path="modules/upload"
          element={<ModuleUpload onUploadSuccess={() => {}} />}
        />
        <Route path="executable" element={<ExecutableModules />} />
        <Route path="users" element={<UserManagement />} />
        <Route path="error-logs" element={<ErrorLogViewer />} />
        <Route path="audit-logs" element={<AuditLogViewer />} />
        <Route path="validation-logs" element={<ValidationLogViewer />} />
        <Route path="profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/admin/dashboard" replace />} />
    </Routes>
  );
};

export default AppRouter;
