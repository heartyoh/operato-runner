import React, { useState } from "react";
import { createModule } from "../api";
import axios from "axios";
import {
  Box,
  Button,
  TextField,
  Typography,
  MenuItem,
  Paper,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
} from "@mui/material";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import VersionSelectInput from "./VersionSelectInput";
import { useNavigate } from "react-router-dom";

interface Props {
  onUploadSuccess?: () => void;
}

const ModuleUpload: React.FC<Props> = ({ onUploadSuccess }) => {
  const [tab, setTab] = useState(0); // 0: 파일 업로드, 1: 인라인 등록
  // 파일 업로드 상태
  const [name, setName] = useState("");
  const [env, setEnv] = useState("venv");
  const [version, setVersion] = useState("0.1.0");
  const [file, setFile] = useState<File | null>(null);
  const [artifactUri, setArtifactUri] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isPublic, setIsPublic] = useState(false);
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);
  // 인라인 등록 상태
  const [inlineName, setInlineName] = useState("");
  const [inlineVersion, setInlineVersion] = useState("0.1.0");
  const [inlineCode, setInlineCode] = useState("");
  const [inlineDesc, setInlineDesc] = useState("");
  const [inlineLoading, setInlineLoading] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [inlineSuccess, setInlineSuccess] = useState(false);
  const [inlineInput, setInlineInput] = useState<string>(`{
  "x": 1,
  "y": 2
}`);
  const [artifactType, setArtifactType] = useState<string>("zip");
  const [inlineIsPublic, setInlineIsPublic] = useState(false);
  const [dockerImage, setDockerImage] = useState("");
  const navigate = useNavigate();

  // 폼 초기화 함수
  const resetForm = () => {
    setName("");
    setEnv("venv");
    setVersion("0.1.0");
    setFile(null);
    setArtifactUri("");
    setDockerImage("");
    setArtifactType("zip");
    setInlineCode("");
    setInlineInput(`{\n  \"x\": 1,\n  \"y\": 2\n}`);
  };

  // artifact_type별 허용 env 목록 정의
  const allowedEnvs: Record<string, string[]> = {
    zip: ["venv", "conda", "uv"],
    git: ["venv", "conda", "uv"],
    docker: ["docker"],
    inline: ["inline"],
  };

  // 논리적 조합 체크 함수
  const isArtifactTypeAllowed = (type: string, env: string) => {
    if (env === "inline") return type === "inline";
    if (env === "docker") return type === "docker";
    return ["zip", "git"].includes(type);
  };

  // 탭 변경 핸들러
  const handleArtifactTabChange = (_: any, newValue: string) => {
    setArtifactType(newValue);
    setFile(null);
    setArtifactUri("");
    setDockerImage("");
    setInlineName("");
    setInlineCode("");
    setInlineDesc("");
    setInlineInput(`{\n  \"x\": 1,\n  \"y\": 2\n}`);
  };

  // artifactType 변경 시 env 자동 보정
  React.useEffect(() => {
    if (!allowedEnvs[artifactType].includes(env)) {
      setEnv(allowedEnvs[artifactType][0]);
    }
  }, [artifactType]);

  // artifactType이 'inline'이거나 env가 'inline'이면 인라인 입력란 항상 활성화
  const showInlineFields = artifactType === "inline" || env === "inline";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    if (!name) {
      setError("모듈 이름을 입력하세요.");
      return;
    }
    if (!isArtifactTypeAllowed(artifactType, env)) {
      setError("선택한 환경과 아티팩트 타입 조합이 맞지 않습니다.");
      return;
    }
    if (artifactType === "zip" && !file) {
      setError("zip 파일을 첨부하세요.");
      return;
    }
    if (artifactType === "git" && !artifactUri) {
      setError("Git 저장소 링크를 입력하세요.");
      return;
    }
    if (artifactType === "docker" && !dockerImage) {
      setError("Docker 이미지 주소를 입력하세요.");
      return;
    }
    if (artifactType === "inline" && !inlineCode) {
      setError("인라인 코드를 입력하세요.");
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("env", env);
      formData.append("version", version);
      formData.append("is_public", String(isPublic));
      formData.append("description", description);
      formData.append("tags", tags);
      formData.append("artifact_type", artifactType);
      if (artifactType === "zip") {
        formData.append("file", file!);
      } else if (artifactType === "git") {
        formData.append("artifact_uri", artifactUri);
      } else if (artifactType === "docker") {
        formData.append("artifact_uri", dockerImage);
      } else if (artifactType === "inline") {
        formData.append("code", inlineCode);
        formData.append("input", inlineInput);
      }
      const response = await axios.post("/api/modules", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // 신규 모듈 생성의 경우 이전 버전이 없으므로 항상 성공
      setSuccess(true);
      resetForm();
      navigate(`/admin/modules/${encodeURIComponent(name)}`);
      if (onUploadSuccess) onUploadSuccess();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      let errorMessage = err.message;
      if (typeof detail === "string") {
        errorMessage = detail;
      } else if (detail && typeof detail === "object") {
        try {
          errorMessage = JSON.stringify(detail);
        } catch {
          errorMessage = "서버에서 오류 응답을 받았습니다.";
        }
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 템플릿 다운로드 핸들러
  const handleDownloadTemplate = async () => {
    try {
      const res = await axios.get("/api/templates/module", {
        responseType: "blob",
        // 인증이 필요한 경우 아래 주석 해제 후 토큰 변수 사용
        // headers: { Authorization: `Bearer ${token}` }
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "module_template.zip");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert("다운로드 실패: " + (err?.message || "알 수 없는 오류"));
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h4" gutterBottom>
        신규 모듈 업로드
      </Typography>
      <Typography variant="body1" color="textSecondary" gutterBottom>
        새로운 모듈을 업로드하고 버전을 관리하세요.
      </Typography>
      <Box
        display="flex"
        alignItems="center"
        justifyContent="space-between"
        mb={2}
      >
        <Typography variant="h6" gutterBottom></Typography>
        <Button
          variant="outlined"
          startIcon={<FileDownloadIcon />}
          onClick={handleDownloadTemplate}
        >
          템플릿 다운로드
        </Button>
      </Box>
      <Tabs
        value={artifactType}
        onChange={handleArtifactTabChange}
        sx={{ mb: 2 }}
        variant="scrollable"
        scrollButtons="auto"
      >
        <Tab label="ZIP 파일" value="zip" />
        <Tab label="Git 저장소" value="git" />
        <Tab label="Docker 이미지" value="docker" />
        <Tab label="인라인 코드" value="inline" />
      </Tabs>
      <form onSubmit={handleSubmit}>
        <Box display="flex" gap={2} flexWrap="wrap" alignItems="center">
          <FormControlLabel
            control={
              <Switch
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                color="primary"
              />
            }
            label={isPublic ? "공개 모듈" : "비공개 모듈"}
            sx={{ mr: 2 }}
          />
          <TextField
            label="이름"
            value={name}
            onChange={(e) => {
              const v = e.target.value;
              // 슬래시, 역슬래시, .., 특수문자 금지
              if (/[\/\\]|\.\./.test(v) || !/^[a-zA-Z0-9_\-]*$/.test(v)) {
                setNameError("모듈명에 /, \\, .., 특수문자 사용 불가");
              } else {
                setNameError(null);
              }
              setName(v);
            }}
            required
            size="small"
            error={!!nameError}
            helperText={nameError || ""}
          />
          <TextField
            label="환경"
            select
            value={env}
            onChange={(e) => setEnv(e.target.value)}
            size="small"
          >
            {(["venv", "conda", "uv", "docker", "inline"] as const).map(
              (opt) => (
                <MenuItem
                  key={opt}
                  value={opt}
                  disabled={!allowedEnvs[artifactType].includes(opt)}
                >
                  {opt}
                </MenuItem>
              )
            )}
          </TextField>
          <TextField
            label="버전"
            value={version}
            onChange={(e) => setVersion(e.target.value)}
            required
            size="small"
            sx={{ width: 120 }}
          />
          <TextField
            label="설명"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            size="small"
            sx={{ minWidth: 200 }}
          />
          <TextField
            label="태그"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            size="small"
            sx={{ minWidth: 160 }}
            placeholder="쉼표로 구분"
          />
          {/* 각 탭별 입력란 */}
          {artifactType === "zip" && isArtifactTypeAllowed("zip", env) && (
            <Button
              variant="contained"
              component="label"
              disabled={!!artifactUri || !!dockerImage}
            >
              파일 선택
              <input
                type="file"
                accept=".zip"
                hidden
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null);
                  if (e.target.files?.[0]) {
                    setArtifactUri("");
                    setDockerImage("");
                  }
                }}
              />
            </Button>
          )}
          {file && artifactType === "zip" && (
            <Typography>{file.name}</Typography>
          )}
          {artifactType === "git" && isArtifactTypeAllowed("git", env) && (
            <TextField
              label="Git 저장소 링크"
              value={artifactUri}
              onChange={(e) => {
                setArtifactUri(e.target.value);
                if (e.target.value) {
                  setFile(null);
                  setDockerImage("");
                }
              }}
              size="small"
              sx={{ minWidth: 260 }}
              placeholder="https://github.com/username/repo.git"
            />
          )}
          {artifactType === "docker" && (
            <TextField
              label="도커 이미지 주소"
              value={dockerImage}
              onChange={(e) => {
                setDockerImage(e.target.value);
                if (e.target.value) {
                  setFile(null);
                  setArtifactUri("");
                }
              }}
              size="small"
              sx={{ minWidth: 260 }}
              placeholder="ghcr.io/yourorg/yourimage:tag"
              required
            />
          )}
          {artifactType === "inline" && (
            <>
              <TextField
                label="input 예시 (JSON)"
                value={inlineInput}
                onChange={(e) => setInlineInput(e.target.value)}
                fullWidth
                margin="normal"
                multiline
                minRows={3}
                placeholder={`{\n  \"x\": 1,\n  \"y\": 2\n}`}
                helperText="실행 시 input 파라미터로 전달됩니다. 코드에서 input['x'] 등으로 바로 사용하세요."
              />
              <TextField
                label="코드"
                value={inlineCode}
                onChange={(e) => setInlineCode(e.target.value)}
                fullWidth
                margin="normal"
                multiline
                minRows={8}
                placeholder="여기에 파이썬 코드를 입력하세요"
                required
              />
            </>
          )}
          {/* 논리적으로 맞지 않는 조합 안내 제거 */}
          {/* 업로드 버튼 항상 활성화, 필수 입력값만 체크 */}
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={
              loading ||
              !name ||
              !!nameError ||
              (artifactType === "inline" && !inlineCode) ||
              (artifactType === "zip" && !file) ||
              (artifactType === "git" && !artifactUri) ||
              (artifactType === "docker" && !dockerImage)
            }
          >
            {artifactType === "inline" ? "등록" : "업로드"}
          </Button>
        </Box>
      </form>
      {loading && <CircularProgress sx={{ mt: 2 }} />}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          업로드 성공!
        </Alert>
      )}
    </Paper>
  );
};

export default ModuleUpload;
