# 📚 tldrify Documentation Hub

> 모든 프로젝트 문서의 중앙 허브

## 🗂️ Documentation Structure

### 📋 Planning & Strategy
- [MVP Roadmap](mvp-roadmap.md) - 8주 개발 계획
- [Technical Decisions](tech-decisions.md) - 기술 스택 선택 이유
- [Research Notes](research/) - 경쟁사 분석, 사용자 조사

### 📝 Development Logs
- [Daily Logs](daily-log/) - 일일 개발 기록
- [Weekly Reviews](weekly-reviews/) - 주간 회고 및 계획
- [Benchmarks](benchmarks/) - 성능 테스트 결과

### 🔧 Technical Documentation
- [API Reference](api.md) - API 엔드포인트 문서
- [Database Schema](database.md) - 데이터베이스 구조
- [Architecture Overview](architecture.md) - 시스템 아키텍처

### 📊 Project Management
- [Issue Templates](../.github/ISSUE_TEMPLATE/) - 이슈 템플릿
- [PR Guidelines](pr-guidelines.md) - PR 작성 가이드
- [Contributing](../CONTRIBUTING.md) - 기여 가이드

## 🚀 Quick Links

### For Developers
```bash
# Start development
npm run dev

# Run tests
npm test

# Build for production
npm run build
```


## 🔍 Search Documentation

Use GitHub's search with these patterns:
```
# Search in docs
path:docs/ "keyword"

# Search in specific file type
path:docs/ extension:md "OCR"

# Search in date range
path:docs/daily-log/ created:2025-01-01..2025-01-31
```

## 📈 Documentation Standards

### Markdown Guidelines
- Use headers hierarchically (# > ## > ###)
- Include TOC for long documents
- Add diagrams using Mermaid
- Link related documents

### Code Examples
```python
# Always include language identifier
def example():
    """Include docstrings"""
    pass
```

### Commit Messages for Docs
```
docs: Update MVP roadmap with Week 3 progress
docs: Add OCR benchmark results
docs: Fix typos in API documentation
```

## 🎯 Documentation Goals

1. **Clarity**: Anyone can understand our decisions
2. **Traceability**: Every decision is tracked
3. **Accessibility**: Easy to find information
4. **Maintainability**: Regular updates, no stale docs

---
