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
import { getAuditLogs, downloadAuditLogs } from "../api";
import CloseIcon from "@mui/icons-material/Close";

const columns = [
  { id: "created_at", label: "발생시각", minWidth: 140 },
  { id: "username", label: "사용자명", minWidth: 100 },
  { id: "action", label: "작업", minWidth: 120 },
  { id: "detail", label: "상세 내용", minWidth: 200 },
];

const AuditLogViewer: React.FC = () => {
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
    const data = await getAuditLogs(params);
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

  const handleClearFilters = () => {
    setFilters({});
    setPage(0);
  };

  const handleDownload = async () => {
    const params = { ...filters };
    const res = await downloadAuditLogs(params);
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "audit_logs.csv");
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
          감사 로그 뷰어
        </Typography>
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <TextField
            label="작업"
            name="action"
            size="small"
            value={filters.action || ""}
            onChange={handleFilterChange}
            placeholder="작업명으로 필터링"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
          <TextField
            label="사용자명"
            name="username"
            size="small"
            value={filters.username || ""}
            onChange={handleFilterChange}
            placeholder="사용자명으로 검색"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
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
            감사 로그 상세
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
                  <strong>사용자 ID:</strong> {selected.username}
                </div>
                <div>
                  <strong>작업:</strong> {selected.action}
                </div>
                <div>
                  <strong>발생시각:</strong>{" "}
                  {new Date(selected.created_at).toLocaleString()}
                </div>
                <div>
                  <strong>상세 내용:</strong>
                  <div style={{ whiteSpace: "pre-wrap", marginTop: 8 }}>
                    {selected.detail}
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

export default AuditLogViewer;
