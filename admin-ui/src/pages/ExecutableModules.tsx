import React from "react";
import { Container, Typography, Box } from "@mui/material";
import ExecutableModuleList from "../components/ExecutableModuleList";

const ExecutableModules: React.FC = () => {
  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>
        모듈 실행
      </Typography>
      <Typography variant="body1" color="textSecondary" gutterBottom>
        실행 가능한 모듈들을 검색하고 테스트해보세요.
      </Typography>
      <ExecutableModuleList />
    </Container>
  );
};

export default ExecutableModules;
