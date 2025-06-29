import React, { useEffect, useState, useCallback } from "react";
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
  Grid,
  TextField,
  IconButton,
  InputAdornment,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Tabs,
  Tab,
  Switch,
  FormControlLabel,
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
  getModuleEnvVars,
  addModuleEnvVar,
  deleteModuleEnvVar,
  updateModuleEnvVar,
} from "../api";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import VersionSelectInput from "../components/VersionSelectInput";
import axios from "axios";

const formatDate = (isoString?: string | null) => {
  if (!isoString) {
    return "";
  }
  return new Date(isoString).toLocaleString();
};

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
  const [upgradeArtifactUri, setUpgradeArtifactUri] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [editDesc, setEditDesc] = useState("");
  const [editTags, setEditTags] = useState("");
  const [editLoading, setEditLoading] = useState(false);
  const [editMsg, setEditMsg] = useState<string | null>(null);
  const [editError, setEditError] = useState<string | null>(null);
  const [upgradeCode, setUpgradeCode] = useState("");
  const [envVars, setEnvVars] = useState<{ key: string; value: string }[]>([]);
  const [showValue, setShowValue] = useState<{ [key: string]: boolean }>({});
  const [newEnv, setNewEnv] = useState({ key: "", value: "" });
  const [envSnackbar, setEnvSnackbar] = useState<string | null>(null);
  const [editKey, setEditKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>("");
  const [tab, setTab] = useState(0); // 0: 기본정보, 1: 버전관리, 2: 이력, 3: 환경변수, 4: 실제 전개 정보
  const [deployInfo, setDeployInfo] = useState<any>(null);
  const [deployInfoLoading, setDeployInfoLoading] = useState(false);
  const [deployInfoError, setDeployInfoError] = useState<string | null>(null);
  const [editIsPublic, setEditIsPublic] = useState(false);

  const fetchData = useCallback(() => {
    if (!name) return;
    setLoading(true);
    Promise.all([
      fetchModuleDetail(name),
      fetchModuleVersions(name),
      fetchModuleHistory(name),
      getModuleEnvVars(name),
    ])
      .then(([mod, versions, history, envVarsData]) => {
        setModule(mod);
        if (mod.env === "inline") {
          setUpgradeCode(mod.code || "");
        }
        setVersions(versions);
        setHistory(history);
        setEnvVars(envVarsData || []);
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail;
        let errorMessage = err.message;

        if (typeof detail === "string") {
          errorMessage = detail;
        } else if (detail && typeof detail === "object") {
          try {
            errorMessage = JSON.stringify(detail);
          } catch {
            errorMessage = "서버에서 오류 응답을 받았습니다.";
          }
        }

        setError(errorMessage);
      })
      .finally(() => setLoading(false));
  }, [name]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (actionMsg) {
      fetchData();
    }
  }, [actionMsg, fetchData]);

  // 실제 전개 정보 fetch
  useEffect(() => {
    if (!name || tab !== 4) return;
    setDeployInfo(null);
    setDeployInfoLoading(true);
    setDeployInfoError(null);
    axios
      .get(`/api/modules/${name}/deployed-info`)
      .then((res) => setDeployInfo(res.data))
      .catch((err) =>
        setDeployInfoError(err?.response?.data?.detail || err.message)
      )
      .finally(() => setDeployInfoLoading(false));
  }, [name, tab]);

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
    } catch (e: any) {
      setActionError(e?.response?.data?.detail || e.message);
    } finally {
      setActionLoading(false);
    }
  };

  const fetchEnvVars = async () => {
    // 예시: setEnvVars([{key: 'API_KEY', value: 'secret'}, ...]);
  };
  const handleAddEnv = async () => {
    if (!newEnv.key || !name) return;
    try {
      await addModuleEnvVar(name, newEnv.key, newEnv.value);
      setEnvVars([...envVars, { ...newEnv }]);
      setNewEnv({ key: "", value: "" });
      setEnvSnackbar("환경변수 추가됨");
    } catch (error: any) {
      setEnvSnackbar(error?.response?.data?.detail || "환경변수 추가 실패");
    }
  };
  const handleDeleteEnv = async (key: string) => {
    if (!name) return;
    try {
      await deleteModuleEnvVar(name, key);
      setEnvVars(envVars.filter((e) => e.key !== key));
      setEnvSnackbar("환경변수 삭제됨");
    } catch (error: any) {
      setEnvSnackbar(error?.response?.data?.detail || "환경변수 삭제 실패");
    }
  };
  const handleValueChange = async (key: string, value: string) => {
    if (!name) return;
    try {
      await updateModuleEnvVar(name, key, value);
      setEnvVars(envVars.map((e) => (e.key === key ? { ...e, value } : e)));
    } catch (error: any) {
      setEnvSnackbar(error?.response?.data?.detail || "환경변수 수정 실패");
    }
  };
  const handleToggleShow = (key: string) => {
    setShowValue((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // --- 섹션별 렌더링 함수 ---
  const renderInfo = () => (
    <>
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
        <Grid container spacing={3}>
          {/* Left Column */}
          <Grid item xs={12} md={6}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                이름
              </Typography>
              <Typography>{module.name}</Typography>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                환경
              </Typography>
              <Typography>{module.env}</Typography>
            </Box>
            {module.artifact_type && module.artifact_uri && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Artifact
                </Typography>
                <Typography color="primary" fontWeight={500}>
                  {module.artifact_type}: {module.artifact_uri}
                </Typography>
              </Box>
            )}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                현재 적용 버전
              </Typography>
              <Typography>
                {module.current_version || module.version}
              </Typography>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                공개 여부
              </Typography>
              {editMode ? (
                <FormControlLabel
                  control={
                    <Switch
                      checked={editIsPublic}
                      onChange={(e) => setEditIsPublic(e.target.checked)}
                      color="primary"
                    />
                  }
                  label={editIsPublic ? "공개" : "비공개"}
                />
              ) : (
                <Chip
                  label={module.visibility === "public" ? "공개" : "비공개"}
                  color={module.visibility === "public" ? "primary" : "default"}
                  size="small"
                />
              )}
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                생성일
              </Typography>
              <Typography>{formatDate(module.created_at)}</Typography>
            </Box>
          </Grid>

          {/* Right Column */}
          <Grid item xs={12} md={6}>
            <Box sx={{ mb: 2 }}>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                sx={{ mb: 0.5 }}
              >
                태그
              </Typography>
              {editMode ? (
                <TextField
                  fullWidth
                  size="small"
                  value={editTags}
                  onChange={(e) => setEditTags(e.target.value)}
                  variant="outlined"
                />
              ) : (
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  {module.tags?.length > 0 ? (
                    module.tags.map((tag: string) => (
                      <Chip key={tag} label={tag} size="small" />
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      태그 없음
                    </Typography>
                  )}
                </Stack>
              )}
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                sx={{ mb: 0.5 }}
              >
                설명
              </Typography>
              {editMode ? (
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  size="small"
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  variant="outlined"
                />
              ) : (
                <Typography
                  variant="body2"
                  color={module.description ? "text.primary" : "text.secondary"}
                  sx={{ whiteSpace: "pre-wrap", minHeight: "22px" }}
                >
                  {module.description || "설명 없음"}
                </Typography>
              )}
            </Box>

            {editMsg && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {editMsg}
              </Alert>
            )}
            {editError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {editError}
              </Alert>
            )}

            <Box>
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
                          is_public: editIsPublic,
                        });
                        setEditMsg("수정 완료");
                        setEditMode(false);
                        fetchData();
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
                    setEditIsPublic(module.visibility === "public");
                    setEditMsg(null);
                    setEditError(null);
                  }}
                >
                  수정
                </Button>
              )}
            </Box>
          </Grid>
        </Grid>
      )}
      {!loading && !error && !module && (
        <Typography>모듈 정보를 찾을 수 없습니다.</Typography>
      )}
    </>
  );

  const renderVersion = () => (
    <>
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
            formData.append("version", upgradeVersion);
            formData.append("description", upgradeDesc);
            if (module?.env === "inline") {
              formData.append("code", upgradeCode);
            } else if (
              module?.env === "venv" ||
              module?.env === "conda" ||
              module?.env === "uv"
            ) {
              if (upgradeFile) formData.append("file", upgradeFile);
              if (upgradeArtifactUri)
                formData.append("artifact_uri", upgradeArtifactUri);
            }
            await uploadModuleVersion(name, formData);
            setUpgradeMsg("새 버전 업로드 성공");
            setUpgradeVersion("");
            setUpgradeCode("");
            fetchData();
            setUpgradeTags("");
            setUpgradeFile(null);
            setUpgradeArtifactUri("");
          } catch (e: any) {
            setUpgradeError(e?.response?.data?.detail || e.message);
          } finally {
            setUpgradeLoading(false);
          }
        }}
      >
        {module?.env === "inline" ? (
          <Box sx={{ mb: 3 }}>
            <Typography
              variant="subtitle2"
              color="text.secondary"
              sx={{ mb: 0.5 }}
            >
              코드 *
            </Typography>
            <TextField
              multiline
              minRows={10}
              maxRows={30}
              fullWidth
              value={upgradeCode}
              onChange={(e) => setUpgradeCode(e.target.value)}
              placeholder={`import os\n\nreturn {"message": "기본 동작 테스트", "A": os.environ.get('A', 'NOT_SET')}`}
              sx={{ fontFamily: "monospace", mb: 1 }}
              required
            />
            <Typography variant="caption" color="text.secondary">
              실행 시 input 파라미터로 전달됩니다. 코드에서 input['x'] 등으로
              바로 사용하세요.
              <br />
              환경변수는 <b>os.environ.get('KEY')</b>로 접근할 수 있습니다.
            </Typography>
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
              sx={{ mt: 2 }}
            >
              <VersionSelectInput
                currentVersion={
                  module?.current_version || module?.version || "0.1.0"
                }
                value={upgradeVersion}
                onChange={setUpgradeVersion}
              />
              <TextField
                size="small"
                placeholder="태그(쉼표구분)"
                value={upgradeTags}
                onChange={(e) => setUpgradeTags(e.target.value)}
                sx={{ width: 160 }}
              />
              <TextField
                size="small"
                placeholder="설명"
                value={upgradeDesc}
                onChange={(e) => setUpgradeDesc(e.target.value)}
                sx={{ width: 200 }}
              />
              <Button
                type="submit"
                variant="contained"
                disabled={upgradeLoading}
              >
                {upgradeLoading ? "업로드중..." : "업그레이드"}
              </Button>
            </Stack>
          </Box>
        ) : module?.env === "venv" ||
          module?.env === "conda" ||
          module?.env === "uv" ? (
          <Box sx={{ mb: 3 }}>
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
              sx={{ mb: 2 }}
            >
              <VersionSelectInput
                currentVersion={
                  module?.current_version || module?.version || "0.1.0"
                }
                value={upgradeVersion}
                onChange={setUpgradeVersion}
              />
              <TextField
                size="small"
                placeholder="태그(쉼표구분)"
                value={upgradeTags}
                onChange={(e) => setUpgradeTags(e.target.value)}
                sx={{ width: 160 }}
              />
              <TextField
                size="small"
                placeholder="설명"
                value={upgradeDesc}
                onChange={(e) => setUpgradeDesc(e.target.value)}
                sx={{ width: 200 }}
              />
            </Stack>
            <Box sx={{ mb: 2 }}>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                sx={{ mb: 1 }}
              >
                소스 업로드 방식 선택
              </Typography>
              <Stack direction="row" spacing={2} alignItems="center">
                <Button
                  variant="contained"
                  component="label"
                  disabled={!!upgradeArtifactUri}
                  size="small"
                >
                  파일 선택
                  <input
                    type="file"
                    accept=".zip"
                    hidden
                    onChange={(e) => {
                      setUpgradeFile(e.target.files?.[0] || null);
                      if (e.target.files?.[0]) setUpgradeArtifactUri("");
                    }}
                  />
                </Button>
                {upgradeFile && (
                  <Typography variant="body2" color="text.secondary">
                    선택된 파일: {upgradeFile.name}
                  </Typography>
                )}
              </Stack>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 1, mb: 1 }}
              >
                또는
              </Typography>
              <TextField
                size="small"
                label="Git 저장소 링크"
                value={upgradeArtifactUri}
                onChange={(e) => {
                  setUpgradeArtifactUri(e.target.value);
                  if (e.target.value) setUpgradeFile(null);
                }}
                placeholder="https://github.com/username/repo.git"
                disabled={!!upgradeFile}
                sx={{ width: 400 }}
              />
            </Box>
            <Button type="submit" variant="contained" disabled={upgradeLoading}>
              {upgradeLoading ? "업로드중..." : "업그레이드"}
            </Button>
          </Box>
        ) : null}
      </Box>
      <Divider sx={{ my: 3 }} />
      <Typography variant="h6" gutterBottom>
        버전 목록
      </Typography>
      {actionMsg && <Alert severity="success">{actionMsg}</Alert>}
      {actionError && <Alert severity="error">{actionError}</Alert>}
      <TableContainer sx={{ mb: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow key="version-header">
              <TableCell>이름</TableCell>
              <TableCell>환경</TableCell>
              <TableCell>버전</TableCell>
              <TableCell>설명</TableCell>
              <TableCell>태그</TableCell>
              <TableCell>상태</TableCell>
              <TableCell>액션</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {versions
              .sort((a, b) => {
                // 버전 문자열을 숫자 배열로 변환 (예: "1.2.3" -> [1, 2, 3])
                const vA = a.version.split(".").map(Number);
                const vB = b.version.split(".").map(Number);

                // 역순 정렬 (최신 버전이 위로)
                for (let i = 0; i < Math.max(vA.length, vB.length); i++) {
                  const numA = vA[i] || 0;
                  const numB = vB[i] || 0;
                  if (numA !== numB) return numB - numA;
                }
                return 0;
              })
              .map((v, index) => (
                <TableRow key={`${v.id}-${index}`}>
                  <TableCell>{v.name}</TableCell>
                  <TableCell>{v.env}</TableCell>
                  <TableCell>{v.version}</TableCell>
                  <TableCell>{v.description || ""}</TableCell>
                  <TableCell>
                    {Array.isArray(v.tags) ? v.tags.join(", ") : v.tags || ""}
                  </TableCell>
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
    </>
  );

  // version_id → semver 매핑 테이블 생성 (id, version_id 모두 string 변환)
  const versionIdToSemver = Object.fromEntries(
    versions.map((v) => [String(v.id), v.version])
  );

  const renderHistory = () => (
    <>
      <Typography variant="h6" gutterBottom>
        이력
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow key="history-header">
              <TableCell>액션</TableCell>
              <TableCell>버전</TableCell>
              <TableCell>담당자</TableCell>
              <TableCell>일시</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {history.map((h, index) => (
              <TableRow key={`${h.id}-${index}`}>
                <TableCell>{h.action}</TableCell>
                <TableCell>{h.version || ""}</TableCell>
                <TableCell>{h.operator}</TableCell>
                <TableCell>{formatDate(h.timestamp)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );

  const renderEnvVars = () => (
    <>
      <Typography variant="h6" gutterBottom>
        환경변수 관리
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>키</TableCell>
              <TableCell>값</TableCell>
              <TableCell>액션</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {envVars.map((env) => (
              <TableRow key={env.key}>
                <TableCell>{env.key}</TableCell>
                <TableCell>
                  <TextField
                    type={showValue[env.key] ? "text" : "password"}
                    value={editKey === env.key ? editValue : env.value}
                    size="small"
                    onChange={(e) => {
                      setEditKey(env.key);
                      setEditValue(e.target.value);
                    }}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() =>
                              setShowValue((prev) => ({
                                ...prev,
                                [env.key]: !prev[env.key],
                              }))
                            }
                            size="small"
                          >
                            {showValue[env.key] ? (
                              <VisibilityOff />
                            ) : (
                              <Visibility />
                            )}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                </TableCell>
                <TableCell>
                  {editKey === env.key ? (
                    <>
                      <Button
                        size="small"
                        color="primary"
                        onClick={async () => {
                          if (!name) return;
                          await updateModuleEnvVar(name, env.key, editValue);
                          setEnvVars(
                            envVars.map((e) =>
                              e.key === env.key ? { ...e, value: editValue } : e
                            )
                          );
                          setEditKey(null);
                          setEditValue("");
                          setEnvSnackbar("환경변수 수정됨");
                        }}
                      >
                        저장
                      </Button>
                      <Button
                        size="small"
                        onClick={() => {
                          setEditKey(null);
                          setEditValue("");
                        }}
                      >
                        취소
                      </Button>
                    </>
                  ) : null}
                  <Button
                    size="small"
                    color="error"
                    onClick={() => handleDeleteEnv(env.key)}
                  >
                    삭제
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell>
                <TextField
                  size="small"
                  placeholder="키"
                  value={newEnv.key}
                  onChange={(e) =>
                    setNewEnv((v) => ({ ...v, key: e.target.value }))
                  }
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      handleAddEnv();
                    }
                  }}
                />
              </TableCell>
              <TableCell>
                <TextField
                  size="small"
                  placeholder="값"
                  value={newEnv.value}
                  onChange={(e) =>
                    setNewEnv((v) => ({ ...v, value: e.target.value }))
                  }
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      handleAddEnv();
                    }
                  }}
                />
              </TableCell>
              <TableCell>
                <Button size="small" variant="outlined" onClick={handleAddEnv}>
                  추가
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
      <Snackbar
        open={!!envSnackbar}
        autoHideDuration={1500}
        onClose={() => setEnvSnackbar(null)}
        message={envSnackbar}
      />
    </>
  );

  const renderDeployedInfo = () => (
    <>
      <Typography variant="h6" gutterBottom>
        실제 전개 정보
      </Typography>
      {deployInfoLoading && <CircularProgress sx={{ mt: 2 }} />}
      {deployInfoError && <Alert severity="error">{deployInfoError}</Alert>}
      {deployInfo && deployInfo.message && (
        <Alert severity="info">{deployInfo.message}</Alert>
      )}
      {deployInfo && !deployInfo.message && (
        <>
          {/* 배포 경로 정보 */}
          {deployInfo.deploy_exists && (
            <>
              <Typography
                variant="subtitle1"
                sx={{ mt: 2, mb: 1, fontWeight: "bold" }}
              >
                📦 배포 경로 (원본 파일)
              </Typography>
              <Box sx={{ mb: 2, p: 2, bgcolor: "grey.50", borderRadius: 1 }}>
                <b>경로:</b> {deployInfo.deploy_path}
                <br />
                <b>활성화된 버전:</b> {deployInfo.active_version || "없음"}
                <br />
                <b>파일 개수:</b> {deployInfo.deploy_file_count}
                <br />
                <b>디스크 사용량:</b> {deployInfo.deploy_total_size}
              </Box>

              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                배포된 파일 목록 (최대 30개)
              </Typography>
              <TableContainer sx={{ maxHeight: 200, mb: 3 }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>경로</TableCell>
                      <TableCell>크기</TableCell>
                      <TableCell>수정일</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {deployInfo.deploy_files.map((f: any, idx: number) => (
                      <TableRow key={`deploy-${idx}`}>
                        <TableCell>{f.path}</TableCell>
                        <TableCell>{f.size}</TableCell>
                        <TableCell>
                          {f.modified
                            ? new Date(f.modified).toLocaleString()
                            : ""}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}

          {/* 전개 경로 정보 */}
          {deployInfo.env_exists && (
            <>
              <Typography
                variant="subtitle1"
                sx={{ mt: 3, mb: 1, fontWeight: "bold" }}
              >
                🚀 전개 경로 (실행 환경)
              </Typography>
              <Box sx={{ mb: 2, p: 2, bgcolor: "blue.50", borderRadius: 1 }}>
                <b>경로:</b> {deployInfo.env_path}
                <br />
                <b>환경 타입:</b> {deployInfo.env_type}
                <br />
                <b>파일 개수:</b> {deployInfo.env_file_count}
                <br />
                <b>디스크 사용량:</b> {deployInfo.env_total_size}
                {deployInfo.dependency_count > 0 && (
                  <>
                    <br />
                    <b>설치된 패키지:</b> {deployInfo.dependency_count}개
                  </>
                )}
              </Box>

              {/* Dependencies 정보 */}
              {deployInfo.dependencies &&
                deployInfo.dependencies.length > 0 && (
                  <>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      설치된 Dependencies ({deployInfo.dependency_count}개)
                    </Typography>
                    <TableContainer sx={{ maxHeight: 200, mb: 3 }}>
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell>패키지명</TableCell>
                            <TableCell>버전</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {deployInfo.dependencies.map(
                            (dep: any, idx: number) => (
                              <TableRow key={`dep-${idx}`}>
                                <TableCell>
                                  {dep.error ? (
                                    <Alert severity="error" sx={{ py: 0 }}>
                                      {dep.error}
                                    </Alert>
                                  ) : (
                                    dep.package
                                  )}
                                </TableCell>
                                <TableCell>
                                  {dep.error ? "" : dep.version}
                                </TableCell>
                              </TableRow>
                            )
                          )}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </>
                )}

              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                전개된 환경 파일 목록 (최대 30개)
              </Typography>
              <TableContainer sx={{ maxHeight: 200 }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>경로</TableCell>
                      <TableCell>크기</TableCell>
                      <TableCell>수정일</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {deployInfo.env_files.map((f: any, idx: number) => (
                      <TableRow key={`env-${idx}`}>
                        <TableCell>{f.path}</TableCell>
                        <TableCell>{f.size}</TableCell>
                        <TableCell>
                          {f.modified
                            ? new Date(f.modified).toLocaleString()
                            : ""}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}

          {/* 경로가 존재하지 않는 경우 */}
          {!deployInfo.deploy_exists && !deployInfo.env_exists && (
            <Alert severity="warning">
              배포 경로와 전개 경로 모두 존재하지 않습니다.
            </Alert>
          )}
        </>
      )}
    </>
  );

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        width: "100%",
        marginTop: 40,
      }}
    >
      <Paper
        sx={{
          p: 4,
          mb: 3,
          minWidth: 1200,
          maxWidth: "90vw",
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
          <Tab label="기본 정보" />
          <Tab label="버전 관리" />
          <Tab label="이력" />
          <Tab label="환경변수" />
          <Tab label="실제 전개 정보" />
        </Tabs>
        <Box sx={{ mt: 2 }}>
          {tab === 0 && renderInfo()}
          {tab === 1 && renderVersion()}
          {tab === 2 && renderHistory()}
          {tab === 3 && renderEnvVars()}
          {tab === 4 && renderDeployedInfo()}
        </Box>
      </Paper>
    </div>
  );
};

export default ModuleDetail;
