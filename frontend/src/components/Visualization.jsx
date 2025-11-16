// src/components/Visualization.jsx

import React, { useState } from "react";

import PropTypes from "prop-types";

import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tooltip, // === ИЗМЕНЕНИЕ: Импортируем Tooltip ===
  CircularProgress,
  Snackbar,
  Alert,
} from "@mui/material";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import { BarChart } from "@mui/x-charts/BarChart";

import { PieChart } from "@mui/x-charts/PieChart";

import { ScatterChart } from "@mui/x-charts/ScatterChart";

import { DataGrid } from "@mui/x-data-grid";

import { downloadPdfReport } from "../api/apiClient"; // Импортируем функцию

// === ИЗМЕНЕНИЕ: Создаем вспомогательную функцию для рендеринга ячеек с подсказками ===

// Это поможет избежать дублирования кода.

const renderCellWithTooltip = (params) => (
  <Tooltip title={params.value} placement="bottom-start">
    <Box
      sx={{
        whiteSpace: "nowrap",

        overflow: "hidden",

        textOverflow: "ellipsis",
      }}
    >
      {params.value}
    </Box>
  </Tooltip>
);

// === ИЗМЕНЕНИЕ: Обновляем определения колонок ===

const feedbackAnalysisColumns = [
  // Используем flex: 1, чтобы колонка растягивалась, и добавляем renderCell для подсказки

  {
    field: "text",

    headerName: "Feedback Text",

    flex: 1,

    minWidth: 300,

    renderCell: renderCellWithTooltip,
  },

  { field: "topic", headerName: "Topic", width: 180 },

  { field: "sentiment", headerName: "Sentiment", width: 120 },
];

const feedbackRepliesColumns = [
  {
    field: "feedback_text",

    headerName: "Original Feedback",

    flex: 1,

    minWidth: 250,

    renderCell: renderCellWithTooltip,
  },

  {
    field: "feedback_reply",

    headerName: "AI Generated Reply",

    flex: 1,

    minWidth: 250,

    renderCell: renderCellWithTooltip,
  },

  { field: "score", headerName: "Score", width: 100 },
];

const topicDetailColumns = [
  {
    field: "text",

    headerName: "Feedback Text",

    flex: 1,

    renderCell: renderCellWithTooltip,
  },

  { field: "sentiment", headerName: "Sentiment", width: 120 },
];

// === ИЗМЕНЕНИЕ: Добавляем палитру цветов для кластеров ===

const CLUSTER_COLORS = [
  "#1f77b4",
  "#ff7f0e",
  "#2ca02c",
  "#d62728",
  "#9467bd",
  "#8c564b",

  "#e377c2",
  "#7f7f7f",
  "#bcbd22",
  "#17becf",
  "#aec7e8",
  "#ffbb78",

  "#98df8a",
  "#ff9896",
  "#c5b0d5",
  "#c49c94",
  "#f7b6d2",
  "#c7c7c7",

  "#dbdb8d",
  "#9edae5",
  "#393b79",
  "#637939",
  "#8c6d31",
  "#843c39",

  "#7b4173",
  "#5254a3",
  "#6b6ecf",
  "#9c9ede",
  "#637939",
  "#8ca252",

  "#b5cf6b",
  "#cedb9c",
  "#8c6d31",
  "#bd9e39",
  "#e7ba52",
  "#e7cb94",

  "#843c39",
  "#ad494a",
  "#d6616b",
  "#e7969c",
  "#7b4173",
  "#a55194",

  "#ce6dbd",
  "#de9ed6",
];

