import React, { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  PlayArrow as PlayIcon,
  Info as InfoIcon,
  Search as SearchIcon,
  VideoFile as VideoIcon,
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  Close as CloseIcon,
} from "@mui/icons-material";
import axios from "axios";
import { ModuleInfoPopup } from "./ModuleInfoPopup";

interface Module {
  name: string;
  env: string;
  version: string;
  description: string;
  tags: string[];
  isDeployed: boolean;
  visibility: string;
  created_at?: string;
  owner_id?: number;
  owner_name?: string;
  deployment_mismatch?: boolean;
}

interface ExecutionResult {
  result: any;
  exit_code: number;
  stderr: string;
  stdout: string;
  duration: number;
}

interface OutputFile {
  file_id: string;
  download_url: string;
  original_filename: string;
  file_size: number;
  expires_at: string;
}

interface MediaExecutionResult {
  result: any;
  exit_code: number;
  stderr: string;
  stdout: string;
  duration: number;
  output_files: OutputFile[];
}

const ExecutableModuleList: React.FC = () => {
  const [modules, setModules] = useState<Module[]>([]);
  const [filteredModules, setFilteredModules] = useState<Module[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 필터 상태
  const [searchTerm, setSearchTerm] = useState("");
  const [envFilter, setEnvFilter] = useState<string>("");
  const [visibilityFilter, setVisibilityFilter] = useState<string>("");

  // 실행 관련 상태
  const [infoModule, setInfoModule] = useState<Module | null>(null);
  const [executeModule, setExecuteModule] = useState<Module | null>(null);
  const [executionDialogOpen, setExecutionDialogOpen] = useState(false);
  const [executionInput, setExecutionInput] = useState("");
  const [executionResult, setExecutionResult] =
    useState<ExecutionResult | null>(null);
  const [executing, setExecuting] = useState(false);
  const [executionError, setExecutionError] = useState<string | null>(null);
  
  // 멀티미디어 실행 상태
  const [mediaExecutionResult, setMediaExecutionResult] = useState<MediaExecutionResult | null>(null);
  const [executionMode, setExecutionMode] = useState<'json' | 'media'>('json');
  const [uploadFiles, setUploadFiles] = useState<FileList | null>(null);

  // 모듈 목록 로드
  useEffect(() => {
    loadModules();
  }, []);

  // 필터링 적용
  useEffect(() => {
    let filtered = modules;

    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (module) =>
          module.name.toLowerCase().includes(searchLower) ||
          module.description.toLowerCase().includes(searchLower) ||
          module.tags.some((tag) => tag.toLowerCase().includes(searchLower))
      );
    }

    if (envFilter) {
      filtered = filtered.filter((module) => module.env === envFilter);
    }

    if (visibilityFilter) {
      filtered = filtered.filter(
        (module) => module.visibility === visibilityFilter
      );
    }

    setFilteredModules(filtered);
  }, [modules, searchTerm, envFilter, visibilityFilter]);

  const loadModules = async () => {
    try {
      setLoading(true);
      const response = await axios.get("/api/modules/executable");
      setModules(response.data);
      setError(null);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "모듈 목록을 불러오는데 실패했습니다."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!executeModule) return;

    try {
      setExecuting(true);
      setExecutionError(null);
      setExecutionResult(null);

      // 입력 데이터가 없으면 빈 객체로 처리
      let inputData = {};
      if (executionInput.trim()) {
        try {
          inputData = JSON.parse(executionInput);
        } catch (err) {
          setExecutionError("입력 데이터가 올바른 JSON 형식이 아닙니다.");
          return;
        }
      }

      const response = await axios.post(`/api/run/${executeModule.name}`, {
        input: inputData,
      });

      setExecutionResult(response.data);
    } catch (err: any) {
      setExecutionError(
        err.response?.data?.detail || "모듈 실행에 실패했습니다."
      );
    } finally {
      setExecuting(false);
    }
  };

  const handleOpenExecutionDialog = (module: Module) => {
    setExecuteModule(module);
    setExecutionInput("");
    setExecutionResult(null);
    setMediaExecutionResult(null);
    setExecutionError(null);
    setExecutionMode('json');
    setUploadFiles(null);
    
    // 파일 입력 초기화
    setTimeout(() => {
      const fileInput = document.getElementById('file-upload-execution') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }
    }, 0);
    
    setExecutionDialogOpen(true);
  };

  const handleCloseExecutionDialog = () => {
    setExecutionDialogOpen(false);
    setExecuteModule(null);
    setExecutionInput("");
    setExecutionResult(null);
    setMediaExecutionResult(null);
    setExecutionError(null);
    setExecutionMode('json');
    setUploadFiles(null);
    
    // 파일 입력 초기화
    const fileInput = document.getElementById('file-upload-execution') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
  };

  const getEnvironmentLabel = (env: string) => {
    const labels: { [key: string]: string } = {
      inline: "인라인",
      venv: "가상환경",
      conda: "Conda",
      uv: "UV",
      docker: "Docker",
    };
    return labels[env] || env;
  };

  const getVisibilityLabel = (visibility: string) => {
    const labels: { [key: string]: string } = {
      public: "공개",
      private: "비공개",
      organization: "조직",
    };
    return labels[visibility] || visibility;
  };
  
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setUploadFiles(event.target.files);
    setExecutionError(null);
  };
  
  const removeFile = (indexToRemove: number) => {
    if (!uploadFiles) return;
    
    const dt = new DataTransfer();
    const files = Array.from(uploadFiles);
    
    files.forEach((file, index) => {
      if (index !== indexToRemove) {
        dt.items.add(file);
      }
    });
    
    setUploadFiles(dt.files.length > 0 ? dt.files : null);
    
    // HTML input도 업데이트
    const fileInput = document.getElementById('file-upload-execution') as HTMLInputElement;
    if (fileInput) {
      fileInput.files = dt.files;
    }
  };
  
  const clearAllFiles = () => {
    setUploadFiles(null);
    const fileInput = document.getElementById('file-upload-execution') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
  };
  
  const downloadFile = async (outputFile: OutputFile) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(outputFile.download_url, {
        headers: { 'Authorization': `Bearer ${token}` },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', outputFile.original_filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
    } catch (err: any) {
      setExecutionError(`다운로드 실패: ${err.response?.data?.detail || err.message}`);
    }
  };
  
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* 검색 및 필터 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="모듈 검색"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="이름, 설명, 태그로 검색..."
                InputProps={{
                  startAdornment: (
                    <SearchIcon sx={{ mr: 1, color: "text.secondary" }} />
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>환경</InputLabel>
                <Select
                  value={envFilter}
                  label="환경"
                  onChange={(e) => setEnvFilter(e.target.value)}
                >
                  <MenuItem value="">전체</MenuItem>
                  <MenuItem value="inline">인라인</MenuItem>
                  <MenuItem value="venv">가상환경</MenuItem>
                  <MenuItem value="conda">Conda</MenuItem>
                  <MenuItem value="uv">UV</MenuItem>
                  <MenuItem value="docker">Docker</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>가시성</InputLabel>
                <Select
                  value={visibilityFilter}
                  label="가시성"
                  onChange={(e) => setVisibilityFilter(e.target.value)}
                >
                  <MenuItem value="">전체</MenuItem>
                  <MenuItem value="public">공개</MenuItem>
                  <MenuItem value="private">비공개</MenuItem>
                  <MenuItem value="organization">조직</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Typography variant="body2" color="text.secondary">
                총 {filteredModules.length}개 모듈
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 모듈 목록 */}
      <Grid container spacing={2}>
        {filteredModules.map((module) => (
          <Grid item xs={12} md={6} lg={4} key={module.name}>
            <Card>
              <CardContent>
                <Box
                  display="flex"
                  justifyContent="space-between"
                  alignItems="flex-start"
                  mb={1}
                >
                  <Typography variant="h6" component="h3" noWrap>
                    {module.name}
                  </Typography>
                  <Box display="flex" gap={1}>
                    <Tooltip title="모듈 정보">
                      <IconButton
                        size="small"
                        onClick={() => setInfoModule(module)}
                      >
                        <InfoIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="실행 테스트">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleOpenExecutionDialog(module)}
                        disabled={!module.isDeployed}
                      >
                        <PlayIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2 }}
                >
                  {module.description || "설명 없음"}
                </Typography>

                {/* 소유자 정보 */}
                <Typography
                  variant="caption"
                  color="textSecondary"
                  sx={{ mb: 1, display: "block" }}
                >
                  소유자: {module.owner_name || "Unknown"}
                </Typography>

                <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                  <Chip
                    label={getEnvironmentLabel(module.env)}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={getVisibilityLabel(module.visibility)}
                    size="small"
                    variant="outlined"
                    color={
                      module.visibility === "public" ? "success" : "default"
                    }
                  />
                  <Chip
                    label={`v${module.version}`}
                    size="small"
                    variant="outlined"
                  />
                </Box>

                {module.tags.length > 0 && (
                  <Box display="flex" gap={0.5} flexWrap="wrap">
                    {module.tags.map((tag, index) => (
                      <Chip
                        key={index}
                        label={tag}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {filteredModules.length === 0 && !loading && (
        <Box textAlign="center" py={4}>
          <Typography variant="h6" color="text.secondary">
            실행 가능한 모듈이 없습니다.
          </Typography>
        </Box>
      )}

      {/* 실행 테스트 다이얼로그 */}
      <Dialog
        open={executionDialogOpen}
        onClose={handleCloseExecutionDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>모듈 실행 테스트: {executeModule?.name}</DialogTitle>
        <DialogContent>
          {/* 실행 모드 선택 */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              실행 모드:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant={executionMode === 'json' ? 'contained' : 'outlined'}
                onClick={() => setExecutionMode('json')}
                size="small"
              >
                JSON 입력
              </Button>
              <Button
                variant={executionMode === 'media' ? 'contained' : 'outlined'}
                onClick={() => setExecutionMode('media')}
                size="small"
                startIcon={<VideoIcon />}
              >
                멀티미디어 파일
              </Button>
            </Box>
          </Box>
          
          {/* 파일 업로드 (media 모드일 때만) */}
          {executionMode === 'media' && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                파일 업로드 (동영상/이미지):
              </Typography>
              <input
                type="file"
                multiple
                accept="video/*,image/*"
                onChange={handleFileChange}
                style={{ display: 'none' }}
                id="file-upload-execution"
              />
              <label htmlFor="file-upload-execution">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<UploadIcon />}
                  sx={{ mb: 1 }}
                >
                  파일 선택
                </Button>
              </label>
              
              {uploadFiles && uploadFiles.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      선택된 파일 {uploadFiles.length}개:
                    </Typography>
                    <Button
                      size="small"
                      onClick={clearAllFiles}
                      sx={{ minWidth: 'auto', px: 1 }}
                    >
                      전체 삭제
                    </Button>
                  </Box>
                  {Array.from(uploadFiles).map((file, index) => (
                    <Chip
                      key={index}
                      label={`${file.name} (${formatFileSize(file.size)})`}
                      variant="outlined"
                      onDelete={() => removeFile(index)}
                      deleteIcon={<CloseIcon />}
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                </Box>
              )}
            </Box>
          )}
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              입력 데이터 (JSON 형식, 선택사항):
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              value={executionInput}
              onChange={(e) => setExecutionInput(e.target.value)}
              placeholder='{"key": "value"} (빈 값으로도 실행 가능)'
              variant="outlined"
            />
          </Box>

          {executionError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {executionError}
            </Alert>
          )}

          {executionResult && (
            <Box>
              <Typography variant="h6" gutterBottom>
                실행 결과
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  종료 코드: {executionResult.exit_code}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  실행 시간: {executionResult.duration.toFixed(2)}초
                </Typography>
              </Box>

              {executionResult.stdout && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    표준 출력:
                  </Typography>
                  <Box
                    component="pre"
                    sx={{
                      backgroundColor: "grey.100",
                      p: 1,
                      borderRadius: 1,
                      fontSize: "0.875rem",
                      overflow: "auto",
                    }}
                  >
                    {executionResult.stdout}
                  </Box>
                </Box>
              )}

              {executionResult.stderr && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    표준 에러:
                  </Typography>
                  <Box
                    component="pre"
                    sx={{
                      backgroundColor: "error.light",
                      color: "error.contrastText",
                      p: 1,
                      borderRadius: 1,
                      fontSize: "0.875rem",
                      overflow: "auto",
                    }}
                  >
                    {executionResult.stderr}
                  </Box>
                </Box>
              )}

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  결과:
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    backgroundColor: "success.light",
                    color: "success.contrastText",
                    p: 1,
                    borderRadius: 1,
                    fontSize: "0.875rem",
                    overflow: "auto",
                  }}
                >
                  {JSON.stringify(executionResult.result, null, 2)}
                </Box>
              </Box>
            </Box>
          )}
          
          {/* 멀티미디어 실행 결과 */}
          {mediaExecutionResult && (
            <Box>
              <Typography variant="h6" gutterBottom>
                실행 결과 (멀티미디어)
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  종료 코드: {mediaExecutionResult.exit_code}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  실행 시간: {mediaExecutionResult.duration.toFixed(2)}초
                </Typography>
              </Box>

              {mediaExecutionResult.stdout && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    표준 출력:
                  </Typography>
                  <Box
                    component="pre"
                    sx={{
                      backgroundColor: "grey.100",
                      p: 1,
                      borderRadius: 1,
                      fontSize: "0.875rem",
                      overflow: "auto",
                    }}
                  >
                    {mediaExecutionResult.stdout}
                  </Box>
                </Box>
              )}

              {mediaExecutionResult.stderr && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    표준 에러:
                  </Typography>
                  <Box
                    component="pre"
                    sx={{
                      backgroundColor: "error.light",
                      color: "error.contrastText",
                      p: 1,
                      borderRadius: 1,
                      fontSize: "0.875rem",
                      overflow: "auto",
                    }}
                  >
                    {mediaExecutionResult.stderr}
                  </Box>
                </Box>
              )}
              
              {/* 결과 데이터 */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  결과 데이터:
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    backgroundColor: "success.light",
                    color: "success.contrastText",
                    p: 1,
                    borderRadius: 1,
                    fontSize: "0.875rem",
                    overflow: "auto",
                    maxHeight: "200px"
                  }}
                >
                  {JSON.stringify(mediaExecutionResult.result, null, 2)}
                </Box>
              </Box>
              
              {/* 출력 파일들 */}
              {mediaExecutionResult.output_files && mediaExecutionResult.output_files.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    결과 파일들 ({mediaExecutionResult.output_files.length}개):
                  </Typography>
                  {mediaExecutionResult.output_files.map((file, index) => (
                    <Card key={index} variant="outlined" sx={{ mb: 1 }}>
                      <CardContent sx={{ p: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Box>
                            <Typography variant="body2">
                              {file.original_filename}
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
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseExecutionDialog}>닫기</Button>
          <Button
            onClick={handleExecute}
            variant="contained"
            disabled={executing}
            startIcon={
              executing ? <CircularProgress size={16} /> : <PlayIcon />
            }
          >
            {executing ? "실행 중..." : "실행"}
          </Button>
        </DialogActions>
      </Dialog>

      {infoModule && (
        <ModuleInfoPopup
          module={infoModule}
          onClose={() => setInfoModule(null)}
        />
      )}
    </Box>
  );
};

export default ExecutableModuleList;
