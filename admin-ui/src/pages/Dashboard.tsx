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
  Button,
} from "@mui/material";
import Grid from "@mui/material/Grid";
import {
  Widgets as WidgetsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  History as HistoryIcon,
  Dns as DnsIcon,
  PlayArrow as PlayArrowIcon,
  Code as CodeIcon,
  List as ListIcon,
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

interface ExecutableModule {
  name: string;
  env: string;
  version: string;
  description: string;
  visibility: string;
  isDeployed: boolean;
  tags: string[];
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
  const [executableModules, setExecutableModules] = useState<
    ExecutableModule[]
  >([]);
  const [dbStatus, setDbStatus] = useState<DbStatus | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // 병렬로 API 호출
        const [modulesRes, auditRes, healthRes, errorsRes, executableRes] =
          await Promise.all([
            api.fetchModules(),
            api.getAuditLogs({ limit: 5 }),
            api.getDbHealth(),
            api.fetchErrorLogs({
              from: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            }),
            api.fetchExecutableModules(),
          ]);

        setStats({
          totalModules: modulesRes.length,
          activeModules: modulesRes.filter((m: Module) => m.isDeployed).length,
          recentErrors: errorsRes.length,
        });

        setRecentLogs(auditRes);
        setDbStatus(healthRes);
        setRecentModules(modulesRes);
        setExecutableModules(executableRes);
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
          } else if (detail && typeof detail === "object") {
            // 객체인 경우 JSON 문자열로 변환하거나 기본 메시지 사용
            try {
              errorMessage = JSON.stringify(detail);
            } catch {
              errorMessage = "서버에서 오류 응답을 받았습니다.";
            }
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
      <Typography variant="body1" color="textSecondary" gutterBottom>
        전체 시스템 현황과 최근 활동, 상태를 한눈에 확인하세요.
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

      {/* 모듈 섹션 */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          모듈 현황
        </Typography>

        {/* 관리 대상 모듈 섹션 */}
        <Box sx={{ mb: 4 }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 2,
            }}
          >
            <Box>
              <Typography variant="h6" gutterBottom>
                📦 관리 대상 모듈
              </Typography>
              <Typography variant="body2" color="textSecondary">
                내가 관리하는 모듈들과 전체 모듈 현황
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<ListIcon />}
              onClick={() => navigate("/admin/modules")}
            >
              모듈 관리
            </Button>
          </Box>
          <Grid container spacing={2}>
            {loading ? (
              <Grid item xs={12}>
                <Box sx={{ display: "flex", justifyContent: "center", p: 3 }}>
                  <CircularProgress />
                </Box>
              </Grid>
            ) : recentModules.length === 0 ? (
              <Grid item xs={12}>
                <Paper sx={{ p: 3, textAlign: "center" }}>
                  <Typography color="textSecondary">
                    관리할 모듈이 없습니다.
                  </Typography>
                </Paper>
              </Grid>
            ) : (
              recentModules.slice(0, 3).map((module) => (
                <Grid item xs={12} sm={6} md={4} key={module.name}>
                  <Card
                    sx={{
                      height: "100%",
                      cursor: "pointer",
                      "&:hover": { boxShadow: 3 },
                      transition: "box-shadow 0.2s",
                    }}
                    onClick={() => navigate(`/admin/modules/${module.name}`)}
                  >
                    <CardContent>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 1 }}
                      >
                        <CodeIcon sx={{ mr: 1, color: "primary.main" }} />
                        <Typography variant="h6" component="h3" noWrap>
                          {module.name}
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          mb: 1,
                        }}
                      >
                        <Typography variant="caption" color="textSecondary">
                          v{module.version}
                        </Typography>
                        <Chip
                          icon={
                            module.isDeployed ? (
                              <CheckCircleIcon />
                            ) : (
                              <ErrorIcon />
                            )
                          }
                          label={module.isDeployed ? "배포됨" : "미배포"}
                          size="small"
                          color={module.isDeployed ? "success" : "error"}
                        />
                      </Box>
                      <Typography variant="caption" color="textSecondary">
                        생성일:{" "}
                        {new Date(module.created_at).toLocaleDateString()}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        </Box>

        {/* 실행 가능한 모듈 섹션 */}
        <Box sx={{ mb: 4 }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 2,
            }}
          >
            <Box>
              <Typography variant="h6" gutterBottom>
                ▶️ 실행 가능한 모듈
              </Typography>
              <Typography variant="body2" color="textSecondary">
                현재 실행할 수 있는 모듈들 (공개 모듈 + 내 모듈)
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<PlayArrowIcon />}
              onClick={() => navigate("/admin/executable")}
            >
              모듈 실행
            </Button>
          </Box>
          <Grid container spacing={2}>
            {loading ? (
              <Grid item xs={12}>
                <Box sx={{ display: "flex", justifyContent: "center", p: 3 }}>
                  <CircularProgress />
                </Box>
              </Grid>
            ) : executableModules.length === 0 ? (
              <Grid item xs={12}>
                <Paper sx={{ p: 3, textAlign: "center" }}>
                  <Typography color="textSecondary">
                    실행 가능한 모듈이 없습니다.
                  </Typography>
                </Paper>
              </Grid>
            ) : (
              executableModules.slice(0, 6).map((module) => (
                <Grid item xs={12} sm={6} md={4} key={module.name}>
                  <Card
                    sx={{
                      height: "100%",
                      cursor: "pointer",
                      "&:hover": { boxShadow: 3 },
                      transition: "box-shadow 0.2s",
                    }}
                    onClick={() =>
                      navigate(`/admin/executable?module=${module.name}`)
                    }
                  >
                    <CardContent>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 1 }}
                      >
                        <CodeIcon sx={{ mr: 1, color: "primary.main" }} />
                        <Typography variant="h6" component="h3" noWrap>
                          {module.name}
                        </Typography>
                      </Box>
                      <Typography
                        variant="body2"
                        color="textSecondary"
                        sx={{ mb: 1 }}
                      >
                        {module.description || "설명 없음"}
                      </Typography>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 1 }}
                      >
                        <Chip
                          label={module.env}
                          size="small"
                          color="primary"
                          variant="outlined"
                          sx={{ mr: 1 }}
                        />
                        <Chip
                          label={module.visibility}
                          size="small"
                          color={
                            module.visibility === "public"
                              ? "success"
                              : "default"
                          }
                          variant="outlined"
                        />
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}
                      >
                        <Typography variant="caption" color="textSecondary">
                          v{module.version}
                        </Typography>
                        <Chip
                          icon={
                            module.isDeployed ? (
                              <CheckCircleIcon />
                            ) : (
                              <ErrorIcon />
                            )
                          }
                          label={module.isDeployed ? "배포됨" : "미배포"}
                          size="small"
                          color={module.isDeployed ? "success" : "error"}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        </Box>
      </Box>

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
