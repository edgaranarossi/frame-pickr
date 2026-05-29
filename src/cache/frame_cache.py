"""Frame cache system for the Frame Capture Application.

Implements a circular buffer for frame storage with disk persistence.
"""

import os
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image


@dataclass
class FrameMetadata:
    """Metadata for a captured frame."""
    index: int
    timestamp: float
    file_path: str
    dimensions: Tuple[int, int]  # (width, height)


class FrameCache:
    """Circular buffer for frame storage with disk persistence.
    
    Manages up to MAX_FRAMES frames, automatically deleting the oldest
    when the cache is full. Frames are stored as PNG files on disk.
    
    Attributes:
        max_frames: Maximum number of frames to cache
        frame_count: Current number of frames in cache
    """
    
    def __init__(self, max_frames: int = 200):
        """Initialize the frame cache.
        
        Args:
            max_frames: Maximum number of frames to cache (default: 200)
        """
        self.max_frames = max_frames
        self._frames: OrderedDict[int, FrameMetadata] = OrderedDict()
        self._next_index = 0
        self._temp_directory = Path(os.environ.get('TEMP', 'C:\\Temp')) / "frame-capture-cache"
        self._temp_directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def frame_count(self) -> int:
        """Get current number of frames in cache."""
        return len(self._frames)
    
    @property
    def is_full(self) -> bool:
        """Check if cache is at capacity."""
        return len(self._frames) >= self.max_frames
    
    def add_frame(self, frame_data: np.ndarray, timestamp: Optional[float] = None) -> Optional[FrameMetadata]:
        """Add a new frame to the cache.
        
        If the cache is full, the oldest frame will be deleted.
        
        Args:
            frame_data: Frame as numpy array (BGR format)
            timestamp: Frame timestamp (default: current time)
            
        Returns:
            FrameMetadata for the added frame, or None if failed
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Check if frame data is valid
        if frame_data is None or frame_data.size == 0:
            return None
        
        # Get dimensions
        height, width = frame_data.shape[:2]
        
        # Generate filename
        filename = f"frame_{self._next_index:06d}.png"
        file_path = str(self._temp_directory / filename)
        
        try:
            # Save frame as PNG
            image = Image.fromarray(frame_data)
            image.save(file_path, format='PNG', compress_level=1)
            
            # Create metadata
            metadata = FrameMetadata(
                index=self._next_index,
                timestamp=timestamp,
                file_path=file_path,
                dimensions=(width, height)
            )
            
            # Add to cache
            self._frames[self._next_index] = metadata
            self._next_index += 1
            
            # Remove oldest frame if cache is full
            if len(self._frames) > self.max_frames:
                oldest_index = next(iter(self._frames))
                oldest_metadata = self._frames.pop(oldest_index)
                try:
                    os.remove(oldest_metadata.file_path)
                except OSError:
                    pass  # Ignore removal errors
            
            return metadata
            
        except Exception as e:
            return None
    
    def get_frame(self, index: int) -> Optional[FrameMetadata]:
        """Get frame metadata by index.
        
        Args:
            index: Frame index
            
        Returns:
            FrameMetadata if found, None otherwise
        """
        return self._frames.get(index)
    
    def get_frame_data(self, index: int) -> Optional[np.ndarray]:
        """Get frame image data by index.
        
        Args:
            index: Frame index
            
        Returns:
            Frame as numpy array (BGR format), or None if not found
        """
        metadata = self.get_frame(index)
        if metadata is None:
            return None
        
        try:
            image = Image.open(metadata.file_path)
            return np.array(image.convert('RGB'))
        except Exception:
            return None
    
    def get_all_frames(self) -> List[FrameMetadata]:
        """Get all frame metadata in order.
        
        Returns:
            List of FrameMetadata objects
        """
        return list(self._frames.values())
    
    def get_next_index(self) -> int:
        """Get the next frame index that will be used."""
        return self._next_index
    
    def get_previous_index(self, index: int) -> Optional[int]:
        """Get the previous frame index.
        
        Args:
            index: Current frame index
            
        Returns:
            Previous frame index, or None if at the beginning
        """
        indices = list(self._frames.keys())
        try:
            current_pos = indices.index(index)
            if current_pos > 0:
                return indices[current_pos - 1]
        except ValueError:
            pass
        return None
    
    def get_next_index_in_order(self, index: int) -> Optional[int]:
        """Get the next frame index in display order.
        
        Args:
            index: Current frame index
            
        Returns:
            Next frame index, or None if at the end
        """
        indices = list(self._frames.keys())
        try:
            current_pos = indices.index(index)
            if current_pos < len(indices) - 1:
                return indices[current_pos + 1]
        except ValueError:
            pass
        return None
    
    def clear_cache(self) -> int:
        """Clear all cached frames.
        
        Returns:
            Number of frames cleared
        """
        count = len(self._frames)
        for metadata in self._frames.values():
            try:
                os.remove(metadata.file_path)
            except OSError:
                pass
        self._frames.clear()
        return count
    
    def get_indices_in_order(self) -> List[int]:
        """Get all frame indices in display order (oldest to newest).
        
        Returns:
            List of frame indices
        """
        return list(self._frames.keys())
    
    def get_oldest_frame_index(self) -> Optional[int]:
        """Get the oldest frame index.
        
        Returns:
            Oldest frame index, or None if cache is empty
        """
        if not self._frames:
            return None
        return next(iter(self._frames))
    
    def get_newest_frame_index(self) -> Optional[int]:
        """Get the newest frame index.
        
        Returns:
            Newest frame index, or None if cache is empty
        """
        if not self._frames:
            return None
        return list(self._frames.keys())[-1]