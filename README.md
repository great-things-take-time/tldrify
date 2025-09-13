# TLDRify - AI-Powered PDF Learning Platform

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Development Status](https://img.shields.io/badge/Status-Pre--Alpha-orange.svg)]()
[![PRD Research](https://img.shields.io/badge/PRD-Research%20Complete-blue.svg)](docs/research/prd-research-report.md)

> Transform lengthy PDFs into intelligent, digestible study materials powered by AI

## 🎯 Vision
TLDRify transforms PDF documents into interactive learning experiences using AI. It combines PDF analysis, automatic question generation, and adaptive learning paths in one seamless workflow.

**Target:** "From document to mastery in 5 minutes"

## ✨ Core Features
- 📄 **Smart PDF Processing**: OCR + AI 기반 텍스트 추출
- 🎯 **Intelligent Summarization**: 챕터별 핵심 요약
- ❓ **Auto Question Generation**: 학습 검증용 문제 자동 생성
- 🔍 **Interactive Q&A**: 문서 기반 질문 답변
- 📊 **Visual Learning**: 다이어그램, 플로우차트 자동 생성

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/tldrify.git
cd tldrify

# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn src.main:app --reload
```

## 📁 Project Structure
```
tldrify/
├── src/                     # 핵심 애플리케이션 코드
│   ├── api/                # FastAPI endpoints
│   ├── core/               # 핵심 비즈니스 로직
│   ├── services/           # OCR, AI 서비스
│   └── utils/              # 유틸리티 함수
├── ocr-poc/                # Surya OCR PoC 통합
├── docs/                   # 프로젝트 문서
│   ├── mvp-roadmap.md     # 개발 로드맵
│   ├── tech-decisions.md  # 기술 선택 기록
│   └── daily-log/         # 일일 개발 로그
├── tests/                  # 테스트 코드
└── .github/               # GitHub 설정
```

## 🗓️ MVP Timeline (8 Weeks)

### Phase 1: Foundation (Week 1-2)
- [ ] PDF 업로드 시스템
- [ ] Surya OCR 통합
- [ ] 기본 텍스트 추출

### Phase 2: Core Features (Week 3-4)
- [ ] AI 요약 기능
- [ ] 문제 생성 엔진
- [ ] 데이터베이스 설계

### Phase 3: Enhancement (Week 5-6)
- [ ] 사용자 인터페이스
- [ ] Q&A 시스템
- [ ] 성능 최적화

### Phase 4: Polish (Week 7-8)
- [ ] 테스트 & 버그 수정
- [ ] 배포 준비
- [ ] 문서화

## 🛠️ Tech Stack
- **Backend**: FastAPI, Python 3.11+
- **OCR**: Surya (Open Source OCR)
- **AI**: OpenAI GPT-4 / Claude
- **Database**: PostgreSQL + Redis
- **Frontend**: Next.js + TypeScript
- **Deployment**: Docker + AWS

## 📊 Project Status
![GitHub issues](https://img.shields.io/github/issues/YOUR_USERNAME/tldrify)
![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/tldrify)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📖 Documentation
- [MVP Roadmap](docs/mvp-roadmap.md)
- [Technical Decisions](docs/tech-decisions.md)
- [API Documentation](docs/api.md)
- [Contributing Guide](CONTRIBUTING.md)


---
*Building the future of intelligent document processing, one PDF at a time.* 🚀