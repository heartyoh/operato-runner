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
import FileDownloadIcon from "@mui/icons-material/FileDownload";

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
  const [artifactUri, setArtifactUri] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  // 인라인 등록 상태
  const [inlineName, setInlineName] = useState("");
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
  const [artifactType, setArtifactType] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    if (!name || (!file && !artifactUri)) {
      setError(
        "모듈 이름과 소스(zip 파일 또는 git 링크) 중 하나를 입력하세요."
      );
      return;
    }
    if (file && artifactUri) {
      setError("zip 파일과 git 링크 중 하나만 입력하세요.");
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("env", env);
      formData.append("version", version);
      if (file) {
        formData.append("file", file);
      } else if (artifactUri) {
        formData.append("artifact_uri", artifactUri);
      }
      await axios.post("/api/modules", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSuccess(true);
      setName("");
      setEnv("venv");
      setVersion("0.1.0");
      setFile(null);
      setArtifactUri("");
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

  // 템플릿 다운로드 핸들러
  const handleDownloadTemplate = async () => {
    try {
      const res = await axios.get("/api/templates/module", {
        responseType: "blob",
        // 인증이 필요한 경우 아래 주석 해제 후 토큰 변수 사용
        // headers: { Authorization: `Bearer ${token}` }
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "module_template.zip");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert("다운로드 실패: " + (err?.message || "알 수 없는 오류"));
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box
        display="flex"
        alignItems="center"
        justifyContent="space-between"
        mb={2}
      >
        <Typography variant="h6" gutterBottom>
          모듈 업로드 / 인라인 등록
        </Typography>
        <Button
          variant="outlined"
          startIcon={<FileDownloadIcon />}
          onClick={handleDownloadTemplate}
        >
          템플릿 다운로드
        </Button>
      </Box>
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
            </TextField>
            <TextField
              label="버전"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              size="small"
            />
            {/* zip 파일 업로드 또는 git 링크 중 하나만 입력 */}
            <Button
              variant="contained"
              component="label"
              disabled={!!artifactUri}
            >
              파일 선택
              <input
                type="file"
                accept=".zip"
                hidden
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null);
                  if (e.target.files?.[0]) setArtifactUri("");
                }}
              />
            </Button>
            {file && <Typography>{file.name}</Typography>}
            <TextField
              label="Git 저장소 링크"
              value={artifactUri}
              onChange={(e) => {
                setArtifactUri(e.target.value);
                if (e.target.value) setFile(null);
              }}
              size="small"
              sx={{ minWidth: 260 }}
              placeholder="https://github.com/username/repo.git"
              disabled={!!file}
            />
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
