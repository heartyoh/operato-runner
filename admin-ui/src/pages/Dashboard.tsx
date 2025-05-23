import React from "react";
import { Typography, Box } from "@mui/material";

const Dashboard: React.FC = () => (
  <Box p={3}>
    <Typography variant="h4" gutterBottom>
      관리자 대시보드
    </Typography>
    <Typography>모듈 관리 시스템에 오신 것을 환영합니다.</Typography>
  </Box>
);

export default Dashboard;
