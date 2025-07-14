import cv2
import base64
import numpy as np
import os
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class VideoChunk:
    start_time: float
    end_time: float
    frames: List[str]  # Base64 encoded frames
    formatted_timestamp: str


class VideoChunker:
    def __init__(self, chunk_duration: float = 5.0, frames_per_chunk: int = 3):
        self.chunk_duration = chunk_duration
        self.frames_per_chunk = frames_per_chunk

    def _encode_frame(self, frame: np.ndarray) -> str:
        _, buffer = cv2.imencode('.jpeg', frame)
        return base64.b64encode(buffer).decode('utf-8')
    
    def _format_timestamp(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"[{minutes:02d}:{seconds:02d}]"
    
    def chunk_video(self, video_path: str) -> List[VideoChunk]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        chunks = []
        current_time = 0.0
        
        while current_time < duration:
            end_time = min(current_time + self.chunk_duration, duration)
            chunk = self._extract_chunk_frames(cap, current_time, end_time, fps)
            if chunk.frames:
                chunks.append(chunk)
            current_time = end_time
        
        cap.release()
        return chunks
    
    def _extract_chunk_frames(self, cap: cv2.VideoCapture, start_time: float, 
                            end_time: float, fps: float) -> VideoChunk:
        chunk_duration = end_time - start_time
        frame_interval = chunk_duration / (self.frames_per_chunk + 1)
        
        frames = []
        
        for i in range(1, self.frames_per_chunk + 1):
            timestamp = start_time + i * frame_interval
            frame = self._get_frame_at_time(cap, timestamp, fps)
            if frame is not None:
                encoded_frame = self._encode_frame(frame)
                frames.append(encoded_frame)
        
        return VideoChunk(
            start_time=start_time,
            end_time=end_time,
            frames=frames,
            formatted_timestamp=self._format_timestamp(start_time)
        )
    
    def _get_frame_at_time(self, cap: cv2.VideoCapture, timestamp: float, 
                          fps: float) -> np.ndarray:
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        return frame if ret else None

if __name__ == "__main__":
    chunker = VideoChunker(chunk_duration=5.0, frames_per_chunk=3)
    
    video_path = "sample.mp4"
    if os.path.exists(video_path):
        try:
            chunks = chunker.chunk_video(video_path)
            print(f"成功切分视频，共 {len(chunks)} 个片段：")
            
            for i, chunk in enumerate(chunks):
                print(f"片段 {i+1}: {chunk.formatted_timestamp} ({chunk.start_time:.1f}s-{chunk.end_time:.1f}s) - {len(chunk.frames)} 帧")
            
        except Exception as e:
            print(f"处理视频时出错: {e}")
    else:
        print("请提供 sample.mp4 文件进行测试") 