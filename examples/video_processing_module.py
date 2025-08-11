"""
동영상 처리 모듈 예제
- 입력: 동영상 파일
- 출력: 프레임 이미지들
"""

def handler(input):
    """
    동영상에서 프레임을 추출하는 예제 핸들러
    
    Args:
        input (dict): 입력 데이터
            - input_files: [{"path": "파일경로", "filename": "원본파일명"}]
            - frame_interval: 프레임 추출 간격 (기본값: 30)
            - max_frames: 최대 추출 프레임 수 (기본값: 10)
    
    Returns:
        dict: 처리 결과
            - processed_frames: 처리된 프레임 수
            - output_files: 생성된 이미지 파일 경로 목록
            - video_info: 동영상 정보
    """
    import cv2
    import os
    import tempfile
    
    # 입력 파라미터 추출
    input_files = input.get('input_files', [])
    frame_interval = input.get('frame_interval', 30)
    max_frames = input.get('max_frames', 10)
    
    if not input_files:
        return {"error": "No input files provided"}
    
    video_file = input_files[0]  # 첫 번째 파일을 동영상으로 사용
    video_path = video_file['path']
    
    # 동영상 열기
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": f"Cannot open video file: {video_file['filename']}"}
    
    # 동영상 정보 수집
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 결과 저장용 임시 디렉토리 생성
    output_dir = tempfile.mkdtemp()
    output_files = []
    
    processed_frames = 0
    current_frame = 0
    
    try:
        while processed_frames < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 지정된 간격으로만 프레임 처리
            if current_frame % frame_interval == 0:
                # 간단한 이미지 처리 (예: 그레이스케일 변환)
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                colored_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)
                
                # 파일 저장
                output_filename = f"frame_{processed_frames:04d}.jpg"
                output_path = os.path.join(output_dir, output_filename)
                
                success = cv2.imwrite(output_path, colored_frame)
                if success:
                    output_files.append(output_path)
                    processed_frames += 1
            
            current_frame += 1
    
    finally:
        cap.release()
    
    return {
        "processed_frames": processed_frames,
        "output_files": output_files,
        "video_info": {
            "original_filename": video_file['filename'],
            "fps": fps,
            "total_frames": frame_count,
            "duration_seconds": duration,
            "resolution": f"{width}x{height}"
        },
        "processing_params": {
            "frame_interval": frame_interval,
            "max_frames": max_frames
        }
    }