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
} from "@mui/material";
import { getAuditLogs } from "../api";

const columns = [
  { id: "created_at", label: "발생시각", minWidth: 140 },
  { id: "user_id", label: "사용자 ID", minWidth: 80 },
  { id: "action", label: "작업", minWidth: 120 },
  { id: "detail", label: "상세 내용", minWidth: 200 },
];

const AuditLogViewer: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);

  const fetchData = async () => {
    const params = {
      limit: rowsPerPage,
      offset: page * rowsPerPage,
    };
    const data = await getAuditLogs(params);
    setLogs(data);
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line
  }, [page, rowsPerPage]);

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
                <TableRow hover key={row.id}>
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
      </Paper>
    </div>
  );
};

export default AuditLogViewer;
