import React, { useEffect, useState } from "react";
import { fetchModules } from "../api";
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
