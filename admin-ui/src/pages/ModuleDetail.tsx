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
  uploadModuleVersion,
  updateModuleInfo,
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
  const [upgradeLoading, setUpgradeLoading] = useState(false);
  const [upgradeMsg, setUpgradeMsg] = useState<string | null>(null);
  const [upgradeError, setUpgradeError] = useState<string | null>(null);
  const [upgradeVersion, setUpgradeVersion] = useState("");
  const [upgradeDesc, setUpgradeDesc] = useState("");
  const [upgradeTags, setUpgradeTags] = useState("");
  const [upgradeFile, setUpgradeFile] = useState<File | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editDesc, setEditDesc] = useState("");
  const [editTags, setEditTags] = useState("");
  const [editLoading, setEditLoading] = useState(false);
  const [editMsg, setEditMsg] = useState<string | null>(null);
  const [editError, setEditError] = useState<string | null>(null);
  const [upgradeCode, setUpgradeCode] = useState("");

  useEffect(() => {
    if (!name) return;
    setLoading(true);
    fetchModuleDetail(name)
      .then((mod) => {
        setModule(mod);
        if (mod.env === "inline") {
          setUpgradeCode(mod.code || "");
        }
      })
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
            <Typography variant="subtitle2">현재 적용 버전</Typography>
            <Typography>{module.current_version || module.version}</Typography>
          </Box>
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2">최신 업로드 버전</Typography>
            <Typography>{module.latest_version || module.version}</Typography>
          </Box>
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2">태그</Typography>
            {editMode ? (
              <input
                type="text"
                value={editTags}
                onChange={(e) => setEditTags(e.target.value)}
                style={{ width: 200, marginRight: 8 }}
              />
            ) : (
              <Stack direction="row" spacing={1}>
                {module.tags?.map((tag: string) => (
                  <Chip key={tag} label={tag} size="small" />
                ))}
              </Stack>
            )}
          </Box>
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle2">설명</Typography>
            {editMode ? (
              <input
                type="text"
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                style={{ width: 400, marginRight: 8 }}
              />
            ) : (
              <Typography>{module.description}</Typography>
            )}
          </Box>
          {editMsg && <Alert severity="success">{editMsg}</Alert>}
          {editError && <Alert severity="error">{editError}</Alert>}
          <Box sx={{ mb: 2 }}>
            {editMode ? (
              <>
                <Button
                  size="small"
                  variant="contained"
                  color="primary"
                  disabled={editLoading}
                  onClick={async () => {
                    if (!name) return;
                    setEditLoading(true);
                    setEditMsg(null);
                    setEditError(null);
                    try {
                      await updateModuleInfo(name, {
                        description: editDesc,
                        tags: editTags,
                      });
                      setEditMsg("수정 완료");
                      setEditMode(false);
                      fetchModuleDetail(name).then(setModule);
                    } catch (e: any) {
                      setEditError(e?.response?.data?.detail || e.message);
                    } finally {
                      setEditLoading(false);
                    }
                  }}
                >
                  저장
                </Button>
                <Button
                  size="small"
                  sx={{ ml: 1 }}
                  onClick={() => setEditMode(false)}
                  disabled={editLoading}
                >
                  취소
                </Button>
              </>
            ) : (
              <Button
                size="small"
                variant="outlined"
                onClick={() => {
                  setEditMode(true);
                  setEditDesc(module.description || "");
                  setEditTags(
                    Array.isArray(module.tags)
                      ? module.tags.join(",")
                      : module.tags || ""
                  );
                  setEditMsg(null);
                  setEditError(null);
                }}
              >
                수정
              </Button>
            )}
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
      <Divider sx={{ my: 3 }} />
      <Typography variant="h6" gutterBottom>
        새 버전 업로드
      </Typography>
      {upgradeMsg && <Alert severity="success">{upgradeMsg}</Alert>}
      {upgradeError && <Alert severity="error">{upgradeError}</Alert>}
      <Box
        component="form"
        sx={{ mb: 3 }}
        onSubmit={async (e) => {
          e.preventDefault();
          if (!name) return;
          setUpgradeLoading(true);
          setUpgradeMsg(null);
          setUpgradeError(null);
          try {
            const formData = new FormData();
            formData.append("env", module?.env || "venv");
            formData.append("version", upgradeVersion);
            formData.append("description", upgradeDesc);
            formData.append("tags", upgradeTags);
            if (module?.env === "inline") {
              formData.append("code", upgradeCode);
            } else {
              if (upgradeFile) formData.append("file", upgradeFile);
            }
            await uploadModuleVersion(name, formData);
            setUpgradeMsg("새 버전 업로드 성공");
            setUpgradeVersion("");
            fetchModuleDetail(name).then((mod) => {
              setModule(mod);
              if (mod.env === "inline") {
                setUpgradeCode(mod.code || "");
                setUpgradeDesc(mod.description || "");
              }
            });
            setUpgradeTags("");
            setUpgradeFile(null);
            fetchModuleVersions(name).then(setVersions);
          } catch (e: any) {
            setUpgradeError(e?.response?.data?.detail || e.message);
          } finally {
            setUpgradeLoading(false);
          }
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          {module?.env === "inline" ? (
            <textarea
              placeholder="코드 입력"
              value={upgradeCode}
              onChange={(e) => setUpgradeCode(e.target.value)}
              rows={6}
              style={{ width: 400, fontFamily: "monospace" }}
              required
            />
          ) : (
            <input
              type="file"
              accept=".zip"
              onChange={(e) => setUpgradeFile(e.target.files?.[0] || null)}
              style={{ display: "inline-block" }}
            />
          )}
          <input
            type="text"
            placeholder="버전 (예: 0.2.0)"
            value={upgradeVersion}
            onChange={(e) => setUpgradeVersion(e.target.value)}
            style={{ width: 120 }}
            required
          />
          <input
            type="text"
            placeholder="태그(쉼표구분)"
            value={upgradeTags}
            onChange={(e) => setUpgradeTags(e.target.value)}
            style={{ width: 160 }}
          />
          <Button type="submit" variant="contained" disabled={upgradeLoading}>
            {upgradeLoading ? "업로드중..." : "업그레이드"}
          </Button>
        </Stack>
      </Box>
    </Paper>
  );
};

export default ModuleDetail;
