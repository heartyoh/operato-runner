import React, { useState } from "react";
import { createModule, uploadModuleFile } from "../api";
import {
  Box,
  Button,
  TextField,
  Typography,
  MenuItem,
  Paper,
  CircularProgress,
  Alert,
} from "@mui/material";

interface Props {
  onUploadSuccess?: () => void;
}

const ModuleUpload: React.FC<Props> = ({ onUploadSuccess }) => {
  const [name, setName] = useState("");
  const [env, setEnv] = useState("venv");
  const [version, setVersion] = useState("0.1.0");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

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
        res.data.id || res.data.module_id || res.data.name || name; // id 반환 방식 유연하게 처리
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

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        모듈 업로드
      </Typography>
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
      {loading && <CircularProgress sx={{ mt: 2 }} />}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          업로드 성공!
        </Alert>
      )}
    </Paper>
  );
};

export default ModuleUpload;
