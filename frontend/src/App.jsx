// src/App.jsx

import React from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { AppBar, Toolbar, Typography, Container } from "@mui/material";
import { Dashboard } from "./components/Dashboard";

const darkTheme = createTheme({
  palette: {
    mode: "dark",
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div">
            AI Feedback Analysis Dashboard
          </Typography>
        </Toolbar>
      </AppBar>
      <Container component="main">
        <Dashboard />
      </Container>
    </ThemeProvider>
  );
}

export default App;
