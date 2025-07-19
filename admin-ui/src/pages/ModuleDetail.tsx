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
  DialogContentText,
  Container,
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
  const [autoDeploy, setAutoDeploy] = useState(false);
  const [showDeployDialog, setShowDeployDialog] = useState(false);
  const [deployDialogData, setDeployDialogData] = useState<{
    moduleName: string;
    version: string;
  }>({ moduleName: "", version: "" });
  const [showDeployFailureDialog, setShowDeployFailureDialog] = useState(false);
  const [deployFailureData, setDeployFailureData] = useState<{
    version: string;
    error: string;
  }>({ version: "", error: "" });

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
        // 인라인 모듈의 경우 활성화된 버전의 코드를 설정하지 않음 (별도 useEffect에서 처리)
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

  // 업그레이드 탭 진입 시 활성화 버전(없으면 최신 버전) 코드 자동 세팅
  useEffect(() => {
    if (tab === 1 && module?.artifact_type === "inline" && name) {
      // 1. 버전 리스트 조회
      fetchModuleVersions(name).then((versions) => {
        let targetVersion = versions.find((v: any) => v.is_active)?.version;
        if (!targetVersion && versions.length > 0) {
          targetVersion = versions[0].version; // 최신 버전
        }
        if (targetVersion) {
          // 2. 해당 버전의 code 조회
          axios
            .get(`/api/modules/${name}/versions/${targetVersion}`)
            .then((res) => setUpgradeCode(res.data.code || ""))
            .catch(() => setUpgradeCode(""));
        } else {
          setUpgradeCode("");
        }
      });
    }
    // eslint-disable-next-line
  }, [tab, module?.artifact_type, name]);

  const handleAction = async (type: "activate", version: string) => {
    if (!name) return;
    setActionLoading(true);
    setActionMsg(null);
    setActionError(null);
    try {
      let res;
      if (type === "activate") {
        // 1. 먼저 버전을 활성화
        res = await activateModuleVersion(name, version);

        // 2. 모듈이 inline이 아니면 전개도 진행
        if (module && module.env !== "inline") {
          try {
            const deployResponse = await axios.post(
              `/api/modules/${encodeURIComponent(name)}/deploy`
            );
            setActionMsg(
              `버전 ${version} 활성화 및 전개 완료 - ${deployResponse.data.detail}`
            );
          } catch (deployError: any) {
            // 전개 실패 시 활성화도 롤백
            try {
              // 이전 활성 버전으로 롤백 (또는 비활성화)
              const currentActiveVersion = module?.version;
              if (currentActiveVersion && currentActiveVersion !== version) {
                await activateModuleVersion(name, currentActiveVersion);
              }
              // 전개 실패 다이얼로그 표시
              setDeployFailureData({
                version: version,
                error:
                  deployError?.response?.data?.detail ||
                  deployError?.message ||
                  "알 수 없는 오류",
              });
              setShowDeployFailureDialog(true);
            } catch (rollbackError: any) {
              setActionError(
                `전개 실패 및 롤백 실패: ${
                  deployError?.response?.data?.detail || deployError?.message
                } (롤백 오류: ${
                  rollbackError?.response?.data?.detail ||
                  rollbackError?.message
                })`
              );
            }
          }
        } else {
          setActionMsg(res.detail || "활성화 완료");
          // 인라인 모듈의 경우 활성화된 버전의 코드로 UI 갱신
          if (module?.artifact_type === "inline") {
            try {
              const versionResponse = await axios.get(
                `/api/modules/${encodeURIComponent(name)}/versions/${version}`
              );
              setUpgradeCode(versionResponse.data.code || "");
            } catch (error) {
              console.error("활성화된 버전 코드 조회 실패:", error);
            }
          }
        }
      }
    } catch (e: any) {
      setActionError(e?.response?.data?.detail || e.message);
    } finally {
      setActionLoading(false);
      // 데이터 새로고침
      fetchData();
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
    setShowValue({ ...showValue, [key]: !showValue[key] });
  };

  // 자동 전개 다이얼로그 핸들러
  const handleDeployConfirm = async () => {
    try {
      // 새 버전을 활성화하는 API 호출
      const formData = new FormData();
      formData.append("version", deployDialogData.version);

      await axios.post(
        `/api/modules/${encodeURIComponent(
          deployDialogData.moduleName
        )}/activate`,
        formData
      );
      setShowDeployDialog(false);
      setUpgradeMsg("새 버전 업로드 및 자동 전개 성공");
      setUpgradeVersion("");
      setUpgradeCode("");
      fetchData();
      setUpgradeTags("");
      setUpgradeFile(null);
      setUpgradeArtifactUri("");
      setAutoDeploy(false);
    } catch (err: any) {
      console.error("자동 전개 오류:", err);
      let errorMessage = "자동 전개 중 오류가 발생했습니다";

      if (err?.response?.data?.detail) {
        errorMessage += ": " + err.response.data.detail;
      } else if (err?.response?.status) {
        errorMessage += ` (HTTP ${err.response.status})`;
      } else if (err?.message) {
        errorMessage += ": " + err.message;
      } else if (typeof err === "string") {
        errorMessage += ": " + err;
      } else {
        errorMessage += ": 알 수 없는 오류";
      }

      setUpgradeError(errorMessage);
    }
  };

  const handleDeployCancel = () => {
    setShowDeployDialog(false);
    setUpgradeMsg("새 버전 업로드 성공 (수동 전개 필요)");
    setUpgradeVersion("");
    setUpgradeCode("");
    fetchData();
    setUpgradeTags("");
    setUpgradeFile(null);
    setUpgradeArtifactUri("");
    setAutoDeploy(false);
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
            {/* artifact_type/env/artifact_uri 표 */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                유형 정보
              </Typography>
              <Table size="small" sx={{ maxWidth: 400 }}>
                <TableBody>
                  <TableRow>
                    <TableCell sx={{ fontWeight: "bold", width: 90 }}>
                      artifact_type
                    </TableCell>
                    <TableCell>{module.artifact_type || "-"}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: "bold" }}>env</TableCell>
                    <TableCell>{module.env || "-"}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: "bold" }}>
                      artifact_uri
                    </TableCell>
                    <TableCell>
                      {module.artifact_uri ? (
                        <a
                          href={module.artifact_uri}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            textDecoration: "underline",
                            color: "#1976d2",
                          }}
                        >
                          {module.artifact_uri}
                        </a>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
              <Typography variant="caption" color="text.secondary">
                artifact_type은 최초 생성 후 변경할 수 없습니다.
              </Typography>
            </Box>
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
            formData.append("auto_deploy", String(autoDeploy));
            // artifact_type별 분기
            if (module?.artifact_type === "inline") {
              formData.append("code", upgradeCode);
            } else if (module?.artifact_type === "zip") {
              if (upgradeFile) formData.append("file", upgradeFile);
            } else if (
              module?.artifact_type === "git" ||
              module?.artifact_type === "docker"
            ) {
              // git/docker: 업그레이드는 코드 다시 가져오기만 지원
              // 별도 업로드 없음
            }
            const response = await uploadModuleVersion(name, formData);

            // 응답에서 전개 상태 확인 (안전한 접근)
            const responseData = response?.data || response;
            if (responseData?.was_deployed && !responseData?.auto_deployed) {
              setDeployDialogData({
                moduleName: name,
                version: upgradeVersion,
              });
              setShowDeployDialog(true);
            } else {
              setUpgradeMsg("새 버전 업로드 성공");
              setUpgradeVersion("");
              setUpgradeCode("");
              fetchData();
              setUpgradeTags("");
              setUpgradeFile(null);
              setUpgradeArtifactUri("");
              setAutoDeploy(false);
            }
          } catch (e: any) {
            console.error("버전 업로드 오류:", e);
            let errorMessage = "버전 업로드 중 오류가 발생했습니다";

            if (e?.response?.data?.detail) {
              errorMessage += ": " + e.response.data.detail;
            } else if (e?.response?.status) {
              errorMessage += ` (HTTP ${e.response.status})`;
            } else if (e?.message) {
              errorMessage += ": " + e.message;
            } else if (typeof e === "string") {
              errorMessage += ": " + e;
            } else {
              errorMessage += ": 알 수 없는 오류";
            }

            setUpgradeError(errorMessage);
          } finally {
            setUpgradeLoading(false);
          }
        }}
      >
        {/* artifact_type별 업그레이드 UI */}
        {module?.artifact_type === "inline" && (
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
                versions={versions.map((v: any) => v.version)}
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
              <FormControlLabel
                control={
                  <Switch
                    checked={autoDeploy}
                    onChange={(e) => setAutoDeploy(e.target.checked)}
                    color="primary"
                  />
                }
                label="자동 전개"
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
        )}
        {module?.artifact_type === "zip" && (
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
                versions={versions.map((v: any) => v.version)}
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
                새 zip 파일 첨부
              </Typography>
              <Button variant="contained" component="label" size="small">
                파일 선택
                <input
                  type="file"
                  accept=".zip"
                  hidden
                  onChange={(e) => {
                    setUpgradeFile(e.target.files?.[0] || null);
                  }}
                />
              </Button>
              {upgradeFile && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ ml: 2 }}
                >
                  선택된 파일: {upgradeFile.name}
                </Typography>
              )}
            </Box>
            <Button type="submit" variant="contained" disabled={upgradeLoading}>
              {upgradeLoading ? "업로드중..." : "업그레이드"}
            </Button>
            <FormControlLabel
              control={
                <Switch
                  checked={autoDeploy}
                  onChange={(e) => setAutoDeploy(e.target.checked)}
                  color="primary"
                />
              }
              label="자동 전개"
            />
          </Box>
        )}
        {(module?.artifact_type === "git" ||
          module?.artifact_type === "docker") && (
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
                versions={versions.map((v: any) => v.version)}
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
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {module.artifact_type === "git"
                ? "Git 저장소 URL은 변경할 수 없습니다. 업그레이드는 현재 저장소의 최신 코드를 다시 가져옵니다."
                : "Docker 이미지 URL은 변경할 수 없습니다. 업그레이드는 현재 이미지를 다시 가져옵니다."}
            </Typography>
            <Button type="submit" variant="contained" disabled={upgradeLoading}>
              {upgradeLoading ? "업로드중..." : "코드 다시 가져오기"}
            </Button>
          </Box>
        )}
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
                    {v.version === module?.version ? (
                      <Button disabled variant="contained" color="success">
                        활성화됨
                      </Button>
                    ) : (
                      <Tooltip
                        title={
                          module?.env === "inline"
                            ? "버전을 활성화합니다"
                            : "버전을 활성화하고 전개합니다"
                        }
                      >
                        <Button
                          onClick={() => handleAction("activate", v.version)}
                          variant="contained"
                          color="primary"
                          disabled={actionLoading}
                        >
                          {actionLoading ? "처리중..." : "활성화 및 전개"}
                        </Button>
                      </Tooltip>
                    )}
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
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>
        모듈 상세 정보
      </Typography>
      <Paper sx={{ p: 4, mb: 3 }}>
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

      {/* 자동 전개 확인 다이얼로그 */}
      <Dialog
        open={showDeployDialog}
        onClose={handleDeployCancel}
        aria-labelledby="deploy-dialog-title"
        aria-describedby="deploy-dialog-description"
      >
        <DialogTitle id="deploy-dialog-title">새 버전 자동 전개</DialogTitle>
        <DialogContent>
          <DialogContentText id="deploy-dialog-description">
            모듈 "{deployDialogData?.moduleName}"의 새 버전 v
            {deployDialogData?.version}이 업로드되었습니다. 이전 버전이 전개되어
            있었습니다. 새 버전을 자동으로 전개하시겠습니까?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeployCancel} color="primary">
            나중에 수동 전개
          </Button>
          <Button
            onClick={handleDeployConfirm}
            color="primary"
            variant="contained"
          >
            자동 전개
          </Button>
        </DialogActions>
      </Dialog>

      {/* 전개 실패 다이얼로그 */}
      <Dialog
        open={showDeployFailureDialog}
        onClose={() => setShowDeployFailureDialog(false)}
        aria-labelledby="deploy-failure-dialog-title"
        aria-describedby="deploy-failure-dialog-description"
      >
        <DialogTitle id="deploy-failure-dialog-title">전개 실패</DialogTitle>
        <DialogContent>
          <DialogContentText id="deploy-failure-dialog-description">
            버전 v{deployFailureData?.version}을 전개하는 중 오류가
            발생했습니다:
            <br />
            <b>{deployFailureData?.error}</b>
            <br />
            활성화된 버전을 롤백하고 새 버전을 활성화하시겠습니까?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setShowDeployFailureDialog(false)}
            color="primary"
          >
            취소
          </Button>
          <Button
            onClick={async () => {
              setShowDeployFailureDialog(false);
              await handleAction("activate", deployFailureData?.version || "");
            }}
            color="primary"
            variant="contained"
          >
            롤백 및 전개
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ModuleDetail;
