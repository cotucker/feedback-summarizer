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
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { BarChart } from "@mui/x-charts/BarChart";
import { PieChart } from "@mui/x-charts/PieChart";
import { DataGrid } from "@mui/x-data-grid";

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

export const Visualization = ({ results }) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedTopicData, setSelectedTopicData] = useState(null);

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

  return (
    <Box sx={{ mt: 4 }}>
      {/* Весь остальной JSX остается без изменений */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h5">Overall Summary</Typography>
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
  }).isRequired,
};
