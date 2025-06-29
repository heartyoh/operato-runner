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
    `const axios = require('axios');\naxios.post('/api/modules/${name}/run', { input: {} })\n  .then(res => console.log(res.data));`,
  python: (name: string) =>
    `import requests\nresp = requests.post('/api/modules/${name}/run', json={'input': {}})\nprint(resp.json())`,
  curl: (name: string) =>
    `curl -X POST '/api/modules/${name}/run' -H 'Content-Type: application/json' -d '{"input":{}}'`,
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
