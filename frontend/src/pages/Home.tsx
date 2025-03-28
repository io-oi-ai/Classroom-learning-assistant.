import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import { uploadFile, sendMessage } from '../services/api';

const Home: React.FC = () => {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setLoading(true);
    setError('');

    try {
      let endpoint = '';
      if (file.type === 'application/pdf') {
        endpoint = '/api/upload/pdf';
      } else if (file.type.startsWith('audio/')) {
        endpoint = '/api/upload/audio';
      } else if (file.type.startsWith('video/')) {
        endpoint = '/api/upload/video';
      } else {
        throw new Error('不支持的文件类型');
      }

      const result = await uploadFile(file, endpoint);
      setResponse(result.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败');
    } finally {
      setLoading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'audio/*': ['.wav', '.mp3', '.m4a'],
      'video/*': ['.mp4', '.avi', '.mov'],
    },
    multiple: false,
  });

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    setLoading(true);
    setError('');

    try {
      const result = await sendMessage(message);
      setResponse(result.response);
    } catch (err) {
      setError(err instanceof Error ? err.message : '发送失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          AI智能助手
        </Typography>

        <Box sx={{ mb: 4 }}>
          <Paper
            {...getRootProps()}
            sx={{
              p: 3,
              textAlign: 'center',
              backgroundColor: isDragActive ? '#f0f0f0' : 'white',
              cursor: 'pointer',
              border: '2px dashed #ccc',
            }}
          >
            <input {...getInputProps()} />
            <Typography>
              {isDragActive
                ? '将文件拖放到此处'
                : '点击或拖放文件到此处上传（支持PDF、音频、视频）'}
            </Typography>
          </Paper>
        </Box>

        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            placeholder="输入您的问题..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Button
            variant="contained"
            onClick={handleSendMessage}
            disabled={loading || !message.trim()}
            fullWidth
          >
            {loading ? <CircularProgress size={24} /> : '发送'}
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {response && (
          <Paper sx={{ p: 2, backgroundColor: '#f8f9fa' }}>
            <Typography variant="body1">{response}</Typography>
          </Paper>
        )}
      </Paper>
    </Container>
  );
};

export default Home; 