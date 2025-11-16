// src/components/Visualization.jsx

import React, { useState } from "react";
import PropTypes from "prop-types";
import Plot from "react-plotly.js"; // ИМПОРТ PLOTLY
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
// ScatterChart больше не используется
import { DataGrid } from "@mui/x-data-grid";
import { downloadPdfReport } from "../api/apiClient";

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

  const clusterDataFor2D = (results.phrase_clusters || []).reduce(
    (acc, point) => {
      const clusterId = point.cluster;
      if (!acc[clusterId]) {
        acc[clusterId] = {
          x: [],
          y: [],
          text: [],
          mode: "markers",
          type: "scatter", // Изменено на scatter для 2D
          name: `Cluster ${clusterId}`,
          marker: { size: 5 },
        };
      }
      acc[clusterId].x.push(point.x);
      acc[clusterId].y.push(point.y);
      acc[clusterId].text.push(point.phrase);
      return acc;
    },
  );

  const plotlyData = Object.values(clusterDataFor2D);
  const hasClusterData = plotlyData.length > 0;

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

        {hasClusterData && (
          <Grid item xs={12}>
            <Button
              variant="outlined"
              onClick={() => setIsClusterDialogOpen(true)}
              fullWidth
            >
              Show Phrase Clusters (2D)
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

      {/* === ИЗМЕНЕНИЕ: Диалоговое окно с 3D-графиком Plotly === */}
      <Dialog
        open={isClusterDialogOpen}
        onClose={() => setIsClusterDialogOpen(false)}
        fullWidth
        maxWidth="xl"
      >
        <DialogTitle variant="h4">Phrase-Semantic Clusters (2D)</DialogTitle>
        <DialogContent>
          <Box sx={{ height: "70vh", width: "100%", mt: 2 }}>
            <Plot
              data={plotlyData}
              layout={{
                title: {
                  text: "2D UMAP Visualization", // Изменено на 2D
                  font: { color: "#e0e0e0" },
                },
                autosize: true,
                paper_bgcolor: "#1a1a1a",
                plot_bgcolor: "#1a1a1a",
                xaxis: { title: "X", backgroundcolor: "#333", gridcolor: "#444", zerolinecolor: "#555", color: "#e0e0e0" },
                yaxis: { title: "Y", backgroundcolor: "#333", gridcolor: "#444", zerolinecolor: "#555", color: "#e0e0e0" },
                font: { color: "#e0e0e0" },
                margin: { l: 0, r: 0, b: 0, t: 40 },
              }}
              style={{ width: "100%", height: "100%" }}
              useResizeHandler={true}
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
    // === ИЗМЕНЕНИЕ: Добавляем 'z' в PropTypes ===
    phrase_clusters: PropTypes.arrayOf(
      PropTypes.shape({
        x: PropTypes.number,
        y: PropTypes.number,
        z: PropTypes.number, // Z координата для 3D
        cluster: PropTypes.number,
        phrase: PropTypes.string,
      }),
    ),
  }).isRequired,
};
