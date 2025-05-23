import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Divider,
  Box,
  Chip,
  Stack,
} from "@mui/material";
import { fetchModuleDetail } from "../api";

const formatDate = (iso: string) =>
  iso ? iso.replace("T", " ").slice(0, 19) : "";

const ModuleDetail: React.FC = () => {
  const { name } = useParams();
  const [module, setModule] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!name) return;
    setLoading(true);
    fetchModuleDetail(name)
      .then(setModule)
      .catch((err) => setError(err?.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, [name]);

  return (
    <Paper sx={{ p: 4, mb: 3, maxWidth: 500, mx: "auto" }}>
      <Typography variant="h5" gutterBottom>
        모듈 상세 정보
      </Typography>
      <Divider sx={{ mb: 2 }} />
      {loading && <CircularProgress sx={{ mt: 2 }} />}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      {module && (
        <>
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2">이름</Typography>
            <Typography>{module.name}</Typography>
          </Box>
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2">환경</Typography>
            <Typography>{module.env}</Typography>
          </Box>
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2">버전</Typography>
            <Typography>{module.version}</Typography>
          </Box>
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2">태그</Typography>
            <Stack direction="row" spacing={1}>
              {module.tags?.map((tag: string) => (
                <Chip key={tag} label={tag} size="small" />
              ))}
            </Stack>
          </Box>
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2">생성일</Typography>
            <Typography>{formatDate(module.created_at)}</Typography>
          </Box>
        </>
      )}
      {!loading && !error && !module && (
        <Typography>모듈 정보를 찾을 수 없습니다.</Typography>
      )}
    </Paper>
  );
};

export default ModuleDetail;
