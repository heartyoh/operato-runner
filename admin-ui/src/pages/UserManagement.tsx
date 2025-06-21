import React, { useEffect, useState } from "react";
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
  Alert,
  Box,
  Modal,
  TextField,
  Switch,
  FormControlLabel,
  FormGroup,
  Checkbox,
} from "@mui/material";
import { listUsers, updateUser, deleteUser, createUser } from "../api";

// 임시 타입 정의
interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  roles: { name: string }[];
  created_at: string;
}

const style = {
  position: "absolute" as "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 400,
  bgcolor: "background.paper",
  border: "2px solid #000",
  boxShadow: 24,
  p: 4,
};

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [open, setOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [newUser, setNewUser] = useState({
    username: "",
    email: "",
    password: "",
    roles: [] as string[],
    is_active: true,
  });

  const handleOpen = (user: User | null = null) => {
    if (user) {
      setEditingUser(user);
      setNewUser({
        username: user.username,
        email: user.email,
        password: "",
        roles: user.roles.map((r) => r.name),
        is_active: user.is_active,
      });
    } else {
      setEditingUser(null);
      setNewUser({
        username: "",
        email: "",
        password: "",
        roles: [],
        is_active: true,
      });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingUser(null);
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await listUsers();
      setUsers(data);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || "사용자 목록을 불러올 수 없습니다."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleDeleteUser = async (userId: number) => {
    if (window.confirm("정말로 이 사용자를 삭제하시겠습니까?")) {
      try {
        await deleteUser(userId);
        fetchUsers(); // 목록 새로고침
      } catch (err: any) {
        setError(err?.response?.data?.detail || "사용자 삭제에 실패했습니다.");
      }
    }
  };

  const handleSaveUser = async () => {
    const roles = newUser.roles.map((r) => r.trim()).filter((r) => r);
    try {
      if (editingUser) {
        await updateUser(editingUser.id, {
          email: newUser.email,
          is_active: newUser.is_active,
          roles: roles,
        });
      } else {
        await createUser({
          ...newUser,
          roles: roles,
        });
      }
      fetchUsers();
      handleClose();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      let message = "작업에 실패했습니다.";

      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail)) {
        // FastAPI validation error format
        message = detail.map((d) => `${d.loc.join(".")}: ${d.msg}`).join(", ");
      } else if (detail && typeof detail === "object") {
        // 객체인 경우 JSON 문자열로 변환하거나 기본 메시지 사용
        try {
          message = JSON.stringify(detail);
        } catch {
          message = "서버에서 오류 응답을 받았습니다.";
        }
      }

      setError(message);
    }
  };

  return (
    <Paper sx={{ p: 3, mt: 4 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}>
        <Typography variant="h5" gutterBottom>
          사용자 관리
        </Typography>
        <Button variant="contained" onClick={() => handleOpen()}>
          신규 사용자 추가
        </Button>
      </Box>

      <Modal
        open={open}
        onClose={handleClose}
        aria-labelledby="modal-modal-title"
      >
        <Box sx={style}>
          <Typography id="modal-modal-title" variant="h6" component="h2">
            {editingUser ? "사용자 정보 수정" : "신규 사용자 정보"}
          </Typography>
          <TextField
            margin="normal"
            required
            fullWidth
            label="사용자명"
            value={newUser.username}
            disabled={!!editingUser}
            onChange={(e) =>
              setNewUser({ ...newUser, username: e.target.value })
            }
          />
          <TextField
            margin="normal"
            required
            fullWidth
            label="이메일"
            value={newUser.email}
            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
          />
          {!editingUser && (
            <TextField
              margin="normal"
              required
              fullWidth
              label="비밀번호"
              type="password"
              onChange={(e) =>
                setNewUser({ ...newUser, password: e.target.value })
              }
            />
          )}
          <FormGroup sx={{ mt: 2 }}>
            <Typography variant="subtitle1">역할</Typography>
            <FormControlLabel
              control={
                <Checkbox
                  checked={newUser.roles.includes("admin")}
                  onChange={(e) => {
                    const newRoles = e.target.checked
                      ? [...newUser.roles, "admin"]
                      : newUser.roles.filter((r) => r !== "admin");
                    setNewUser({ ...newUser, roles: newRoles });
                  }}
                />
              }
              label="Admin"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={newUser.roles.includes("user")}
                  onChange={(e) => {
                    const newRoles = e.target.checked
                      ? [...newUser.roles, "user"]
                      : newUser.roles.filter((r) => r !== "user");
                    setNewUser({ ...newUser, roles: newRoles });
                  }}
                />
              }
              label="User"
            />
          </FormGroup>
          {editingUser && (
            <FormControlLabel
              control={
                <Switch
                  checked={newUser.is_active}
                  onChange={(e) =>
                    setNewUser({ ...newUser, is_active: e.target.checked })
                  }
                />
              }
              label="활성 상태"
            />
          )}
          <Button
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            onClick={handleSaveUser}
          >
            저장
          </Button>
        </Box>
      </Modal>

      {loading && <CircularProgress />}
      {error && <Alert severity="error">{error}</Alert>}
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>사용자명</TableCell>
              <TableCell>이메일</TableCell>
              <TableCell>역할</TableCell>
              <TableCell>활성 상태</TableCell>
              <TableCell>생성일</TableCell>
              <TableCell>작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.id}</TableCell>
                <TableCell>{user.username}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  {user.roles.map((r) => r.name).join(", ")}
                </TableCell>
                <TableCell>{user.is_active ? "활성" : "비활성"}</TableCell>
                <TableCell>
                  {new Date(user.created_at).toLocaleString()}
                </TableCell>
                <TableCell>
                  <Button
                    size="small"
                    variant="outlined"
                    sx={{ mr: 1 }}
                    onClick={() => handleOpen(user)}
                  >
                    수정
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="error"
                    onClick={() => handleDeleteUser(user.id)}
                  >
                    삭제
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default UserManagement;
