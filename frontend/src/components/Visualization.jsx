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
import Plot from "react-plotly.js";
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
    minWidth: 770,
    renderCell: renderCellWithTooltip,
  },
  { field: "topic", headerName: "Topic", width: 270 },
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

const allFeedbacksColumns = [
  {
    field: "feedback",
    headerName: "Original Feedback",
    flex: 1,
    minWidth: 770,
    renderCell: renderCellWithTooltip,
  },
  { field: "topics", headerName: "Topics", width: 270 },
  { field: "rating", headerName: "Rating", width: 120 },
];

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
];

const calculateConvexHull = (points) => {
  if (points.length < 3) return points;

  const crossProduct = (o, a, b) => {
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  };

  points.sort((a, b) => (a.x !== b.x ? a.x - b.x : a.y - b.y));

  const hull = [];
  for (let i = 0; i < points.length; ++i) {
    while (
      hull.length >= 2 &&
      crossProduct(hull[hull.length - 2], hull[hull.length - 1], points[i]) <= 0
    ) {
      hull.pop();
    }
    hull.push(points[i]);
  }

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

  hull.pop();
  return hull;
};

export const Visualization = ({ results, analyzedFilename }) => {
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

  const allFeedbacksRows = results.all_feedbacks.map((row, index) => ({
    ...row,
    id: index,
  }));

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

  const preparePlotlyData = () => {
    const plotlyTraces = [];

    Object.keys(clusters).forEach((clusterKey, index) => {
      const points = clusters[clusterKey];
      const color = CLUSTER_COLORS[index % CLUSTER_COLORS.length];

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

      if (points.length >= 3) {
        const hull = calculateConvexHull([...points]);
        const hullX = [...hull.map((p) => p.x), hull[0].x];
        const hullY = [...hull.map((p) => p.y), hull[0].y];

        plotlyTraces.push({
          x: hullX,
          y: hullY,
          mode: "lines",
          type: "scatter",
          fill: "toself",
          fillcolor: color + "20",
          line: { color: color, width: 2 },
          showlegend: false,
          hoverinfo: "skip",
        });
      } else if (points.length === 2) {
        plotlyTraces.push({
          x: points.map((p) => p.x),
          y: points.map((p) => p.y),
          mode: "lines",
          type: "scatter",
          line: { color: color, width: 2, dash: "dash" },
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

  const plotlyData = preparePlotlyData();

  let plotLayout = {};
  if (clusterData.length > 0) {
    const xValues = clusterData.map((p) => p.x);
    const yValues = clusterData.map((p) => p.y);
    const minX = Math.min(...xValues);
    const maxX = Math.max(...xValues);
    const minY = Math.min(...yValues);
    const maxY = Math.max(...yValues);
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
      dragmode: "pan",
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
              {analyzedFilename && (
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  sx={{ mt: 1, mb: 2, textAlign: "center" }}
                >
                  Analyzed file: {analyzedFilename}
                </Typography>
              )}
              <Divider sx={{ my: 2 }} />
              <Typography variant="body1">{results.summary}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2, height: "700px" }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
              Bar Chart of Topic Distribution
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              This chart illustrates the frequency of feedback across different
              topics, highlighting the most discussed areas to help prioritize
              business focus.
            </Typography>
            <BarChart
              margin={{ bottom: 80 }}
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

        <Grid item xs={12}>
          <Paper sx={{ p: 2, height: "500px", width: "1150px" }}>
            <Typography
              variant="h6"
              gutterBottom
              sx={{ mb: 2, position: "relative", zIndex: 1 }}
            >
              Horizontal Bar Chart of Overall Sentiment Distribution
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              This overview visualizes the aggregate customer sentiment,
              providing a quick gauge of overall satisfaction levels across all
              feedback.
            </Typography>
            <BarChart
              layout="horizontal"
              margin={{ left: 100, right: 50, top: 70, bottom: 80 }}
              yAxis={[
                {
                  scaleType: "band",
                  data: sentimentChartData.map((s) => s.label),
                  colorMap: {
                    type: "ordinal",
                    colors: sentimentChartData.map((s) => s.color),
                  },
                },
              ]}
              xAxis={[{ label: "Number of Feedbacks" }]}
              series={[
                {
                  data: sentimentChartData.map((s) => s.value),
                  type: "bar",
                },
              ]}
              tooltip={{ trigger: "item" }}
              legend={{ hidden: true }}
            />
          </Paper>
        </Grid>

        {Object.keys(clusters).length > 0 && (
          <Grid item xs={12}>
            <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
              <Button
                variant="outlined"
                onClick={() => setIsClusterDialogOpen(true)}
                sx={{ py: 1.5, minWidth: "300px" }} // Сделал кнопку пошире
              >
                Show Phrase Clusters with Boundaries
              </Button>
            </Box>
          </Grid>
        )}

        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mb: 2, mt: 2 }}>
            Topic Summaries
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Detailed AI-generated summaries for each identified topic, providing
            actionable insights into specific customer pain points and praises.
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

        {/* 6. Data Grid */}
        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
            Text Analytics Insights
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            This data grid presents a comprehensive view of individual feedback
            entries, categorized by topic and sentiment, enabling detailed
            review and analysis.
          </Typography>
          <Paper sx={{ height: 600, width: "100%" }}>
            <DataGrid
              rows={feedbackAnalysisRows}
              columns={feedbackAnalysisColumns}
              pageSizeOptions={[5, 10, 20]}
            />
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mb: 2, mt: 4 }}>
            All Original Feedbacks
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            This section provides a complete list of all original customer
            feedbacks, alongside their identified topics and assigned ratings.
          </Typography>
          <Paper sx={{ height: 600, width: "100%" }}>
            <DataGrid
              rows={allFeedbacksRows}
              columns={allFeedbacksColumns}
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
        <DialogTitle variant="h4">
          Scatter Plot: Phrase-Semantic Clusters with Boundaries
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            This scatter plot visualizes the semantic landscape of your customer
            feedback. In this mapping,{" "}
            <b>spatial proximity indicates thematic similarity</b>: feedback
            points located close to each other share the same meaning. The
            formation of distinct clusters validates the accuracy of our
            analysis, demonstrating that the model successfully differentiates
            between unique business topics.
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
    all_feedbacks: PropTypes.arrayOf(
      PropTypes.shape({
        feedback: PropTypes.string,
        topics: PropTypes.string,
        rating: PropTypes.number,
      }),
    ),
    phrase_clusters: PropTypes.arrayOf(
      PropTypes.shape({
        x: PropTypes.number,
        y: PropTypes.number,
        cluster: PropTypes.number,
        phrase: PropTypes.string,
      }),
    ),
  }).isRequired,
  analyzedFilename: PropTypes.string,
};
