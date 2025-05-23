import React, { useState } from "react";
import { createModule, uploadModuleFile } from "../api";
import axios from "axios";
import {
  Box,
  Button,
  TextField,
  Typography,
  MenuItem,
  Paper,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
} from "@mui/material";

interface Props {
  onUploadSuccess?: () => void;
}

const ModuleUpload: React.FC<Props> = ({ onUploadSuccess }) => {
  const [tab, setTab] = useState(0); // 0: 파일 업로드, 1: 인라인 등록
  // 파일 업로드 상태
  const [name, setName] = useState("");
  const [env, setEnv] = useState("venv");
  const [version, setVersion] = useState("0.1.0");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  // 인라인 등록 상태
  const [inlineName, setInlineName] = useState("");
  const [inlineEnv, setInlineEnv] = useState("venv");
  const [inlineVersion, setInlineVersion] = useState("0.1.0");
  const [inlineCode, setInlineCode] = useState("");
  const [inlineDesc, setInlineDesc] = useState("");
  const [inlineLoading, setInlineLoading] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [inlineSuccess, setInlineSuccess] = useState(false);
  const [inlineInput, setInlineInput] = useState<string>(`{
  "x": 1,
  "y": 2
}`);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    if (!name || !file) {
      setError("모듈 이름과 파일을 모두 입력하세요.");
      return;
    }
    setLoading(true);
    try {
      // 1. 모듈 메타데이터 등록
      const res = await createModule({ name, env, version });
      const moduleId =
        res.data.id || res.data.module_id || res.data.name || name;
      // 2. 파일 업로드
      await uploadModuleFile(moduleId, file);
      setSuccess(true);
      setName("");
      setEnv("venv");
      setVersion("0.1.0");
      setFile(null);
      if (onUploadSuccess) onUploadSuccess();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 인라인 등록 핸들러 (FormData로 /api/modules에 전송, axios 사용)
  const handleInlineSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setInlineError(null);
    setInlineSuccess(false);
    if (!inlineName || !inlineCode) {
      setInlineError("모듈 이름과 코드를 모두 입력하세요.");
      return;
    }
    setInlineLoading(true);
    try {
      const formData = new FormData();
      formData.append("name", inlineName.trim());
      formData.append("env", "inline");
      formData.append("version", inlineVersion);
      formData.append("code", inlineCode);
      formData.append("description", inlineDesc);
      formData.append("input", inlineInput);
      // tags 등 추가 필드 필요시 formData.append("tags", ...)
      await axios.post("/api/modules", formData);
      setInlineSuccess(true);
      setInlineName("");
      setInlineVersion("0.1.0");
      setInlineCode("");
      setInlineDesc("");
      setInlineInput(`{
  "x": 1,
  "y": 2
}`);
      if (onUploadSuccess) onUploadSuccess();
    } catch (err: any) {
      setInlineError(err?.response?.data?.detail || err.message);
    } finally {
      setInlineLoading(false);
    }
  };

  const handleFileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    if (!name || !file) {
      setError("모듈 이름과 파일을 모두 입력하세요.");
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("name", name.trim());
      formData.append("env", env);
      formData.append("version", version);
      formData.append("file", file);
      // ... existing code ...
    } catch (err: any) {
      // ... existing code ...
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        모듈 업로드 / 인라인 등록
      </Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="파일 업로드" />
        <Tab label="인라인 코드 등록" />
      </Tabs>
      {tab === 0 && (
        <form onSubmit={handleSubmit}>
          <Box display="flex" gap={2} flexWrap="wrap" alignItems="center">
            <TextField
              label="이름"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              size="small"
            />
            <TextField
              label="환경"
              select
              value={env}
              onChange={(e) => setEnv(e.target.value)}
              size="small"
            >
              <MenuItem value="venv">venv</MenuItem>
              <MenuItem value="conda">conda</MenuItem>
              <MenuItem value="docker">docker</MenuItem>
            </TextField>
            <TextField
              label="버전"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              size="small"
            />
            <Button variant="contained" component="label">
              파일 선택
              <input
                type="file"
                hidden
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </Button>
            {file && <Typography>{file.name}</Typography>}
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={loading}
            >
              업로드
            </Button>
          </Box>
        </form>
      )}
      {tab === 0 && loading && <CircularProgress sx={{ mt: 2 }} />}
      {tab === 0 && error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      {tab === 0 && success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          업로드 성공!
        </Alert>
      )}
      {tab === 1 && (
        <form onSubmit={handleInlineSubmit}>
          <Box display="flex" gap={2} flexWrap="wrap" alignItems="center">
            <TextField
              label="이름"
              value={inlineName}
              onChange={(e) => setInlineName(e.target.value)}
              required
              size="small"
            />
            <TextField
              label="환경"
              value="inline"
              InputProps={{ readOnly: true }}
              size="small"
              sx={{ width: 120 }}
            />
            <TextField
              label="버전"
              value={inlineVersion}
              onChange={(e) => setInlineVersion(e.target.value)}
              size="small"
            />
            <TextField
              label="설명"
              value={inlineDesc}
              onChange={(e) => setInlineDesc(e.target.value)}
              size="small"
              sx={{ minWidth: 200 }}
            />
          </Box>
          <TextField
            label="input 예시 (JSON)"
            value={inlineInput}
            onChange={(e) => setInlineInput(e.target.value)}
            fullWidth
            margin="normal"
            multiline
            minRows={3}
            placeholder={`{
  "x": 1,
  "y": 2
}`}
            helperText="실행 시 input 파라미터로 전달됩니다. 코드에서 input['x'] 등으로 바로 사용하세요."
          />
          <TextField
            label="코드"
            value={inlineCode}
            onChange={(e) => setInlineCode(e.target.value)}
            fullWidth
            margin="normal"
            multiline
            minRows={8}
            placeholder="여기에 파이썬 코드를 입력하세요"
            required
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={inlineLoading}
            sx={{ mt: 2 }}
          >
            인라인 등록
          </Button>
        </form>
      )}
      {tab === 1 && inlineLoading && <CircularProgress sx={{ mt: 2 }} />}
      {tab === 1 && inlineError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {inlineError}
        </Alert>
      )}
      {tab === 1 && inlineSuccess && (
        <Alert severity="success" sx={{ mt: 2 }}>
          인라인 등록 성공!
        </Alert>
      )}
    </Paper>
  );
};

export default ModuleUpload;
