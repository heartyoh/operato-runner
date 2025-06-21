export function formatUtcToLocal(dateString?: string | null): string {
  if (!dateString) {
    return "";
  }

  // 서버에서 받은 시간 문자열이 UTC임을 명시합니다.
  // 예: '2025-06-21 14:07:57' -> '2025-06-21 14:07:57 UTC'
  const date = new Date(dateString + " UTC");

  // 만약 위 형식으로 파싱이 실패하면 (예: 이미 ISO 형식일 경우), 원본 문자열로 다시 시도합니다.
  if (isNaN(date.getTime())) {
    const fallbackDate = new Date(dateString);
    // 그래도 파싱에 실패하면 원본 문자열을 반환합니다.
    if (isNaN(fallbackDate.getTime())) {
      return dateString;
    }
    return fallbackDate.toLocaleString();
  }

  return date.toLocaleString();
}
