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

// 파일 다운로드 처리 컴포넌트
const FileDownload: React.FC = () => {
  React.useEffect(() => {
    const fileId = window.location.pathname.split('/').pop();
    if (fileId) {
      // axios를 통해 백엔드에서 파일을 받아서 다운로드 처리
      const downloadFile = async () => {
        try {
          const response = await fetch(`/api/files/download/${fileId}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          });
          
          if (response.ok) {
            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            let filename = 'download';
            
            if (contentDisposition) {
              const match = contentDisposition.match(/filename="?(.+)"?/);
              if (match) filename = match[1];
            }
            
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
          } else {
            console.error('Download failed:', response.statusText);
          }
        } catch (error) {
          console.error('Download error:', error);
        }
      };
      
      downloadFile();
    }
  }, []);
  
  return <div>Downloading...</div>;
};

const AppRouter: React.FC = () => {
  return (
    <Routes>
      <Route path="/api/files/download/:fileId" element={<FileDownload />} />
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
