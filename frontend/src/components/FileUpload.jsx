// src/components/FileUpload.jsx

import React from "react";
import PropTypes from "prop-types";
import {
  Box,
  Button,
  Typography,
  LinearProgress,
  Alert,
  TextField,
  Tooltip,
  IconButton,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

export const FileUpload = ({
  onFileUpload,
  isLoading,
  error,
  progress,
  topics,
  onTopicsChange,
  onCancel,
  columns,
  onColumnsChange,
}) => {
  const [selectedFile, setSelectedFile] = React.useState(null);

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleUploadClick = () => {
    if (selectedFile) {
      onFileUpload(selectedFile);
    }
  };

  return (
    <Box
      sx={{
        p: 3,
        border: "2px dashed grey",
        borderRadius: 2,
        textAlign: "center",
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Typography variant="h6">Control Panel</Typography>
        <Tooltip
          title={
            <Box sx={{ textAlign: "left" }}>
              <Typography variant="body2" paragraph>
                Upload a CSV file. You can specify columns (Text, Rating order)
                or, if left empty, the system will default to 'Text' and 'Rating'
                columns. Optionally filter by topics.
              </Typography>
              <Typography variant="body2">
                Warning: If column names are duplicated (e.g., 'Text, Text'), the
                first instance will keep its name, and subsequent duplicates will
                have an index appended (e.g., 'Text', 'Text.1') to ensure
                uniqueness.
              </Typography>
            </Box>
          }
          arrow
          placement="top"
        >
          <IconButton size="small" sx={{ ml: 1 }}>
            <InfoOutlinedIcon fontSize="medium" color="primary" />
          </IconButton>
        </Tooltip>
      </Box>

      <TextField
        label="Filter by Topics (comma-separated, e.g., Price, UI)"
        variant="outlined"
        fullWidth
        value={topics}
        onChange={(e) => onTopicsChange(e.target.value)}
        sx={{ mb: 2 }}
        disabled={isLoading}
      />

      <TextField
        label="Desired Columns (comma-separated, e.g., Text, Rating)"
        variant="outlined"
        fullWidth
        value={columns}
        onChange={(e) => onColumnsChange(e.target.value)}
        sx={{ mb: 2 }}
        disabled={isLoading}
      />

      <Button
        variant="outlined"
        component="label"
        startIcon={<UploadFileIcon />}
        disabled={isLoading}
      >
        Select CSV File
        <input type="file" accept=".csv" hidden onChange={handleFileChange} />
      </Button>

      {selectedFile && (
        <Typography variant="body1" sx={{ mt: 2, mb: 2 }}>
          Selected: {selectedFile.name}
        </Typography>
      )}

      <Box sx={{ mt: 2, display: "flex", justifyContent: "center", gap: 2 }}>
        <Button
          variant="contained"
          onClick={handleUploadClick}
          disabled={!selectedFile || isLoading}
          size="large"
        >
          {isLoading ? "Analyzing..." : "Analyze Feedback"}
        </Button>

        {isLoading && (
          <Button
            variant="outlined"
            color="error"
            onClick={onCancel}
            size="large"
          >
            Cancel
          </Button>
        )}
      </Box>

      {isLoading && (
        <Box sx={{ width: "100%", mt: 2 }}>
          <LinearProgress variant="indeterminate" value={progress} />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

FileUpload.propTypes = {
  onFileUpload: PropTypes.func.isRequired,
  isLoading: PropTypes.bool.isRequired,
  error: PropTypes.string,
  progress: PropTypes.number.isRequired,
  topics: PropTypes.string.isRequired,
  onTopicsChange: PropTypes.func.isRequired,
  onCancel: PropTypes.func, // Optional, but recommended
  columns: PropTypes.string.isRequired,
  onColumnsChange: PropTypes.func.isRequired,
};
