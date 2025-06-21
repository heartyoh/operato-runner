import React from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Box,
  Container,
  ListItemButton,
  Alert,
} from "@mui/material";
import {
  Dashboard as DashboardIcon,
  List as ListIcon,
  People as PeopleIcon,
  Logout as LogoutIcon,
  UploadFile as UploadFileIcon,
  ErrorOutline as ErrorOutlineIcon,
  History as HistoryIcon,
} from "@mui/icons-material";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useError } from "../contexts/ErrorContext";

const drawerWidth = 240;

const menuItems = [
  { text: "대시보드", path: "/admin", icon: <DashboardIcon /> },
  { text: "모듈 관리", path: "/admin/modules", icon: <ListIcon /> },
  {
    text: "신규 모듈 업로드",
    path: "/admin/modules/upload",
    icon: <UploadFileIcon />,
  },
  { text: "사용자 관리", path: "/admin/users", icon: <PeopleIcon /> },
  {
    text: "에러 로그",
    path: "/admin/error-logs",
    icon: <ErrorOutlineIcon />,
  },
  { text: "감사 로그", path: "/admin/audit-logs", icon: <HistoryIcon /> },
];

const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { error, clearError } = useError();

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login");
  };

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar
        position="fixed"
        sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            Operato Runner
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: "auto" }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.path} disablePadding>
                <ListItemButton
                  component={Link}
                  to={item.path}
                  selected={location.pathname === item.path}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
            <ListItem disablePadding>
              <ListItemButton onClick={handleLogout}>
                <ListItemIcon>
                  <LogoutIcon />
                </ListItemIcon>
                <ListItemText primary="로그아웃" />
              </ListItemButton>
            </ListItem>
          </List>
        </Box>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Container maxWidth="xl">
          {error && (
            <Alert severity="error" onClose={clearError} sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;
