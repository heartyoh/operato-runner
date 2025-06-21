import React from "react";
import { BrowserRouter } from "react-router-dom";
import { CssBaseline } from "@mui/material";
import AppRouter from "./router";
import { ErrorProvider } from "./contexts/ErrorContext";

function App() {
  return (
    <BrowserRouter>
      <ErrorProvider>
        <CssBaseline />
        <AppRouter />
      </ErrorProvider>
    </BrowserRouter>
  );
}

export default App;
