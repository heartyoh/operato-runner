import React from "react";
import { Typography, Box, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        width: "100%",
        marginTop: 40,
      }}
    >
      <Box
        p={3}
        sx={{
          minWidth: 800,
          maxWidth: "90vw",
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <Typography variant="h4" gutterBottom>
          관리자 대시보드
        </Typography>
        <Typography sx={{ mb: 3 }}>
          모듈 관리 시스템에 오신 것을 환영합니다.
          <br />
          아래에서 주요 기능으로 바로 이동할 수 있습니다.
        </Typography>
        <Button
          variant="contained"
          onClick={() => navigate("/dashboard/modules")}
        >
          모듈 목록 바로가기
        </Button>
        <Button
          variant="outlined"
          sx={{ ml: 2 }}
          onClick={() => navigate("/dashboard/modules/upload")}
        >
          모듈 업로드
        </Button>
        <Button
          variant="outlined"
          sx={{ ml: 2 }}
          onClick={() => navigate("/dashboard/admin/error-logs")}
        >
          에러 로그
        </Button>
      </Box>
    </div>
  );
};

export default Dashboard;
export {};
