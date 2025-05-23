import axios from "axios";

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

export {};
