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
        <Typography variant="h4" gutterBottom>
          에러 로그
        </Typography>
        <Typography variant="body1" color="textSecondary" gutterBottom>
          시스템에서 발생한 에러 내역을 확인할 수 있습니다.
        </Typography>
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <TextField
            label="코드"
            name="code"
            size="small"
            onChange={handleFilterChange}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
          <TextField
            label="User"
            name="user"
            size="small"
            onChange={handleFilterChange}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
          <TextField
            label="시작일"
            name="from_"
            size="small"
            type="date"
            InputLabelProps={{ shrink: true }}
            onChange={handleFilterChange}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
          <TextField
            label="종료일"
            name="to"
            size="small"
            type="date"
            InputLabelProps={{ shrink: true }}
            onChange={handleFilterChange}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
          <TextField
            label="키워드"
            name="keyword"
            size="small"
            onChange={handleFilterChange}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
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
                  {columns.map((col) => {
                    const value = row[col.id];
                    return (
                      <TableCell key={col.id}>
                        {col.id === "created_at"
                          ? new Date(value).toLocaleString()
                          : value}
                      </TableCell>
                    );
                  })}
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
