// src/components/Dashboard.jsx

import React, { useState, useCallback } from "react";
import { Box } from "@mui/material";
import { FileUpload } from "./FileUpload";
import { Visualization } from "./Visualization";
import { uploadAndAnalyzeCsv } from "../api/apiClient";

export const Dashboard = () => {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [topics, setTopics] = useState(""); // Новое состояние для топиков

  const handleFileUpload = useCallback(
    async (file) => {
      setIsLoading(true);
      setError(null);
      setResults(null);
      setUploadProgress(0);

      try {
        // Передаем топики в API-клиент
        const analysisData = await uploadAndAnalyzeCsv(
          file,
          topics,
          (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total,
            );
            setUploadProgress(percentCompleted);
          },
        );
        setResults(analysisData);
      } catch (err) {
        setError(err.message || "Failed to analyze the file.");
      } finally {
        setIsLoading(false);
      }
    },
    [topics],
  ); // Добавляем topics в массив зависимостей

  return (
    <Box sx={{ width: "100%", maxWidth: 1400, mx: "auto", my: 4 }}>
      <FileUpload
        onFileUpload={handleFileUpload}
        isLoading={isLoading}
        error={error}
        progress={uploadProgress}
        topics={topics}
        onTopicsChange={setTopics}
      />
      {results && !isLoading && <Visualization results={results} />}
    </Box>
  );
};
