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
  Tooltip,
  CircularProgress,
  Snackbar,
  Alert,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { BarChart } from "@mui/x-charts/BarChart";
import { PieChart } from "@mui/x-charts/PieChart";
// Импортируем Plot
import Plot from "react-plotly.js";
import { DataGrid } from "@mui/x-data-grid";

import { downloadPdfReport } from "../api/apiClient"; // Импортируем функцию

// === ИЗМЕНЕНИЕ: Импортируем plotly.js-dist-min в глобальную область видимости ===
// Это может быть сделано в index.js вашего приложения для лучшей организации
// import 'plotly.js-dist-min';
// В этом файле мы предполагаем, что Plotly уже доступен через react-plotly.js,
// но если возникнут проблемы, возможно, потребуется явный импорт в index.js

// === ИЗМЕНЕНИЕ: Вспомогательная функция для рендеринга ячеек с подсказками ===
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

// === ИЗМЕНЕНИЕ: Определения колонок ===
const feedbackAnalysisColumns = [
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

const topicDetailColumns = [
  {
    field: "text",
    headerName: "Feedback Text",
    flex: 1,
    renderCell: renderCellWithTooltip,
  },
  { field: "sentiment", headerName: "Sentiment", width: 120 },
];

// === ИЗМЕНЕНИЕ: Палитра цветов для кластеров ===
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

// === НОВОЕ: Вспомогательная функция для вычисления выпуклой оболочки (Graham Scan) ===
const calculateConvexHull = (points) => {
  if (points.length < 3) return points;

  // Вспомогательная функция для определения поворота
  const crossProduct = (o, a, b) => {
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  };

  // Сортируем точки по x, затем по y
  points.sort((a, b) => (a.x !== b.x ? a.x - b.x : a.y - b.y));

  const hull = [];
  // Нижняя оболочка
  for (let i = 0; i < points.length; ++i) {
    while (
      hull.length >= 2 &&
      crossProduct(hull[hull.length - 2], hull[hull.length - 1], points[i]) <= 0
    ) {
      hull.pop();
    }
    hull.push(points[i]);
  }

  // Верхняя оболочка
  const lowerSize = hull.length;
  for (let i = points.length - 2; i >= 0; --i) {
    while (
      hull.length > lowerSize &&
      crossProduct(hull[hull.length - 2], hull[hull.length - 1], points[i]) <= 0
    ) {
      hull.pop();
    }
    hull.push(points[i]);
  }

  // Удаляем дубликат последней точки
  hull.pop();
  return hull;
};

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

  // Обработка данных для кластеров
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
      label: point.phrase,
    });
    return acc;
  }, {});

  // Функция для подготовки данных Plotly
  const preparePlotlyData = () => {
    const plotlyTraces = [];

    Object.keys(clusters).forEach((clusterKey, index) => {
      const points = clusters[clusterKey];
      const color = CLUSTER_COLORS[index % CLUSTER_COLORS.length];

      // 1. Точки кластера
      plotlyTraces.push({
        x: points.map((p) => p.x),
        y: points.map((p) => p.y),
        mode: "markers",
        type: "scatter",
        name: `Cluster ${clusterKey}`,
        text: points.map((p) => p.label),
        hovertemplate:
          "<b>%{text}</b><br>x: %{x:.2f}<br>y: %{y:.2f}<extra></extra>",
        marker: {
          color: color,
          size: 8,
          opacity: 0.8,
        },
      });

      // 2. Граница кластера (convex hull)
      if (points.length >= 3) {
        const hull = calculateConvexHull([...points]);
        // Замыкаем контур
        const hullX = [...hull.map((p) => p.x), hull[0].x];
        const hullY = [...hull.map((p) => p.y), hull[0].y];

        plotlyTraces.push({
          x: hullX,
          y: hullY,
          mode: "lines",
          type: "scatter",
          fill: "toself",
          fillcolor: color + "20", // Добавляем прозрачность
          line: {
            color: color,
            width: 2,
          },
          showlegend: false,
          hoverinfo: "skip",
        });
      } else if (points.length === 2) {
        // Для 2 точек рисуем линию
        plotlyTraces.push({
          x: points.map((p) => p.x),
          y: points.map((p) => p.y),
          mode: "lines",
          type: "scatter",
          line: {
            color: color,
            width: 2,
            dash: "dash",
          },
          showlegend: false,
          hoverinfo: "skip",
        });
      }
    });

    return plotlyTraces;
  };

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

  // Подготовим данные для Plotly один раз при рендере
  const plotlyData = preparePlotlyData();

  // Рассчитаем границы осей для Plotly
  let plotLayout = {};
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

    plotLayout = {
      xaxis: {
        range: [minX - xPadding, maxX + xPadding],
        title: { text: "t-SNE Component 1" },
      },
      yaxis: {
        range: [minY - yPadding, maxY + yPadding],
        title: { text: "t-SNE Component 2" },
      },
      showlegend: true,
      legend: { orientation: "h", xanchor: "center", x: 0.5 },
      margin: { l: 80, r: 50, b: 80, t: 50 },
      dragmode: "pan", // Позволяет перемещать график
    };
  }

  return (
    <Box sx={{ mt: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card variant="outlined">
            <CardContent>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Typography variant="h5">
                  Overall Summary of Customer Feedbacks
                </Typography>
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
              Bar Chart of Topic Distribution
            </Typography>
            <BarChart
              margin={{ bottom: 40 }}
              xAxis={[
                { scaleType: "band", data: topicLabels, label: "Topics" },
              ]}
              yAxis={[{ label: "Number of feedback on the topic" }]}
              series={topicCounts.map((value, index) => {
                const data = Array(topicCounts.length).fill(null);
                data[index] = value;
                return {
                  data,
                  stack: "single",
                  color: CLUSTER_COLORS[index % CLUSTER_COLORS.length],
                  label: topicLabels[index],
                  valueFormatter: (v) => (v === null ? null : v.toString()),
                };
              })}
              tooltip={{ trigger: "item" }}
              legend={{ hidden: true }}
              onItemClick={handleBarClick}
              sx={{ "& .MuiBarElement-root": { cursor: "pointer" } }}
            />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: "400px" }}>
            <Typography variant="h6" gutterBottom>
              Pie Chart of Overall Sentiment Distribution
            </Typography>
            <PieChart
              series={[{ data: sentimentChartData, innerRadius: 60 }]}
            />
          </Paper>
        </Grid>

        {/* КНОПКА ДЛЯ ОТКРЫТИЯ PLOTLY ГРАФИКА */}
        {Object.keys(clusters).length > 0 && (
          <Grid item xs={12}>
            <Button
              variant="outlined"
              onClick={() => setIsClusterDialogOpen(true)}
              fullWidth
            >
              Show Phrase Clusters with Boundaries
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

      {/* Диалог для отображения кластеров Plotly */}
      <Dialog
        open={isClusterDialogOpen}
        onClose={() => setIsClusterDialogOpen(false)}
        fullWidth
        maxWidth="xl"
      >
        <DialogTitle variant="h4">
          Scatter Plot: Phrase-Semantic Clusters with Boundaries
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            The scatter plot shows the position of text embeddings in 2D using
            t-SNE. The axes (t-SNE Component 1 and t-SNE Component 2) are the
            result of applying the t-SNE algorithm to reduce the dimensionality
            of the original vector representations of texts, which allows
            visualizing their semantic proximity in two-dimensional space.
          </Typography>
          <Box sx={{ height: "70vh", width: "100%", mt: 2 }}>
            <Plot
              data={plotlyData}
              layout={plotLayout}
              config={{ displayModeBar: true, responsive: true }}
              style={{ width: "100%", height: "100%" }}
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