export const Visualization = ({ results }) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const [selectedTopicData, setSelectedTopicData] = useState(null);

  const [isClusterDialogOpen, setIsClusterDialogOpen] = useState(false);

  const [isDownloading, setIsDownloading] = useState(false);

  const [error, setError] = useState(null);

  const topicLabels = results.topics.map((t) => t.topic);

  const topicCounts = results.topics.map((t) => t.count);

  const sentimentChartData = [
    {
      id: 0,

      value: results.sentiment.positive,

      label: "Positive",

      color: "#4caf50",
    },

    {
      id: 1,

      value: results.sentiment.negative,

      label: "Negative",

      color: "#f44336",
    },

    {
      id: 2,

      value: results.sentiment.neutral,

      label: "Neutral",

      color: "#ff9800",
    },
  ];

  const feedbackAnalysisRows = results.feedback_analysis.map((row, index) => ({
    ...row,

    id: index,
  }));

  const feedbackRepliesRows = results.feedback_replies.map((row, index) => ({
    ...row,

    id: index,
  }));

  // Обработка данных для ScatterChart

  const clusterData = results.phrase_clusters || [];

  const clusters = clusterData.reduce((acc, point) => {
    const cluster = point.cluster;

    if (!acc[cluster]) {
      acc[cluster] = [];
    }

    acc[cluster].push({
      x: point.x,

      y: point.y,

      id: point.phrase,

      label: point.phrase, // Добавляем label для отображения во всплывающей подсказке
    });

    return acc;
  }, {});

  const scatterSeries = Object.keys(clusters).map((clusterKey) => ({
    label: `Cluster ${clusterKey}`,

    data: clusters[clusterKey],
  }));

  // Рассчитываем границы осей с отступами для графика кластеров

  const axisConfig = {};

  if (clusterData.length > 0) {
    const xValues = clusterData.map((p) => p.x);

    const yValues = clusterData.map((p) => p.y);

    const minX = Math.min(...xValues);

    const maxX = Math.max(...xValues);

    const minY = Math.min(...yValues);

    const maxY = Math.max(...yValues);

    // Добавляем 10% отступ с каждой стороны

    const xPadding = (maxX - minX) * 0.1 || 0.1;

    const yPadding = (maxY - minY) * 0.1 || 0.1;

    axisConfig.xAxis = [
      { min: minX - xPadding, max: maxX + xPadding, hide: true },
    ];

    axisConfig.yAxis = [
      { min: minY - yPadding, max: maxY + yPadding, hide: true },
    ];
  }

  const handleBarClick = (event, d) => {
    if (!d || d.dataIndex === undefined) return;

    const clickedTopic = results.topics[d.dataIndex];

    if (!clickedTopic) return;

    const relevantFeedback = results.feedback_analysis.filter(
      (feedback) => feedback.topic === clickedTopic.topic,
    );

    const topicSentiments = relevantFeedback.reduce(
      (acc, curr) => {
        if (curr.sentiment === "Positive") acc.positive += 1;
        else if (curr.sentiment === "Negative") acc.negative += 1;
        else if (curr.sentiment === "Neutral") acc.neutral += 1;

        return acc;
      },

      { positive: 0, negative: 0, neutral: 0 },
    );

    setSelectedTopicData({
      ...clickedTopic,

      sentiments: topicSentiments,

      feedback: relevantFeedback.map((fb, index) => ({ ...fb, id: index })),
    });

    setIsDialogOpen(true);
  };

  const handleDownload = async () => {
    setIsDownloading(true);

    setError(null);

    try {
      await downloadPdfReport(results);
    } catch (err) {
      setError(err.message || "Failed to download the report.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      {/* Весь остальной JSX остается без изменений */}

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h5">Overall Summary</Typography>

              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Typography variant="h5">Overall Summary</Typography>

                <Button
                  variant="contained"
                  onClick={handleDownload}
                  disabled={isDownloading}
                  startIcon={
                    isDownloading ? <CircularProgress size={20} /> : null
                  }
                >
                  {isDownloading ? "Downloading..." : "Download Report"}
                </Button>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Typography variant="body1">{results.summary}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: "400px" }}>
            <Typography variant="h6" gutterBottom>
              Topic Distribution
            </Typography>

            <BarChart
              xAxis={[{ scaleType: "band", data: topicLabels }]}
              series={[{ data: topicCounts }]}
              layout="vertical"
              onItemClick={handleBarClick}
              sx={{ "& .MuiBarElement-root": { cursor: "pointer" } }}
            />
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: "400px" }}>
            <Typography variant="h6" gutterBottom>
              Overall Sentiment
            </Typography>

            <PieChart
              series={[{ data: sentimentChartData, innerRadius: 60 }]}
            />
          </Paper>
        </Grid>

        {scatterSeries.length > 0 && (
          <Grid item xs={12}>
            <Button
              variant="outlined"
              onClick={() => setIsClusterDialogOpen(true)}
              fullWidth
            >
              Show Phrase Clusters
            </Button>
          </Grid>
        )}

        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
            Topic Summaries
          </Typography>

          {results.topics.map((topic, index) => (
            <Accordion key={index}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography sx={{ width: "50%", flexShrink: 0 }}>
                  {topic.topic}
                </Typography>

                <Typography sx={{ color: "text.secondary" }}>
                  Feedback Count: {topic.count}
                </Typography>
              </AccordionSummary>

              <AccordionDetails>
                <Typography>{topic.summary}</Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
            Detailed Feedback Analysis
          </Typography>

          <Paper sx={{ height: 400, width: "100%" }}>
            <DataGrid
              rows={feedbackAnalysisRows}
              columns={feedbackAnalysisColumns}
              pageSizeOptions={[5, 10, 20]}
            />
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
            Generated AI Replies
          </Typography>

          <Paper sx={{ height: 400, width: "100%" }}>
            <DataGrid
              rows={feedbackRepliesRows}
              columns={feedbackRepliesColumns}
              pageSizeOptions={[5, 10, 20]}
            />
          </Paper>
        </Grid>
      </Grid>

      {selectedTopicData && (
        <Dialog
          open={isDialogOpen}
          onClose={() => setIsDialogOpen(false)}
          fullWidth
          maxWidth="md"
        >
          <DialogTitle variant="h4">
            Details for Topic: "{selectedTopicData.topic}"
          </DialogTitle>

          <DialogContent>
            <Box sx={{ my: 2 }}>
              <Typography variant="h6" gutterBottom>
                Summary for this Topic
              </Typography>

              <Typography variant="body1" color="text.secondary">
                {selectedTopicData.summary}
              </Typography>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ my: 2 }}>
              <Typography variant="h6" gutterBottom>
                Sentiment Distribution for this Topic
              </Typography>

              <Grid container spacing={2}>
                <Grid item>
                  Positive: {selectedTopicData.sentiments.positive}
                </Grid>

                <Grid item>
                  Negative: {selectedTopicData.sentiments.negative}
                </Grid>

                <Grid item>
                  Neutral: {selectedTopicData.sentiments.neutral}
                </Grid>
              </Grid>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ height: 400, width: "100%", mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Relevant Feedback
              </Typography>

              <DataGrid
                rows={selectedTopicData.feedback}
                columns={topicDetailColumns}
                pageSizeOptions={[5, 10]}
              />
            </Box>
          </DialogContent>

          <DialogActions>
            <Button onClick={() => setIsDialogOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      )}

      <Dialog
        open={isClusterDialogOpen}
        onClose={() => setIsClusterDialogOpen(false)}
        fullWidth
        maxWidth="xl"
      >
        <DialogTitle variant="h4">Phrase-Semantic Clusters</DialogTitle>

        <DialogContent>
          <Box sx={{ height: "70vh", width: "100%", mt: 2 }}>
            <ScatterChart
              colors={CLUSTER_COLORS}
              series={scatterSeries.map((s) => ({
                ...s,

                valueFormatter: (point) =>
                  `${point.label} (${point.x.toFixed(2)}, ${point.y.toFixed(
                    2,
                  )})`,
              }))}
              {...axisConfig}
              legend={{
                direction: "row",

                position: { vertical: "top", horizontal: "middle" },
              }}
            />
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setIsClusterDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          onClose={() => setError(null)}
          severity="error"
          sx={{ width: "100%" }}
        >
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

Visualization.propTypes = {
  results: PropTypes.shape({
    summary: PropTypes.string,

    sentiment: PropTypes.object,

    topics: PropTypes.arrayOf(
      PropTypes.shape({
        topic: PropTypes.string,

        count: PropTypes.number,

        summary: PropTypes.string,
      }),
    ),

    quotes: PropTypes.array,

    feedback_analysis: PropTypes.array,

    feedback_replies: PropTypes.array,

    phrase_clusters: PropTypes.arrayOf(
      PropTypes.shape({
        x: PropTypes.number,

        y: PropTypes.number,

        cluster: PropTypes.number,

        phrase: PropTypes.string,
      }),
    ),
  }).isRequired,
};
