import * as React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import ModuleList from "./components/ModuleList";
import ModuleUpload from "./components/ModuleUpload";
import ModuleDetail from "./pages/ModuleDetail";
import Layout from "./components/Layout";
import ErrorLogViewer from "./pages/ErrorLogViewer";
import LoginPage from "./pages/LoginPage";

function ProtectedRoute({
  children,
}: {
  children: React.ReactElement;
}): React.ReactElement | null {
  const token = localStorage.getItem("access_token");
  return token ? children : <Navigate to="/login" replace />;
}

const AppRouter: React.FC = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="modules" element={<ModuleList />} />
        <Route path="modules/upload" element={<ModuleUpload />} />
        <Route path="modules/:name" element={<ModuleDetail />} />
        <Route path="admin/error-logs" element={<ErrorLogViewer />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  </BrowserRouter>
);

export default AppRouter;
