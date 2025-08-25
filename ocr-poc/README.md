# 🔬 OCR PoC Integration

## Overview
Surya OCR을 활용한 PDF 텍스트 추출 PoC

## Setup

```bash
# Clone Surya repository
git clone https://github.com/VikParuchuri/surya.git

# Install dependencies
pip install surya-ocr

# Or with poetry
poetry add surya-ocr
```

## Quick Test

```python
from surya.ocr import run_ocr
from surya.model.detection.segformer import load_model as load_det_model
from surya.model.recognition.model import load_model as load_rec_model
from PIL import Image

# Load models
det_model = load_det_model()
rec_model = load_rec_model()

# Process image
image = Image.open("sample.pdf")
results = run_ocr([image], [["en"]], det_model, rec_model)
```

## Test Files
- `/static/pdf/` - Sample PDF files from OSTEP book

## Benchmarks

| File | Pages | Processing Time | Accuracy |
|------|-------|----------------|----------|
| cpu-intro.pdf | 15 | TBD | TBD |
| cpu-sched.pdf | 28 | TBD | TBD |

## Integration Points
1. FastAPI endpoint: `/api/ocr/process`
2. Async processing with Celery
3. Result caching in Redis

## Next Steps
- [ ] Create Docker container
- [ ] Build API wrapper
- [ ] Add error handling
- [ ] Performance optimization