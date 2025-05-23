import axios from "axios";

// axios 인스턴스에 Authorization 헤더 자동 추가
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers = config.headers || {};
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

export async function fetchModules() {
  const res = await axios.get("/api/modules");
  return res.data;
}

export async function fetchModuleVersions(name: string) {
  const res = await axios.get(`/api/modules/${name}/versions`);
  return res.data;
}

export async function rollbackModule(name: string, version: string) {
  const res = await axios.post(`/api/modules/${name}/rollback`, { version });
  return res.data;
}

export async function activateModuleVersion(name: string, version: string) {
  const res = await axios.post(`/api/modules/${name}/activate`, { version });
  return res.data;
}

export async function deactivateModuleVersion(name: string, version: string) {
  const res = await axios.post(`/api/modules/${name}/deactivate`, { version });
  return res.data;
}

export async function fetchModuleHistory(name: string) {
  const res = await axios.get(`/api/modules/${name}/history`);
  return res.data;
}

export async function fetchModuleDetail(name: string) {
  const res = await axios.get(`/api/modules/${name}`);
  return res.data;
}

export async function createModule(data: {
  name: string;
  env: string;
  version: string;
}) {
  return axios.post("/api/modules", data);
}

export async function uploadModuleFile(moduleId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return axios.post(`/api/modules/${moduleId}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export async function fetchErrorLogs(params: any) {
  const res = await axios.get("/api/logs/errors", { params });
  return res.data;
}

export async function downloadErrorLogs(params: any) {
  return axios.get("/api/logs/errors/download", {
    params,
    responseType: "blob",
  });
}

export async function login(username: string, password: string) {
  const res = await axios.post("/auth/login", {
    username,
    password,
  });
  return res.data;
}

export {};
