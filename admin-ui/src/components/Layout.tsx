import React from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
} from "@mui/material";
import { Link, Outlet, useLocation } from "react-router-dom";

const navItems = [
  { label: "대시보드", path: "/dashboard" },
  { label: "모듈 목록", path: "/dashboard/modules" },
  { label: "모듈 업로드", path: "/dashboard/modules/upload" },
  { label: "에러 로그", path: "/dashboard/admin/error-logs" },
];

const Layout: React.FC = () => {
  const location = useLocation();
  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Operato 관리자
          </Typography>
          {navItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              component={Link}
              to={item.path}
              sx={{
                fontWeight:
                  location.pathname === item.path ? "bold" : undefined,
                textDecoration:
                  location.pathname === item.path ? "underline" : undefined,
              }}
            >
              {item.label}
            </Button>
          ))}
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Outlet />
      </Container>
    </Box>
  );
};

export default Layout;
