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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
} from "@mui/material";
import {
  fetchModuleDetail,
  fetchModuleVersions,
  rollbackModule,
  activateModuleVersion,
  deactivateModuleVersion,
  fetchModuleHistory,
} from "../api";

const formatDate = (iso: string) =>
  iso ? iso.replace("T", " ").slice(0, 19) : "";

const ModuleDetail: React.FC = () => {
  const { name } = useParams();
  const [module, setModule] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (!name) return;
    setLoading(true);
    fetchModuleDetail(name)
      .then(setModule)
      .catch((err) => setError(err?.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
    fetchModuleVersions(name).then(setVersions);
    fetchModuleHistory(name).then(setHistory);
  }, [name, actionMsg]);

  const handleAction = async (
    type: "rollback" | "activate" | "deactivate",
    version: string
  ) => {
    if (!name) return;
    setActionLoading(true);
    setActionMsg(null);
    setActionError(null);
    try {
      let res;
      if (type === "rollback") res = await rollbackModule(name, version);
      if (type === "activate") res = await activateModuleVersion(name, version);
      if (type === "deactivate")
        res = await deactivateModuleVersion(name, version);
      setActionMsg(res.detail || "성공");
      // 데이터 새로고침
      fetchModuleVersions(name).then(setVersions);
      fetchModuleDetail(name).then(setModule);
      fetchModuleHistory(name).then(setHistory);
    } catch (e: any) {
      setActionError(e?.response?.data?.detail || e.message);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 4, mb: 3, maxWidth: 800, mx: "auto" }}>
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
      <Divider sx={{ my: 3 }} />
      <Typography variant="h6" gutterBottom>
        버전 목록
      </Typography>
      {actionMsg && <Alert severity="success">{actionMsg}</Alert>}
      {actionError && <Alert severity="error">{actionError}</Alert>}
      <TableContainer sx={{ mb: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>버전</TableCell>
              <TableCell>생성일</TableCell>
              <TableCell>상태</TableCell>
              <TableCell>액션</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {versions.map((v) => (
              <TableRow key={v.id}>
                <TableCell>{v.version}</TableCell>
                <TableCell>{formatDate(v.created_at)}</TableCell>
                <TableCell>{v.status}</TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1}>
                    <Button
                      size="small"
                      variant="outlined"
                      disabled={actionLoading || v.status === "active"}
                      onClick={() => handleAction("rollback", v.version)}
                    >
                      롤백
                    </Button>
                    <Button
                      size="small"
                      variant="contained"
                      color="success"
                      disabled={actionLoading || v.status === "active"}
                      onClick={() => handleAction("activate", v.version)}
                    >
                      활성화
                    </Button>
                    <Button
                      size="small"
                      variant="contained"
                      color="warning"
                      disabled={actionLoading || v.status === "inactive"}
                      onClick={() => handleAction("deactivate", v.version)}
                    >
                      비활성화
                    </Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Divider sx={{ my: 3 }} />
      <Typography variant="h6" gutterBottom>
        이력
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>액션</TableCell>
              <TableCell>버전</TableCell>
              <TableCell>담당자</TableCell>
              <TableCell>일시</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {history.map((h) => (
              <TableRow key={h.id}>
                <TableCell>{h.action}</TableCell>
                <TableCell>{h.version_id}</TableCell>
                <TableCell>{h.operator}</TableCell>
                <TableCell>{formatDate(h.timestamp)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default ModuleDetail;
