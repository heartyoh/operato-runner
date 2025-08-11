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

let isRefreshing = false;
let refreshSubscribers: ((token: string | null) => void)[] = [];

function onRefreshed(token: string | null) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response &&
      error.response.status === 401 &&
      !originalRequest._retry
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshSubscribers.push((token) => {
            if (token) {
              originalRequest.headers["Authorization"] = `Bearer ${token}`;
              resolve(axios(originalRequest));
            } else {
              localStorage.removeItem("access_token");
              // 더 안정적인 리다이렉트를 위해 setTimeout 사용
              setTimeout(() => {
                window.location.href = "/login";
              }, 100);
              reject(error);
            }
          });
        });
      }
      originalRequest._retry = true;
      isRefreshing = true;
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) {
          throw new Error("No refresh token available");
        }

        const res = await axios.post("/auth/refresh", {
          refresh_token: refreshToken,
        });
        const newToken = res.data.access_token;
        if (newToken) {
          localStorage.setItem("access_token", newToken);
          axios.defaults.headers.common["Authorization"] = `Bearer ${newToken}`;
          onRefreshed(newToken);
          originalRequest.headers["Authorization"] = `Bearer ${newToken}`;
          return axios(originalRequest);
        } else {
          throw new Error("No access token in refresh response");
        }
      } catch (refreshError) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        onRefreshed(null); // 큐에 있는 요청들도 모두 실패 처리
        // 더 안정적인 리다이렉트를 위해 setTimeout 사용
        setTimeout(() => {
          window.location.href = "/login";
        }, 100);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  fetchModules,
  fetchExecutableModules,
  fetchModuleVersions,
  rollbackModule,
  activateModuleVersion,
  deactivateModuleVersion,
  fetchModuleHistory,
  fetchModuleDetail,
  createModule,
  fetchErrorLogs,
  downloadErrorLogs,
  login,
  deployModule,
  undeployModule,
  deleteModule,
  uploadModuleVersion,
  updateModuleInfo,
  getAuditLogs,
  downloadAuditLogs,
  getDbHealth,
  getValidationLogs,
  downloadValidationLogs,
  downloadFile,
  // 환경변수 관리 API
  getModuleEnvVars,
  addModuleEnvVar,
  updateModuleEnvVar,
  deleteModuleEnvVar,
  get: axios.get,
  post: axios.post,
  patch: axios.patch,
  delete: axios.delete,
};

async function fetchModules() {
  const res = await axios.get("/api/modules");
  return res.data;
}

async function fetchExecutableModules() {
  const res = await axios.get("/api/modules/executable");
  return res.data;
}

export async function fetchModuleVersions(name: string) {
  const res = await axios.get(`/api/modules/${name}/versions`);
  return res.data;
}

export async function rollbackModule(name: string, version: string) {
  const formData = new FormData();
  formData.append("target_version", version);
  const res = await axios.post(`/api/modules/${name}/rollback`, formData);
  return res.data;
}

export async function activateModuleVersion(name: string, version: string) {
  const formData = new FormData();
  formData.append("version", version);
  const res = await axios.post(`/api/modules/${name}/activate`, formData);
  return res.data;
}

export async function deactivateModuleVersion(name: string, version: string) {
  const res = await axios.post(`/api/modules/${name}/deactivate`);
  return res.data;
}

export async function fetchModuleHistory(name: string) {
  const res = await axios.get(`/api/modules/${name}/history`);
  return res.data;
}

export async function fetchModuleDetail(name: string) {
  const res = await axios.get(`/api/modules/${encodeURIComponent(name)}`);
  return res.data;
}

export async function createModule(data: {
  name: string;
  env: string;
  version: string;
}) {
  return axios.post("/api/modules", data);
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

  if (res.data.access_token) {
    localStorage.setItem("access_token", res.data.access_token);
  }

  // refresh_token도 localStorage에 저장 (쿠키에서 추출)
  const refreshToken = document.cookie
    .split("; ")
    .find((row) => row.startsWith("refresh_token="))
    ?.split("=")[1];

  if (refreshToken) {
    localStorage.setItem("refresh_token", refreshToken);
  }

  return res.data;
}

