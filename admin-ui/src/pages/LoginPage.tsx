import React, { useState, useEffect } from "react";
import { Typography, Box, TextField, Button, Alert } from "@mui/material";
import { login } from "../api";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loggedIn, setLoggedIn] = useState(false);
  const [checking, setChecking] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const checkToken = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setChecking(false);
        return;
      }
      try {
        await axios.get("/api/users/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setLoggedIn(true);
        navigate("/dashboard", { replace: true });
      } catch {
        localStorage.removeItem("access_token");
        setChecking(false);
      }
    };
    checkToken();
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const data = await login(username, password);
      localStorage.setItem("access_token", data.access_token);
      setLoggedIn(true);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setLoggedIn(false);
  };

  if (checking) return null;

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        관리자 대시보드
      </Typography>
      <Typography>모듈 관리 시스템에 오신 것을 환영합니다.</Typography>
      {!loggedIn ? (
        <Box
          component="form"
          onSubmit={handleLogin}
          sx={{ mt: 3, maxWidth: 300 }}
        >
          <TextField
            label="아이디"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            fullWidth
            margin="normal"
          />
          <TextField
            label="비밀번호"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            margin="normal"
          />
          <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }}>
            로그인
          </Button>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </Box>
      ) : (
        <Box sx={{ mt: 3 }}>
          <Alert severity="success">로그인됨</Alert>
          <Button variant="outlined" onClick={handleLogout} sx={{ mt: 2 }}>
            로그아웃
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default LoginPage;
