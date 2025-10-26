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
 * @returns {Promise<any>} A promise that resolves to the analysis results object.
 */
export const uploadAndAnalyzeCsv = async (file, topics, onUploadProgress) => {
  const formData = new FormData();
  formData.append("file", file);

  // Формируем URL с параметрами
  let url = "/api/feedback/analyze/";
  if (topics && topics.trim() !== "") {
    // encodeURIComponent важен, чтобы безопасно передавать спецсимволы
    url += `?topics=${encodeURIComponent(topics.trim())}`;
  }

  try {
    const response = await apiClient.post(url, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(
        error.response.data.detail || "An unexpected error occurred.",
      );
    }
    throw new Error("Network error or server is not responding.");
  }
};
