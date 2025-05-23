import axios from "axios";

export async function fetchModules() {
  const res = await axios.get("/api/modules");
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
