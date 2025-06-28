import React, { useEffect, useState } from "react";
import { api } from "../api";
import {
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Tabs,
  Tab,
  Box,
  IconButton,
  Snackbar,
} from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { useNavigate, Link } from "react-router-dom";

interface Module {
  id: string;
  name: string;
  env: string;
  version: string;
  status?: string;
  isDeployed: boolean;
  description?: string;
  tags?: string[];
  artifact_type?: string;
  artifact_uri?: string;
}

const codeTemplates = {
  curl: (name: string, version: string) =>
    `curl -X POST http://<서버주소>/api/modules/${name}/run \
  -H 'Content-Type: application/json' \
  -d '{"input": {}}'`,
  python: (name: string, version: string) =>
    `import requests\nresp = requests.post(\n    \"http://<서버주소>/api/modules/${name}/run\",\n    json={\"input\": {}}\n)\nprint(resp.json())`,
  node: (name: string, version: string) =>
    `const axios = require('axios');\naxios.post('http://<서버주소>/api/modules/${name}/run', { input: {} })\n  .then(res => console.log(res.data));`,
  java: (name: string, version: string) =>
    `// OkHttp 예시\nOkHttpClient client = new OkHttpClient();\nRequestBody body = RequestBody.create(\n    \"{\\\"input\\\": {}}\", MediaType.parse(\"application/json\"));\nRequest request = new Request.Builder()\n    .url(\"http://<서버주소>/api/modules/${name}/run\")\n    .post(body)\n    .build();\nResponse response = client.newCall(request).execute();\nSystem.out.println(response.body().string());`,
};

