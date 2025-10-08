import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Chip,
  LinearProgress
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  VideoFile as VideoIcon,
  Image as ImageIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import axios from 'axios';

interface MediaUploadFormProps {
  moduleName: string;
  onExecutionComplete?: (result: any) => void;
}

interface OutputFile {
  file_id: string;
  download_url: string;
  original_filename: string;
  file_size: number;
  expires_at: string;
}

interface ExecutionResult {
  result: any;
  exit_code: number;
  stderr: string;
  stdout: string;
  duration: number;
  output_files: OutputFile[];
}

const MediaUploadForm: React.FC<MediaUploadFormProps> = ({ 
  moduleName, 
  onExecutionComplete 
}) => {
  const [files, setFiles] = useState<FileList | null>(null);
  const [parameters, setParameters] = useState<string>('{}');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(event.target.files);
    setError(null);
  };

  const validateFiles = (files: FileList): string | null => {
    const maxSize = 100 * 1024 * 1024; // 100MB

    // 파일 타입 제한 제거 - 모든 파일 허용
    // 백엔드와 모듈에서 필요한 파일 타입을 검증하도록 위임

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      if (file.size > maxSize) {
        return `파일 "${file.name}"이 100MB 제한을 초과합니다.`;
      }
    }

    return null;
  };

  const executeWithMedia = async () => {
    if (!files || files.length === 0) {
      setError('파일을 선택해주세요.');
      return;
    }

    const validationError = validateFiles(files);
    if (validationError) {
      setError(validationError);
      return;
    }

    let parsedParams;
    try {
      parsedParams = JSON.parse(parameters);
    } catch (e) {
      setError('잘못된 JSON 형식입니다.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      
      // 파일들 추가
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      
      // JSON 파라미터 추가
      formData.append('input_data', JSON.stringify(parsedParams));

      const token = localStorage.getItem('access_token');
      const response = await axios.post<ExecutionResult>(
        `/api/modules/execute-media/${moduleName}`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const progress = (progressEvent.loaded / progressEvent.total) * 100;
              setUploadProgress(progress);
            }
          }
        }
      );

      setResult(response.data);
      onExecutionComplete?.(response.data);
      
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || '실행 실패';
      setError(errorMsg);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const downloadFile = async (outputFile: OutputFile) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(outputFile.download_url, {
        headers: { 'Authorization': `Bearer ${token}` },
        responseType: 'blob'
      });

      // 파일 다운로드
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', outputFile.original_filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
    } catch (err: any) {
      setError(`다운로드 실패: ${err.response?.data?.detail || err.message}`);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.toLowerCase().split('.').pop();
    const videoExts = ['mp4', 'avi', 'mov', 'mkv'];
    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
    
    if (videoExts.includes(ext || '')) return <VideoIcon />;
    if (imageExts.includes(ext || '')) return <ImageIcon />;
    return <UploadIcon />;
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 2 }}>
      <Typography variant="h6" gutterBottom>
        파일과 함께 실행
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            파일 업로드
          </Typography>
          
          <input
            type="file"
            multiple
            onChange={handleFileChange}
            style={{ display: 'none' }}
            id="file-upload"
          />

          <label htmlFor="file-upload">
            <Button
              variant="outlined"
              component="span"
              startIcon={<UploadIcon />}
              sx={{ mb: 2 }}
            >
              파일 선택
            </Button>
          </label>

          {files && files.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                선택된 파일들:
              </Typography>
              {Array.from(files).map((file, index) => (
                <Chip
                  key={index}
                  icon={getFileIcon(file.name)}
                  label={`${file.name} (${formatFileSize(file.size)})`}
                  variant="outlined"
                  sx={{ m: 0.5 }}
                />
              ))}
            </Box>
          )}

          <TextField
            label="실행 파라미터 (JSON)"
            multiline
            rows={4}
            fullWidth
            value={parameters}
            onChange={(e) => setParameters(e.target.value)}
            placeholder='{"param1": "value1", "param2": "value2"}'
            sx={{ mt: 2 }}
          />

          {uploadProgress > 0 && loading && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2">업로드 진행률: {uploadProgress.toFixed(1)}%</Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
          )}

          <Button
            variant="contained"
            onClick={executeWithMedia}
            disabled={loading || !files || files.length === 0}
            sx={{ mt: 2 }}
            startIcon={loading ? <CircularProgress size={20} /> : <UploadIcon />}
          >
            {loading ? '실행 중...' : '실행'}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              실행 결과
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">
                  실행 시간: {result.duration.toFixed(2)}초
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">
                  종료 코드: {result.exit_code}
                </Typography>
              </Grid>
            </Grid>

            {result.result && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2">결과 데이터:</Typography>
                <pre style={{ 
                  backgroundColor: '#f5f5f5', 
                  padding: '8px', 
                  borderRadius: '4px',
                  fontSize: '12px',
                  overflow: 'auto',
                  maxHeight: '200px'
                }}>
                  {JSON.stringify(result.result, null, 2)}
                </pre>
              </Box>
            )}

            {result.output_files && result.output_files.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  결과 파일들:
                </Typography>
                {result.output_files.map((file, index) => (
                  <Card key={index} variant="outlined" sx={{ mb: 1 }}>
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="body2">
                            {getFileIcon(file.original_filename)} {file.original_filename}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            크기: {formatFileSize(file.file_size)} | 
                            만료: {new Date(file.expires_at).toLocaleString()}
                          </Typography>
                        </Box>
                        <Button
                          size="small"
                          startIcon={<DownloadIcon />}
                          onClick={() => downloadFile(file)}
                        >
                          다운로드
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}

            {result.stdout && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2">Standard Output:</Typography>
                <pre style={{ 
                  backgroundColor: '#f0f0f0', 
                  padding: '8px', 
                  borderRadius: '4px',
                  fontSize: '12px',
                  maxHeight: '150px',
                  overflow: 'auto'
                }}>
                  {result.stdout}
                </pre>
              </Box>
            )}

            {result.stderr && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" color="error">Standard Error:</Typography>
                <pre style={{ 
                  backgroundColor: '#ffebee', 
                  padding: '8px', 
                  borderRadius: '4px',
                  fontSize: '12px',
                  maxHeight: '150px',
                  overflow: 'auto',
                  color: '#c62828'
                }}>
                  {result.stderr}
                </pre>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default MediaUploadForm;