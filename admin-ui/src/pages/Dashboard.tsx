import React, { useEffect, useState } from "react";
import {
  Typography,
  Box,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Paper,
  CircularProgress,
} from "@mui/material";
import Grid from "@mui/material/Grid";
import {
  Widgets as WidgetsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  History as HistoryIcon,
  Dns as DnsIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useError } from "../contexts/ErrorContext";

// 임시 데이터 타입
interface AuditLog {
  id: number;
  action: string;
  detail: string;
  created_at: string;
}

interface Module {
  name: string;
  version: string;
  created_at: string;
  isDeployed: boolean;
}

interface DbStatus {
  status: "ok" | "error";
  detail?: string;
}

const StatCard: React.FC<{
  title: string;
  value: string | number;
  loading?: boolean;
  onClick?: () => void;
}> = ({ title, value, loading, onClick }) => (
  <Card
    onClick={onClick}
    sx={{ cursor: onClick ? "pointer" : "default", height: "100%" }}
  >
    <CardContent>
      <Typography color="textSecondary" gutterBottom>
        {title}
      </Typography>
      <Typography variant="h5" component="h2">
        {loading ? <CircularProgress size={24} /> : value}
      </Typography>
    </CardContent>
  </Card>
);

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const { setError } = useError();
  const [stats, setStats] = useState({
    totalModules: 0,
    activeModules: 0,
    recentErrors: 0,
  });
  const [recentLogs, setRecentLogs] = useState<AuditLog[]>([]);
  const [recentModules, setRecentModules] = useState<Module[]>([]);
  const [dbStatus, setDbStatus] = useState<DbStatus | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // 병렬로 API 호출
        const [modulesRes, auditRes, healthRes, errorsRes] = await Promise.all([
          api.fetchModules(),
          api.getAuditLogs({ limit: 5 }),
          api.getDbHealth(),
          api.fetchErrorLogs({
            from: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          }),
        ]);

        setStats({
          totalModules: modulesRes.length,
          activeModules: modulesRes.filter((m: Module) => m.isDeployed).length,
          recentErrors: errorsRes.length,
        });

        setRecentLogs(auditRes);
        setDbStatus(healthRes);
        setRecentModules(modulesRes);
      } catch (err: any) {
        if (err?.response?.status === 403) {
          setError("대시보드에 접근할 권한이 없습니다. 관리자에게 문의하세요.");
        } else {
          let errorMessage =
            "데이터를 불러오는 중 알 수 없는 오류가 발생했습니다.";
          const detail = err?.response?.data?.detail;
          if (typeof detail === "string") {
            errorMessage = detail;
          } else if (Array.isArray(detail) && detail[0]?.msg) {
            errorMessage = detail
              .map((d) => `${d.loc.join(".")} - ${d.msg}`)
              .join("; ");
          } else if (err.message) {
            errorMessage = err.message;
          }
          setError(errorMessage);
        }
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, [setError]);

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        대시보드
      </Typography>

      {/* KPI 통계 카드 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <StatCard
            title="총 모듈 수"
            value={stats.totalModules}
            loading={loading}
            onClick={() => navigate("/admin/modules")}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <StatCard
            title="활성 모듈 수"
            value={stats.activeModules}
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <StatCard
            title="최근 24시간 에러"
            value={stats.recentErrors}
            loading={loading}
            onClick={() => navigate("/admin/error-logs")}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* 최근 활동 로그 */}
        <Grid item xs={12} md={8}>
          <Paper
            elevation={2}
            onClick={() => navigate("/admin/audit-logs")}
            sx={{ cursor: "pointer", height: "100%" }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom>
                최근 활동 로그
              </Typography>
              <List>
                {recentLogs.map((log) => (
                  <ListItem key={log.id}>
                    <ListItemIcon>
                      <HistoryIcon />
                    </ListItemIcon>
                    <ListItemText primary={log.action} secondary={log.detail} />
                    <Typography variant="body2" color="textSecondary">
                      {new Date(log.created_at).toLocaleString()}
                    </Typography>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Paper>
        </Grid>

        {/* 시스템 상태 */}
        <Grid item xs={12} md={4}>
          <Paper elevation={2} sx={{ height: "100%" }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                시스템 상태
              </Typography>
              {loading ? (
                <CircularProgress size={20} />
              ) : (
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <DnsIcon
                        color={dbStatus?.status === "ok" ? "success" : "error"}
                      />
                    </ListItemIcon>
                    <ListItemText primary="데이터베이스" />
                    <Chip
                      icon={
                        dbStatus?.status === "ok" ? (
                          <CheckCircleIcon />
                        ) : (
                          <ErrorIcon />
                        )
                      }
                      label={dbStatus?.status === "ok" ? "정상" : "오류"}
                      color={dbStatus?.status === "ok" ? "success" : "error"}
                      size="small"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <WidgetsIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary="API 서버" />
                    <Chip
                      icon={<CheckCircleIcon />}
                      label="정상"
                      color="success"
                      size="small"
                    />
                  </ListItem>
                </List>
              )}
            </CardContent>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
