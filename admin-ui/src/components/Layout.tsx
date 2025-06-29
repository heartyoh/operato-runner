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
  CheckCircle as CheckCircleIcon,
  AccountCircle,
} from "@mui/icons-material";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useError } from "../contexts/ErrorContext";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Avatar from "@mui/material/Avatar";
import IconButton from "@mui/material/IconButton";
import axios from "axios";
import Stack from "@mui/material/Stack";

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
  {
    text: "검증 로그",
    path: "/admin/validation-logs",
    icon: <CheckCircleIcon />,
  },
];

const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { error, clearError } = useError();

  // 사용자 정보 상태
  const [user, setUser] = React.useState<any>(null);
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  React.useEffect(() => {
    axios
      .get("/api/profile")
      .then((res) => setUser(res.data))
      .catch(() => setUser(null));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login");
  };

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };
  const handleProfile = () => {
    handleClose();
    navigate("/admin/profile"); // 또는 /admin/users/me 등
  };

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar
        position="fixed"
        sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Operato Runner
          </Typography>
          {/* 사용자 정보 및 메뉴 */}
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              cursor: "pointer",
              borderRadius: 2,
              px: 1.5,
              py: 0.5,
              transition: "background 0.2s",
              "&:hover": { background: "rgba(255,255,255,0.08)" },
            }}
            onClick={handleMenu}
          >
            <Avatar sx={{ width: 32, height: 32, bgcolor: "#1976d2", mr: 1 }}>
              {user && user.username ? user.username[0].toUpperCase() : "U"}
            </Avatar>
            <Typography variant="body1" sx={{ color: "#fff" }}>
              {user && user.username ? user.username : "사용자"}
            </Typography>
          </Box>
          <Menu
            id="menu-appbar"
            anchorEl={anchorEl}
            anchorOrigin={{ vertical: "top", horizontal: "right" }}
            keepMounted
            transformOrigin={{ vertical: "top", horizontal: "right" }}
            open={open}
            onClose={handleClose}
          >
            <MenuItem onClick={handleProfile}>내 프로필</MenuItem>
            <MenuItem onClick={handleLogout}>로그아웃</MenuItem>
          </Menu>
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
