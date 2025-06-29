import React, { useState } from "react";
import { MenuItem, Select, TextField, Stack } from "@mui/material";

interface Props {
  currentVersion: string;
  value: string;
  onChange: (v: string) => void;
}

const VersionSelectInput: React.FC<Props> = ({
  currentVersion,
  value,
  onChange,
}) => {
  const [mode, setMode] = useState<"auto" | "manual">(
    value ? "auto" : "manual"
  );
  const [manual, setManual] = useState("");
  // 신규 모듈 여부 판단
  const isInitial =
    !currentVersion || currentVersion === "0.0.0" || currentVersion === "0.1.0";
  let patchNext = "",
    minorNext = "",
    majorNext = "";
  if (isInitial) {
    patchNext = "0.0.1";
    minorNext = "0.1.0";
    majorNext = "1.0.0";
  } else {
    const [major, minor, patch] = (currentVersion || "0.1.0")
      .split(".")
      .map(Number);
    patchNext = `${major}.${minor}.${(patch || 0) + 1}`;
    minorNext = `${major}.${(minor || 0) + 1}.0`;
    majorNext = `${(major || 0) + 1}.0.0`;
  }

  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <Select
        size="small"
        value={mode === "manual" ? "manual" : value}
        onChange={(e) => {
          if (e.target.value === "manual") {
            setMode("manual");
            onChange(manual);
          } else {
            setMode("auto");
            onChange(e.target.value);
          }
        }}
        style={{ width: 140 }}
      >
        <MenuItem value={patchNext}>{patchNext} (패치)</MenuItem>
        <MenuItem value={minorNext}>{minorNext} (마이너)</MenuItem>
        <MenuItem value={majorNext}>{majorNext} (메이저)</MenuItem>
        <MenuItem value="manual">직접 입력</MenuItem>
      </Select>
      {mode === "manual" && (
        <TextField
          size="small"
          value={manual}
          onChange={(e) => {
            setManual(e.target.value);
            onChange(e.target.value);
          }}
          placeholder="버전 (예: 0.2.0)"
          style={{ width: 120 }}
          required
        />
      )}
    </Stack>
  );
};

export default VersionSelectInput;