const ModuleList: React.FC = () => {
  const [modules, setModules] = useState<Module[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deploying, setDeploying] = useState<string | null>(null);
  const [deployLog, setDeployLog] = useState<{ [key: string]: string }>({});
  const [deployError, setDeployError] = useState<{ [key: string]: string }>({});
  const [undeploying, setUndeploying] = useState<string | null>(null);
  const [undeployLog, setUndeployLog] = useState<{ [key: string]: string }>({});
  const [undeployError, setUndeployError] = useState<{ [key: string]: string }>(
    {}
  );
  const [deleteTarget, setDeleteTarget] = useState<Module | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [clientCodeOpen, setClientCodeOpen] = useState(false);
  const [clientCodeTab, setClientCodeTab] = useState(0);
  const [clientCodeModule, setClientCodeModule] = useState<Module | null>(null);
  const [copySnackbar, setCopySnackbar] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    api
      .fetchModules()
      .then((data) => setModules(data))
      .catch((err: any) => {
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
  }, []);

  const handleDeploy = async (name: string) => {
    setDeploying(name);
    setDeployError((prev) => ({ ...prev, [name]: "" }));
    setDeployLog((prev) => ({ ...prev, [name]: "" }));
    try {
      const res = await api.deployModule(name);
      setDeployLog((prev) => ({
        ...prev,
        [name]: res?.detail || "배포 완료",
      }));
      const data = await api.fetchModules();
      setModules(data);
    } catch (err: any) {
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

      setDeployError((prev) => ({
        ...prev,
        [name]: errorMessage,
      }));
    } finally {
      setDeploying(null);
    }
  };

  const handleUndeploy = async (name: string) => {
    setUndeploying(name);
    setUndeployError((prev) => ({ ...prev, [name]: "" }));
    setUndeployLog((prev) => ({ ...prev, [name]: "" }));
    try {
      const res = await api.undeployModule(name);
      setUndeployLog((prev) => ({
        ...prev,
        [name]: res?.log || "전개 해제 완료",
      }));
      const data = await api.fetchModules();
      setModules(data);
    } catch (err: any) {
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

      setUndeployError((prev) => ({
        ...prev,
        [name]: errorMessage,
      }));
    } finally {
      setUndeploying(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    setDeleteError(null);
    try {
      await api.deleteModule(deleteTarget.name);
      const data = await api.fetchModules();
      setModules(data);
      setDeleteTarget(null);
    } catch (err: any) {
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

      setDeleteError(errorMessage);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopySnackbar(true);
  };

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
          p: 3,
          mb: 3,
          minWidth: 1200,
          maxWidth: "90vw",
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <Typography variant="h6" gutterBottom>
          모듈 목록
        </Typography>
        {loading && <CircularProgress sx={{ mt: 2 }} />}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {!loading && !error && (
          <TableContainer sx={{ overflowX: "visible" }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {/* <TableCell>ID</TableCell> */}
                  <TableCell>이름</TableCell>
                  <TableCell>환경</TableCell>
                  <TableCell>버전</TableCell>
                  <TableCell>Artifact</TableCell>
                  <TableCell
                    sx={{
                      maxWidth: 320,
                      minWidth: 200,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    설명
                  </TableCell>
                  <TableCell
                    sx={{
                      maxWidth: 240,
                      minWidth: 120,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    태그
                  </TableCell>
                  <TableCell>상태</TableCell>
                  <TableCell>액션</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {modules.map((m) => (
                  <TableRow key={m.name} hover>
                    {/* <TableCell>{m.id}</TableCell> */}
                    <TableCell>{m.name}</TableCell>
                    <TableCell>{m.env}</TableCell>
                    <TableCell>{m.version}</TableCell>
                    <TableCell>
                      {m.artifact_type && m.artifact_uri ? (
                        <span style={{ color: "#1976d2", fontWeight: 500 }}>
                          {m.artifact_type}: {m.artifact_uri}
                        </span>
                      ) : (
                        <span style={{ color: "#888" }}>-</span>
                      )}
                    </TableCell>
                    <TableCell
                      sx={{
                        maxWidth: 320,
                        minWidth: 200,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                      title={m.description || ""}
                    >
                      {m.description || ""}
                    </TableCell>
                    <TableCell
                      sx={{
                        maxWidth: 240,
                        minWidth: 120,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                      title={
                        Array.isArray(m.tags) ? m.tags.join(", ") : m.tags || ""
                      }
                    >
                      {Array.isArray(m.tags) ? m.tags.join(", ") : m.tags || ""}
                    </TableCell>
                    <TableCell>
                      {m.isDeployed ? (
                        <span style={{ color: "green", fontWeight: 600 }}>
                          전개됨
                        </span>
                      ) : (
                        <span style={{ color: "gray" }}>미전개</span>
                      )}
                    </TableCell>
                    <TableCell
                      sx={{
                        display: "flex",
                        flexDirection: "row",
                        flexWrap: "nowrap",
                        gap: 1,
                        alignItems: "center",
                        minWidth: 220,
                      }}
                    >
                      <Button
                        size="small"
                        component={Link}
                        to={`/admin/modules/${m.name}`}
                      >
                        상세
                      </Button>
                      {/* 인라인 타입이 아니면 전개/전개 해제 버튼 노출 */}
                      {m.env?.toLowerCase() !== "inline" && (
                        <>
                          {m.isDeployed ? (
                            <Button
                              size="small"
                              variant="outlined"
                              color="error"
                              sx={{ ml: 1 }}
                              disabled={undeploying === m.name}
                              onClick={() => handleUndeploy(m.name)}
                            >
                              {undeploying === m.name
                                ? "전개 해제중..."
                                : "전개 해제"}
                            </Button>
                          ) : (
                            <Button
                              size="small"
                              variant="contained"
                              color="secondary"
                              sx={{ ml: 1 }}
                              disabled={deploying === m.name}
                              onClick={() => handleDeploy(m.name)}
                            >
                              {deploying === m.name ? "전개중..." : "전개"}
                            </Button>
                          )}
                        </>
                      )}
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        sx={{ ml: 1 }}
                        onClick={() => setDeleteTarget(m)}
                      >
                        삭제
                      </Button>
                      {deployLog[m.name] && (
                        <div
                          style={{ color: "green", fontSize: 12, marginTop: 4 }}
                        >
                          {deployLog[m.name]}
                        </div>
                      )}
                      {deployError[m.name] && (
                        <div
                          style={{ color: "red", fontSize: 12, marginTop: 4 }}
                        >
                          {deployError[m.name]}
                        </div>
                      )}
                      {undeployLog[m.name] && (
                        <div
                          style={{ color: "green", fontSize: 12, marginTop: 4 }}
                        >
                          {undeployLog[m.name]}
                        </div>
                      )}
                      {undeployError[m.name] && (
                        <div
                          style={{ color: "red", fontSize: 12, marginTop: 4 }}
                        >
                          {undeployError[m.name]}
                        </div>
                      )}
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          setClientCodeModule(m);
                          setClientCodeTab(0);
                          setClientCodeOpen(true);
                        }}
                      >
                        클라이언트 코드
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
        {/* 삭제 확인 다이얼로그 */}
        <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
          <DialogTitle>모듈 삭제 확인</DialogTitle>
          <DialogContent>
            <DialogContentText>
              정말 <b>{deleteTarget?.name}</b> 모듈을 삭제하시겠습니까?
              <br />이 작업은 되돌릴 수 없습니다.
            </DialogContentText>
            {deleteError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {deleteError}
              </Alert>
            )}
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setDeleteTarget(null)}
              disabled={deleteLoading}
            >
              취소
            </Button>
            <Button
              color="error"
              variant="contained"
              disabled={deleteLoading}
              onClick={handleDelete}
            >
              {deleteLoading ? "삭제중..." : "삭제"}
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
      {/* 클라이언트 코드 Dialog */}
      <Dialog
        open={clientCodeOpen}
        onClose={() => setClientCodeOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>클라이언트 코드 예제</DialogTitle>
        <DialogContent>
          <Tabs
            value={clientCodeTab}
            onChange={(_, v) => setClientCodeTab(v)}
            sx={{ mb: 2 }}
          >
            <Tab label="Node.js" />
            <Tab label="Python" />
            <Tab label="Java" />
            <Tab label="curl" />
          </Tabs>
          {clientCodeModule && (
            <Box sx={{ position: "relative", mb: 2 }}>
              <IconButton
                onClick={() => {
                  const code =
                    clientCodeTab === 0
                      ? codeTemplates.node(
                          clientCodeModule.name,
                          clientCodeModule.version
                        )
                      : clientCodeTab === 1
                      ? codeTemplates.python(
                          clientCodeModule.name,
                          clientCodeModule.version
                        )
                      : clientCodeTab === 2
                      ? codeTemplates.java(
                          clientCodeModule.name,
                          clientCodeModule.version
                        )
                      : codeTemplates.curl(
                          clientCodeModule.name,
                          clientCodeModule.version
                        );
                  handleCopy(code);
                }}
                sx={{ position: "absolute", top: 0, right: 0 }}
                size="small"
              >
                <ContentCopyIcon />
              </IconButton>
              <pre
                style={{
                  background: "#f5f5f5",
                  borderRadius: 4,
                  padding: 16,
                  fontSize: 14,
                  overflowX: "auto",
                }}
              >
                {clientCodeTab === 0
                  ? codeTemplates.node(
                      clientCodeModule.name,
                      clientCodeModule.version
                    )
                  : clientCodeTab === 1
                  ? codeTemplates.python(
                      clientCodeModule.name,
                      clientCodeModule.version
                    )
                  : clientCodeTab === 2
                  ? codeTemplates.java(
                      clientCodeModule.name,
                      clientCodeModule.version
                    )
                  : codeTemplates.curl(
                      clientCodeModule.name,
                      clientCodeModule.version
                    )}
              </pre>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClientCodeOpen(false)}>닫기</Button>
        </DialogActions>
      </Dialog>
      <Snackbar
        open={copySnackbar}
        autoHideDuration={1500}
        onClose={() => setCopySnackbar(false)}
        message="복사됨!"
      />
    </div>
  );
};

export default ModuleList;
