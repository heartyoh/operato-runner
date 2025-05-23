import React, { useEffect, useState } from "react";
import { fetchModules, deployModule, undeployModule } from "../api";
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
} from "@mui/material";
import { useNavigate } from "react-router-dom";

interface Module {
  id: string;
  name: string;
  env: string;
  version: string;
  status?: string;
}

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
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    fetchModules()
      .then((data) => setModules(data))
      .catch((err) => setError(err?.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
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
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>이름</TableCell>
                <TableCell>환경</TableCell>
                <TableCell>버전</TableCell>
                <TableCell>상태</TableCell>
                <TableCell>액션</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {modules.map((m) => (
                <TableRow key={m.id} hover>
                  <TableCell>{m.id}</TableCell>
                  <TableCell>{m.name}</TableCell>
                  <TableCell>{m.env}</TableCell>
                  <TableCell>{m.version}</TableCell>
                  <TableCell>{m.status || "-"}</TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      onClick={() => navigate(`/modules/${m.name}`)}
                    >
                      상세
                    </Button>
                    <Button
                      size="small"
                      variant="contained"
                      color="secondary"
                      sx={{ ml: 1 }}
                      disabled={deploying === m.name}
                      onClick={async () => {
                        setDeploying(m.name);
                        setDeployError((prev) => ({ ...prev, [m.name]: "" }));
                        setDeployLog((prev) => ({ ...prev, [m.name]: "" }));
                        try {
                          const res = await deployModule(m.name);
                          setDeployLog((prev) => ({
                            ...prev,
                            [m.name]: res?.log || "전개 완료",
                          }));
                        } catch (err: any) {
                          setDeployError((prev) => ({
                            ...prev,
                            [m.name]:
                              err?.response?.data?.detail || err.message,
                          }));
                        } finally {
                          setDeploying(null);
                        }
                      }}
                    >
                      {deploying === m.name ? "전개중..." : "전개"}
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      sx={{ ml: 1 }}
                      disabled={undeploying === m.name}
                      onClick={async () => {
                        setUndeploying(m.name);
                        setUndeployError((prev) => ({ ...prev, [m.name]: "" }));
                        setUndeployLog((prev) => ({ ...prev, [m.name]: "" }));
                        try {
                          const res = await undeployModule(m.name);
                          setUndeployLog((prev) => ({
                            ...prev,
                            [m.name]: res?.log || "전개 해제 완료",
                          }));
                        } catch (err: any) {
                          setUndeployError((prev) => ({
                            ...prev,
                            [m.name]:
                              err?.response?.data?.detail || err.message,
                          }));
                        } finally {
                          setUndeploying(null);
                        }
                      }}
                    >
                      {undeploying === m.name ? "전개 해제중..." : "전개 해제"}
                    </Button>
                    {deployLog[m.name] && (
                      <div
                        style={{ color: "green", fontSize: 12, marginTop: 4 }}
                      >
                        {deployLog[m.name]}
                      </div>
                    )}
                    {deployError[m.name] && (
                      <div style={{ color: "red", fontSize: 12, marginTop: 4 }}>
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
                      <div style={{ color: "red", fontSize: 12, marginTop: 4 }}>
                        {undeployError[m.name]}
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
};

export default ModuleList;
