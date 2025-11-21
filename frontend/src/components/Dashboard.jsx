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
    // Optionally, you might want to keep the previous error or set a specific "Cancelled" message
    // setError("Analysis cancelled."); 
  }, []);

  const handleFileUpload = useCallback(
    async (file) => {
      // Cancel any pending request before starting a new one
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
        // Pass topics and signal to the API client
        const analysisData = await uploadAndAnalyzeCsv(
          file,
          topics,
          (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total,
            );
            setUploadProgress(percentCompleted);
          },
          abortController.signal
        );
        setResults(analysisData);
      } catch (err) {
        if (err.message === "Analysis cancelled by user.") {
             // Verify if this specific cancellation matches the current operation
             // (though we usually reset isLoading in handleCancel directly)
             console.log("Request cancelled");
        } else {
            setError(err.message || "Failed to analyze the file.");
        }
      } finally {
        // Only turn off loading if it wasn't cancelled manually (which handles its own state)
        // OR just turn it off here. If cancelled, handleCancel turns it off. 
        // However, due to async nature, if we cancel, this finally block might run after handleCancel.
        // Check if we are still "loading" according to the ref (if ref is null, we cancelled).
        if (abortControllerRef.current === abortController) {
             setIsLoading(false);
             abortControllerRef.current = null;
        }
      }
    },
    [topics],
  ); // Добавляем topics в массив зависимостей

  return (
    <Box sx={{ width: "100%", maxWidth: 1400, mx: "auto", my: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Feedback Summarizer - Voice of the Customer Dashboard
      </Typography>
      <Typography variant="body1" paragraph>
        This AI-powered dashboard helps you summarize customer feedback, extract key themes, and identify sentiment patterns.
        Simply upload your CSV file containing feedback text and ratings, and the system will cluster feedback by topics, perform sentiment analysis (positive/negative/neutral),
        and display summarized insights, representative quotes, and interactive charts.
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
