// src/api/apiClient.js

import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://localhost:8000",
});

/**
 * Uploads a CSV file and returns the analysis results.
 * @param {File} file The CSV file to upload.
 * @param {string} topics A comma-separated string of topics to filter by.
 * @param {(progressEvent: any) => void} onUploadProgress A callback to track progress.
 * @param {AbortSignal} [signal] Optional AbortSignal to cancel the request.
 * @returns {Promise<any>} A promise that resolves to the analysis results object.
 */
export const uploadAndAnalyzeCsv = async (
  file,
  topics,
  columns,
  onUploadProgress,
  signal,
) => {
  const formData = new FormData();
  formData.append("file", file);

  let url = "/api/feedback/analyze";
  const params = new URLSearchParams();
  if (topics && topics.trim() !== "") {
    params.append("topics", topics.trim());
  }
  if (columns && columns.trim() !== "") {
    params.append("columns", columns.trim());
  }

  if (params.toString()) {
    url += `?${params.toString()}`;
  }

  try {
    const response = await apiClient.post(url, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress,
      signal, // Pass the signal to axios
    });
    return response.data;
  } catch (error) {
    if (axios.isCancel(error)) {
      throw new Error("Analysis cancelled by user.");
    }
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(
        error.response.data.detail || "An unexpected error occurred.",
      );
    }
    throw new Error("Network error or server is not responding.");
  }
};

/**
 * Sends analysis data to the backend to generate a PDF report and downloads it.
 * @param {object} analysisData The analysis results data.
 * @returns {Promise<void>}
 */
export const downloadPdfReport = async (analysisData) => {
  try {
    const response = await apiClient.post(
      "/api/feedback/report",
      analysisData,
      {
        responseType: "blob", // Important to handle the binary PDF data
      },
    );

    // Create a URL for the blob
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "feedback_report.pdf"); // or any other filename
    document.body.appendChild(link);
    link.click();

    // Clean up and remove the link
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      // Handle blob error response
      const errorText = await new Response(error.response.data).text();
      const errorJson = JSON.parse(errorText);
      throw new Error(
        errorJson.detail ||
          "An unexpected error occurred while generating the report.",
      );
    }
    throw new Error("Network error or server is not responding.");
  }
};
