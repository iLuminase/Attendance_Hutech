# Face Recognition Service

## Overview

Production-ready face recognition system with multiple detection strategies for robust performance.

## Features

- **Multi-tier Detection**: Haar Cascade → Edge Detection → Center Region fallback
- **Automatic Optimization**: Image resizing for performance
- **Production Ready**: Clean error handling, minimal logging

## API Endpoints

### Upload Face

```http
POST /students/{student_id}/upload-face
Content-Type: multipart/form-data

file: [image file]
```

**Response Success (200)**:

```json
{
  "message": "Face uploaded and processed successfully",
  "student_id": "1",
  "face_encoding_length": 1024
}
```

**Response Error (400)**:

```json
{
  "detail": "No face detected in image. Please upload a clear photo with a visible face."
}
```

## Detection Strategy

1. **Primary**: Haar Cascade with 3 sensitivity levels
2. **Fallback**: Edge-based contour detection
3. **Last Resort**: Center region extraction

## Performance

- Images auto-resized to max 800px width
- Face encoding: 1024 features (32x32 normalized)
- Similarity threshold: 0.8 correlation coefficient

## Usage Tips

- Use clear, well-lit photos
- Face should be prominent in image
- JPG, PNG formats supported
- Recommended resolution: 400x400 to 1200x1200px