export async function deployModule(name: string) {
  const res = await axios.post(
    `/api/modules/${encodeURIComponent(name)}/deploy`
  );
  return res.data;
}

export async function undeployModule(name: string) {
  const res = await axios.delete(
    `/api/modules/${encodeURIComponent(name)}/deploy`
  );
  return res.data;
}

export async function deleteModule(name: string) {
  const res = await axios.delete(`/api/modules/${encodeURIComponent(name)}`);
  return res.data;
}

export async function uploadModuleVersion(name: string, formData: FormData) {
  const res = await axios.post(`/api/modules/${name}/versions`, formData);
  return res.data;
}

export async function updateModuleInfo(
  name: string,
  data: { description?: string; tags?: string; is_public?: boolean }
) {
  const formData = new FormData();
  if (data.description !== undefined)
    formData.append("description", data.description);
  if (data.tags !== undefined) formData.append("tags", data.tags);
  if (data.is_public !== undefined)
    formData.append("is_public", String(data.is_public));
  const res = await axios.patch(
    `/api/modules/${encodeURIComponent(name)}`,
    formData
  );
  return res.data;
}

export async function getAuditLogs(params: any) {
  const res = await axios.get("/api/audit/logs", { params });
  return res.data;
}

export async function downloadAuditLogs(params: any) {
  return axios.get("/api/audit/logs/download", {
    params,
    responseType: "blob",
  });
}

export async function getDbHealth() {
  const res = await axios.get("/api/health/db");
  return res.data;
}

export async function getValidationLogs(params: {
  module_name?: string;
  status?: string;
  from_date?: string;
  to_date?: string;
  limit?: number;
}) {
  const res = await axios.get("/api/logs/validation", { params });
  return res.data;
}

export async function downloadValidationLogs(params: {
  module_name?: string;
  status?: string;
  from_date?: string;
  to_date?: string;
}) {
  return axios.get("/api/logs/validation/download", {
    params,
    responseType: "blob",
  });
}

// 환경변수 관리 API
export async function getModuleEnvVars(name: string) {
  const res = await axios.get(`/api/modules/${name}/env-vars`);
  return res.data;
}

export async function addModuleEnvVar(
  name: string,
  key: string,
  value: string
) {
  const formData = new FormData();
  formData.append("key", key);
  formData.append("value", value);
  const res = await axios.post(`/api/modules/${name}/env-vars`, formData);
  return res.data;
}

export async function updateModuleEnvVar(
  name: string,
  key: string,
  value: string
) {
  const formData = new FormData();
  formData.append("value", value);
  const res = await axios.put(`/api/modules/${name}/env-vars/${key}`, formData);
  return res.data;
}

export async function deleteModuleEnvVar(name: string, key: string) {
  const res = await axios.delete(`/api/modules/${name}/env-vars/${key}`);
  return res.data;
}

export async function downloadFile(fileId: string, filename?: string) {
  const res = await axios.get(`/api/files/download/${fileId}`, {
    responseType: "blob",
  });
  
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename || "download";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

// 사용자 관리 API
export const listUsers = async (params?: any) => {
  const { data } = await api.get("/api/users", { params });
  return data;
};

export const createUser = async (userData: {
  username: string;
  email: string;
  password: string;
  roles?: string[];
  is_active?: boolean;
}) => {
  const { data } = await api.post("/api/users", userData);
  return data;
};

export const updateUser = async (
  userId: number,
  userData: { email?: string; is_active?: boolean; roles?: string[] }
) => {
  const { data } = await api.patch(`/api/users/${userId}`, userData);
  return data;
};

export const deleteUser = async (userId: number) => {
  await api.delete(`/api/users/${userId}`);
};
