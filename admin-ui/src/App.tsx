import React from "react";
import { BrowserRouter as Router } from "react-router-dom";
import AppRouter from "./AppRouter";
import { CssBaseline } from "@mui/material";
import { ErrorProvider } from "./contexts/ErrorContext";

const App: React.FC = () => {
  return (
    <ErrorProvider>
      <Router>
        <CssBaseline />
        <AppRouter />
      </Router>
    </ErrorProvider>
  );
};

export default App;
