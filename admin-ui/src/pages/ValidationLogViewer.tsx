import React, { useEffect, useState } from "react";
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Button,
  TextField,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";
import { getValidationLogs, downloadValidationLogs } from "../api";
import CloseIcon from "@mui/icons-material/Close";

const columns = [
  { id: "created_at", label: "생성시각", minWidth: 140 },
  { id: "filename", label: "파일명", minWidth: 150 },
  { id: "status", label: "상태", minWidth: 100 },
  { id: "message", label: "메시지", minWidth: 200 },
];

const ValidationLogViewer: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [filters, setFilters] = useState<any>({});
  const [selected, setSelected] = useState<any | null>(null);

  const fetchData = async () => {
    const params = {
      ...filters,
      limit: rowsPerPage,
    };
    const data = await getValidationLogs(params);
    setLogs(data);
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line
  }, [page, rowsPerPage]);

  // 상태(status) 변경 시 자동 검색
  useEffect(() => {
    if (filters.status !== undefined) {
      handleSearch();
    }
    // eslint-disable-next-line
  }, [filters.status]);

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  const handleSearch = () => {
    setPage(0);
    fetchData();
  };

  const handleClearFilters = () => {
    setFilters({});
    setPage(0);
  };

  const handleDownload = async () => {
    const params = { ...filters };
    const res = await downloadValidationLogs(params);
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "validation_logs.csv");
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
  };

  const getStatusColor = (status: string) => {
    return status === "success" ? "success" : "error";
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        width: "100%",
        marginTop: 40,
      }}
    >
      <Paper
        sx={{
          p: 3,
          maxWidth: 1200,
          minWidth: 1200,
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <Typography variant="h5" gutterBottom>
          모듈 검증 로그 뷰어
        </Typography>
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <TextField
            label="모듈명"
            name="module_name"
            size="small"
            value={filters.module_name || ""}
            onChange={handleFilterChange}
            placeholder="모듈명으로 필터링"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="status-label">상태</InputLabel>
            <Select
              labelId="status-label"
              name="status"
              value={filters.status || ""}
              label="상태"
              onChange={(e) =>
                setFilters({ ...filters, status: e.target.value })
              }
            >
              <MenuItem value="">전체</MenuItem>
              <MenuItem value="success">success</MenuItem>
              <MenuItem value="fail">fail</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="시작일"
            name="from_date"
            size="small"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={filters.from_date || ""}
            onChange={handleFilterChange}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
          <TextField
            label="종료일"
            name="to_date"
            size="small"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={filters.to_date || ""}
            onChange={handleFilterChange}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
          <Button variant="contained" onClick={handleSearch}>
            검색
          </Button>
          <Button variant="outlined" onClick={handleClearFilters}>
            필터 초기화
          </Button>
          <Button variant="outlined" onClick={handleDownload}>
            다운로드
          </Button>
        </Stack>
        <TableContainer sx={{ maxHeight: 600 }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                {columns.map((col) => (
                  <TableCell key={col.id} style={{ minWidth: col.minWidth }}>
                    {col.label}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map((row) => (
                <TableRow
                  hover
                  key={row.id}
                  onClick={() => setSelected(row)}
                  style={{ cursor: "pointer" }}
                >
                  <TableCell>
                    {new Date(row.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell>{row.filename}</TableCell>
                  <TableCell>
                    <Chip
                      label={row.status}
                      color={getStatusColor(row.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {row.message && row.message.length > 50
                      ? `${row.message.substring(0, 50)}...`
                      : row.message}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={-1} // total count 미지원 시 -1
          page={page}
          onPageChange={(
            event: React.MouseEvent<HTMLButtonElement> | null,
            newPage: number
          ) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            setRowsPerPage(+e.target.value);
            setPage(0);
          }}
          labelDisplayedRows={({ from, to }: { from: number; to: number }) =>
            `${from}-${to}`
          }
          rowsPerPageOptions={[10, 20, 50, 100]}
        />
        <Dialog
          open={!!selected}
          onClose={() => setSelected(null)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            검증 로그 상세
            <IconButton
              onClick={() => setSelected(null)}
              sx={{ position: "absolute", right: 8, top: 8 }}
            >
              <CloseIcon />
            </IconButton>
          </DialogTitle>
          <DialogContent>
            {selected && (
              <Stack spacing={2}>
                <div>
                  <strong>ID:</strong> {selected.id}
                </div>
                <div>
                  <strong>파일명:</strong> {selected.filename}
                </div>
                <div>
                  <strong>상태:</strong>{" "}
                  <Chip
                    label={selected.status}
                    color={getStatusColor(selected.status) as any}
                    size="small"
                  />
                </div>
                <div>
                  <strong>생성시각:</strong>{" "}
                  {new Date(selected.created_at).toLocaleString()}
                </div>
                <div>
                  <strong>메시지:</strong>
                  <div style={{ whiteSpace: "pre-wrap", marginTop: 8 }}>
                    {selected.message}
                  </div>
                </div>
              </Stack>
            )}
          </DialogContent>
        </Dialog>
      </Paper>
    </div>
  );
};

export default ValidationLogViewer;
