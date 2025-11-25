// src/components/Dashboard.jsx

import React, { useState, useCallback } from "react";
import { Box, Typography } from "@mui/material";
import { FileUpload } from "./FileUpload";
import { Visualization } from "./Visualization";
import { uploadAndAnalyzeCsv } from "../api/apiClient";

export const Dashboard = () => {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [topics, setTopics] = useState(""); // New state for topics
  const abortControllerRef = React.useRef(null);

  const handleCancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setUploadProgress(0);
  }, []);

  const handleFileUpload = useCallback(
    async (file) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      setIsLoading(true);
      setError(null);
      setResults(null);
      setUploadProgress(0);

      try {
        const analysisData = await uploadAndAnalyzeCsv(
          file,
          topics,
          (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total,
            );
            setUploadProgress(percentCompleted);
          },
          abortController.signal,
        );
        setResults(analysisData);
      } catch (err) {
        if (err.message === "Analysis cancelled by user.") {
          console.log("Request cancelled");
        } else {
          setError(err.message || "Failed to analyze the file.");
        }
      } finally {
        if (abortControllerRef.current === abortController) {
          setIsLoading(false);
          abortControllerRef.current = null;
        }
      }
    },
    [topics],
  );

  return (
    <Box sx={{ width: "100%", maxWidth: 1400, mx: "auto", my: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Feedback Summarizer - Voice of the Customer Dashboard
      </Typography>
      <Typography variant="body1" paragraph>
        This AI-powered dashboard helps you summarize customer feedback, extract
        key themes, and identify sentiment patterns. Simply upload your CSV file
        containing feedback text and ratings, and the system will cluster
        feedback by topics, perform sentiment analysis
        (positive/negative/neutral), and display summarized insights,
        representative quotes, and interactive charts.
      </Typography>
      <FileUpload
        onFileUpload={handleFileUpload}
        isLoading={isLoading}
        error={error}
        progress={uploadProgress}
        topics={topics}
        onTopicsChange={setTopics}
        onCancel={handleCancel}
      />
      {results && !isLoading && (
        <Visualization results={results} analyzedFilename={results.filename} />
      )}
    </Box>
  );
};
