import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import ModuleList from "./components/ModuleList";
import ModuleUpload from "./components/ModuleUpload";
import ModuleDetail from "./pages/ModuleDetail";
import Layout from "./components/Layout";
import ErrorLogViewer from "./pages/ErrorLogViewer";

const AppRouter: React.FC = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="modules" element={<ModuleList />} />
        <Route path="modules/upload" element={<ModuleUpload />} />
        <Route path="modules/:name" element={<ModuleDetail />} />
        <Route path="admin/error-logs" element={<ErrorLogViewer />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  </BrowserRouter>
);

export default AppRouter;
