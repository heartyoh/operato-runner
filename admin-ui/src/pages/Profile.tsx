import React, { useEffect, useState } from "react";
import {
  Paper,
  Typography,
  TextField,
  CircularProgress,
  Alert,
  Button,
  Stack,
  Snackbar,
  Container,
  Box,
} from "@mui/material";
import axios from "axios";

const getRoleString = (user: any) => {
  if (Array.isArray(user.roles)) {
    if (user.roles.length > 0 && typeof user.roles[0] === "object") {
      return user.roles
        .map((r: any) => r.name || r.role || JSON.stringify(r))
        .join(", ");
    }
    return user.roles.join(", ");
  }
  if (typeof user.role === "string") return user.role;
  if (typeof user.role === "object" && user.role.name) return user.role.name;
  return "";
};

const Profile: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editEmail, setEditEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    axios
      .get("/api/profile")
      .then((res) => {
        setUser(res.data);
        setEditEmail(typeof res.data.email === "string" ? res.data.email : "");
      })
      .catch((err) => setError("사용자 정보를 불러올 수 없습니다."))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      // PATCH /api/profile
      await axios.patch("/api/profile", {
        email: editEmail,
      });
      setSuccessMsg("프로필이 저장되었습니다.");
      setUser((u: any) => ({ ...u, email: editEmail }));
      setEditEmail(typeof editEmail === "string" ? editEmail : "");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <CircularProgress sx={{ mt: 4 }} />;
  if (error) return <Alert severity="error">{error}</Alert>;
  if (!user) return null;

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>
        내 프로필
      </Typography>
      <Typography variant="body1" color="textSecondary" gutterBottom>
        내 계정 정보를 확인하고 수정할 수 있습니다.
      </Typography>
      <Box sx={{ mt: 4 }}>
        <Paper sx={{ p: 4, maxWidth: 500, margin: "0 auto" }}>
          <Typography variant="h5" gutterBottom>
            내 프로필
          </Typography>
          <TextField
            label="아이디"
            value={user.username}
            fullWidth
            margin="normal"
            disabled
          />
          <TextField
            label="이메일"
            value={typeof editEmail === "string" ? editEmail : ""}
            onChange={(e) => setEditEmail(e.target.value)}
            fullWidth
            margin="normal"
          />
          <TextField
            label="역할"
            value={getRoleString(user)}
            fullWidth
            margin="normal"
            disabled
          />
          <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <Button variant="contained" onClick={handleSave} disabled={saving}>
              저장
            </Button>
          </Stack>
          <Snackbar
            open={!!successMsg}
            autoHideDuration={2000}
            onClose={() => setSuccessMsg(null)}
            message={successMsg}
          />
        </Paper>
      </Box>
    </Container>
  );
};

export default Profile;
