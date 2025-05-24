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
} from "@mui/material";
import { fetchErrorLogs, downloadErrorLogs } from "../api";
import CloseIcon from "@mui/icons-material/Close";

const columns = [
  { id: "created_at", label: "발생시각", minWidth: 140 },
  { id: "code", label: "코드", minWidth: 80 },
  { id: "message", label: "메시지", minWidth: 120 },
  { id: "dev_message", label: "dev_message", minWidth: 120 },
  { id: "user", label: "User", minWidth: 80 },
  { id: "url", label: "URL", minWidth: 120 },
];

const ErrorLogViewer: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [filters, setFilters] = useState<any>({});
  const [selected, setSelected] = useState<any | null>(null);

  const fetchData = async () => {
    const params = {
      ...filters,
      limit: rowsPerPage,
      offset: page * rowsPerPage,
    };
    const data = await fetchErrorLogs(params);
    setLogs(data);
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line
  }, [page, rowsPerPage]);

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };
  const handleSearch = () => {
    setPage(0);
    fetchData();
  };
  const handleDownload = async () => {
    const params = { ...filters };
    const res = await downloadErrorLogs(params);
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "error_logs.csv");
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
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
          에러 로그 뷰어
        </Typography>
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <TextField
            label="코드"
            name="code"
            size="small"
            onChange={handleFilterChange}
          />
          <TextField
            label="User"
            name="user"
            size="small"
            onChange={handleFilterChange}
          />
          <TextField
            label="시작일"
            name="from_"
            size="small"
            type="date"
            InputLabelProps={{ shrink: true }}
            onChange={handleFilterChange}
          />
          <TextField
            label="종료일"
            name="to"
            size="small"
            type="date"
            InputLabelProps={{ shrink: true }}
            onChange={handleFilterChange}
          />
          <TextField
            label="키워드"
            name="keyword"
            size="small"
            onChange={handleFilterChange}
          />
          <Button variant="contained" onClick={handleSearch}>
            검색
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
                  {columns.map((col) => (
                    <TableCell key={col.id}>{row[col.id]}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={-1} // total count 미지원 시 -1
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(+e.target.value);
            setPage(0);
          }}
          labelDisplayedRows={({ from, to }) => `${from}-${to}`}
          rowsPerPageOptions={[10, 20, 50, 100]}
        />
        <Dialog
          open={!!selected}
          onClose={() => setSelected(null)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            에러 상세
            <IconButton
              onClick={() => setSelected(null)}
              sx={{ position: "absolute", right: 8, top: 8 }}
            >
              <CloseIcon />
            </IconButton>
          </DialogTitle>
          <DialogContent dividers>
            {selected && (
              <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
                {JSON.stringify(selected, null, 2)}
              </pre>
            )}
          </DialogContent>
        </Dialog>
      </Paper>
    </div>
  );
};

export default ErrorLogViewer;
