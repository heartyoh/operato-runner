import React, { useState } from "react";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";

interface ModuleInfoPopupProps {
  module: {
    name: string;
    description?: string;
    version: string;
    tags?: string[];
    visibility?: string;
  };
  onClose: () => void;
}

const codeTemplates = {
  node: (name: string) =>
    `const axios = require('axios');\nconst FormData = require('form-data');\nconst fs = require('fs');\n\n// JSON 입력만 있는 경우:\naxios.post('/api/run/${name}', { input: {} })\n  .then(res => {\n    console.log(res.data);\n    // output_files가 있으면 파일 다운로드 링크 출력\n    if (res.data.output_files && res.data.output_files.length > 0) {\n      res.data.output_files.forEach(file => {\n        console.log('Download:', file.download_url, 'Filename:', file.original_filename);\n      });\n    }\n  });\n\n// 파일과 함께 실행하는 경우:\nconst form = new FormData();\nform.append('input', JSON.stringify({"key": "value"}));\nform.append('files', fs.createReadStream('/path/to/file1.jpg'));\nform.append('files', fs.createReadStream('/path/to/file2.mp4'));\n\naxios.post('/api/run/${name}', form, {\n  headers: form.getHeaders()\n}).then(res => {\n  console.log(res.data);\n  if (res.data.output_files && res.data.output_files.length > 0) {\n    res.data.output_files.forEach(file => {\n      console.log('Download:', file.download_url, 'Filename:', file.original_filename);\n    });\n  }\n});`,
  python: (name: string) =>
    `import requests\n\n# JSON 입력만 있는 경우:\nresp = requests.post('/api/run/${name}', json={'input': {}})\nresult = resp.json()\nprint(result)\n\n# 파일과 함께 실행하는 경우:\nfiles = [\n    ('files', open('/path/to/file1.jpg', 'rb')),\n    ('files', open('/path/to/file2.mp4', 'rb'))\n]\ndata = {'input': '{"key": "value"}'}\nresp = requests.post(\n    '/api/run/${name}',\n    files=files,\n    data=data\n)\nresult = resp.json()\n\n# output_files가 있으면 파일 다운로드 링크 출력\nif 'output_files' in result and result['output_files']:\n    for file in result['output_files']:\n        print(f"Download: {file['download_url']}, Filename: {file['original_filename']}")`,
  curl: (name: string) =>
    `# JSON 입력만 있는 경우:\ncurl -X POST '/api/run/${name}' \\\n  -H 'Content-Type: application/json' \\\n  -d '{"input":{}}\n\n# 파일과 함께 실행하는 경우:\ncurl -X POST '/api/run/${name}' \\\n  -F 'input={"key": "value"}' \\\n  -F 'files=@/path/to/file1.jpg' \\\n  -F 'files=@/path/to/file2.mp4'`,
};

export const ModuleInfoPopup: React.FC<ModuleInfoPopupProps> = ({
  module,
  onClose,
}) => {
  const [tab, setTab] = useState<"node" | "python" | "curl">("node");
  const [copied, setCopied] = useState(false);
  const code = codeTemplates[tab](module.name);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch (e) {
      setCopied(false);
    }
  };

  return (
    <Dialog open={true} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{module.name}</DialogTitle>
      <DialogContent>
        <div>{module.description || "설명 없음"}</div>
        <div>버전: {module.version}</div>
        <div>태그: {module.tags?.join(", ")}</div>
        <div>공개여부: {module.visibility}</div>
        <hr />
        <div style={{ margin: "1rem 0" }}>
          <Button
            onClick={() => setTab("node")}
            variant={tab === "node" ? "contained" : "outlined"}
            size="small"
          >
            Node.js
          </Button>
          <Button
            onClick={() => setTab("python")}
            variant={tab === "python" ? "contained" : "outlined"}
            size="small"
            style={{ marginLeft: 8 }}
          >
            Python
          </Button>
          <Button
            onClick={() => setTab("curl")}
            variant={tab === "curl" ? "contained" : "outlined"}
            size="small"
            style={{ marginLeft: 8 }}
          >
            Curl
          </Button>
        </div>
        <div style={{ position: "relative" }}>
          <pre
            style={{
              background: "#f5f5f5",
              padding: "1rem",
              borderRadius: 4,
              marginBottom: 0,
            }}
          >
            {code}
          </pre>
          <IconButton
            onClick={handleCopy}
            size="small"
            style={{ position: "absolute", top: 8, right: 8 }}
            aria-label="복사"
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
          {copied && (
            <span
              style={{
                position: "absolute",
                top: 12,
                right: 44,
                color: "#1976d2",
                fontSize: 13,
              }}
            >
              복사됨!
            </span>
          )}
        </div>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>닫기</Button>
      </DialogActions>
    </Dialog>
  );
};
