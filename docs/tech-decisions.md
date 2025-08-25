# 🔧 Technical Decisions Log

> 모든 주요 기술 결정사항을 기록하고 추적합니다.

## 📋 Decision Template
```markdown
## [Technology/Feature Name]
**Decision**: 선택한 기술/접근법
**Date**: YYYY-MM-DD
**Status**: 🟢 Confirmed | 🟡 Testing | 🔴 Deprecated
**Alternatives Considered**: 검토한 대안들
**Reason**: 선택 이유
**Trade-offs**: 장단점
**Related Issues**: #XX, #XX
```

---

## 🎯 Core Architecture

### Backend Framework
**Decision**: FastAPI
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**: Django, Flask, Express.js
**Reason**: 
- Native async support for OCR processing
- Automatic API documentation (Swagger/Redoc)
- Type hints and validation with Pydantic
- High performance for ML workloads
**Trade-offs**: 
- ✅ Fast, modern, great DX
- ✅ Built-in validation
- ❌ Smaller ecosystem than Django
- ❌ Less built-in features (admin, auth)
**Related Issues**: #2

---

## 📄 PDF Processing

### OCR Engine
**Decision**: Surya (Open Source) → LLMWhisperer (Phase 2)
**Date**: 2025-01-27
**Status**: 🟡 Testing
**Alternatives Considered**: 
- Tesseract OCR
- Azure Document Intelligence
- Google Cloud Document AI
- Adobe PDF Services
**Reason**:
- Surya: Free, decent accuracy, good for PoC
- LLMWhisperer: Better table/diagram extraction for production
**Trade-offs**:
- Surya:
  - ✅ Free and open source
  - ✅ Good baseline accuracy
  - ❌ Slower processing
  - ❌ Limited layout understanding
- LLMWhisperer:
  - ✅ Excellent accuracy
  - ✅ Table/diagram support
  - ❌ $50-100/month cost
  - ❌ API dependency
**Related Issues**: #4, #12

### Text Chunking Strategy
**Decision**: Semantic Chunking with LangChain
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**:
- Fixed-size chunks (1000 tokens)
- Page-based splitting
- Paragraph-based splitting
**Reason**:
- Preserves semantic meaning
- Better for RAG performance
- Handles cross-page content well
**Trade-offs**:
- ✅ Better context preservation
- ✅ Improved Q&A accuracy
- ❌ More complex implementation
- ❌ Slightly slower processing
**Related Issues**: #6

---

## 🤖 AI/ML Stack

### LLM Provider
**Decision**: OpenAI GPT-4 (primary) + Claude 3 (fallback)
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**:
- Local LLMs (Llama 3, Mistral)
- Google Gemini
- Cohere
**Reason**:
- Best accuracy for academic content
- Reliable API availability
- Good Korean language support
**Trade-offs**:
- ✅ State-of-the-art performance
- ✅ Reliable uptime
- ❌ Cost ($0.03-0.06 per 1K tokens)
- ❌ Privacy concerns for sensitive docs
**Related Issues**: #9

### Vector Database
**Decision**: Pinecone (managed)
**Date**: 2025-01-27
**Status**: 🟡 Testing
**Alternatives Considered**:
- Weaviate
- Qdrant
- pgvector (PostgreSQL extension)
- ChromaDB
**Reason**:
- Fully managed, no ops overhead
- Great performance at scale
- Good Python SDK
**Trade-offs**:
- ✅ Zero maintenance
- ✅ Automatic scaling
- ❌ Vendor lock-in
- ❌ Monthly cost ($70+)
**Related Issues**: #22

---

## 💾 Data Layer

### Primary Database
**Decision**: PostgreSQL 15
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**:
- MongoDB
- MySQL
- SQLite
**Reason**:
- JSONB for flexible metadata
- Full-text search capabilities
- Rock-solid reliability
- pgvector extension option
**Trade-offs**:
- ✅ ACID compliance
- ✅ Complex queries support
- ✅ Extensions ecosystem
- ❌ Vertical scaling limits
**Related Issues**: #5

### Caching Layer
**Decision**: Redis
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**:
- Memcached
- In-memory cache
- DynamoDB
**Reason**:
- Job queue support (with Celery)
- Session management
- Fast response caching
**Trade-offs**:
- ✅ Versatile (cache + queue)
- ✅ Pub/sub capabilities
- ❌ Memory limits
- ❌ Persistence complexity
**Related Issues**: #7

### Task Queue
**Decision**: Celery + Redis
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**:
- RQ (Redis Queue)
- Dramatiq
- AWS SQS
- BullMQ
**Reason**:
- Mature, battle-tested
- Great FastAPI integration
- Scheduled tasks support
**Trade-offs**:
- ✅ Feature-rich
- ✅ Monitoring tools
- ❌ Complex configuration
- ❌ Learning curve
**Related Issues**: #3

---

## 🎨 Frontend

### Framework
**Decision**: Next.js 14 (App Router)
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**:
- React SPA (Vite)
- Vue.js
- SvelteKit
- Angular
**Reason**:
- Server components for better performance
- Built-in optimization
- Great TypeScript support
- Vercel deployment option
**Trade-offs**:
- ✅ Full-stack capabilities
- ✅ SEO friendly
- ✅ Image optimization
- ❌ Complexity for simple apps
- ❌ Vendor influence (Vercel)
**Related Issues**: #17

### UI Library
**Decision**: shadcn/ui + Tailwind CSS
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**:
- Material-UI
- Ant Design
- Chakra UI
- Bootstrap
**Reason**:
- Copy-paste components (no bloat)
- Highly customizable
- Modern design system
- Radix UI primitives
**Trade-offs**:
- ✅ Full control
- ✅ No dependencies
- ✅ Tree-shakeable
- ❌ More initial setup
- ❌ Need to build some components
**Related Issues**: #18

### State Management
**Decision**: Zustand + React Query
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**:
- Redux Toolkit
- MobX
- Valtio
- Context API only
**Reason**:
- Zustand: Simple, lightweight for UI state
- React Query: Perfect for server state
- Great TypeScript support
**Trade-offs**:
- ✅ Minimal boilerplate
- ✅ Great DX
- ✅ Small bundle size
- ❌ Less ecosystem than Redux
**Related Issues**: #19

---

## 🚀 Infrastructure

### Container Platform
**Decision**: Docker + Docker Compose
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**:
- Podman
- Kubernetes (overkill for MVP)
- Direct deployment
**Reason**:
- Standard in industry
- Easy local development
- Smooth cloud transition
**Trade-offs**:
- ✅ Reproducible environments
- ✅ Easy deployment
- ❌ Resource overhead
- ❌ Complexity for beginners
**Related Issues**: #30

### Cloud Provider
**Decision**: AWS (primary) with multi-cloud ready
**Date**: 2025-01-27
**Status**: 🟡 Testing
**Alternatives Considered**:
- Google Cloud Platform
- Azure
- DigitalOcean
- Vercel + Supabase
**Reason**:
- Free tier for MVP
- Comprehensive services
- Market leader
**Trade-offs**:
- ✅ Feature-complete
- ✅ Good free tier
- ❌ Complex pricing
- ❌ Steep learning curve
**Related Issues**: #32

### CI/CD
**Decision**: GitHub Actions
**Date**: 2025-01-27
**Status**: 🟢 Confirmed
**Alternatives Considered**:
- GitLab CI
- CircleCI
- Jenkins
- Travis CI
**Reason**:
- Native GitHub integration
- Free for public repos
- Great marketplace
**Trade-offs**:
- ✅ Zero setup
- ✅ YAML configuration
- ❌ Vendor lock-in
- ❌ Limited self-hosted options
**Related Issues**: #31

---

## 🔒 Security & Auth

### Authentication
**Decision**: NextAuth.js (Auth.js)
**Date**: 2025-01-27
**Status**: 🟡 Testing
**Alternatives Considered**:
- Clerk
- Auth0
- Supabase Auth
- Custom JWT
**Reason**:
- Free and open source
- Multiple providers
- Edge compatible
**Trade-offs**:
- ✅ Full control
- ✅ No vendor lock-in
- ❌ More setup work
- ❌ Need to handle edge cases
**Related Issues**: #29

---

## 📊 Monitoring

### APM & Logging
**Decision**: Sentry + CloudWatch
**Date**: 2025-01-27
**Status**: 🟡 Testing
**Alternatives Considered**:
- DataDog
- New Relic
- Elastic Stack
- Grafana Stack
**Reason**:
- Sentry: Great error tracking
- CloudWatch: Native AWS integration
- Both have free tiers
**Trade-offs**:
- ✅ Good free tier
- ✅ Easy setup
- ❌ Limited features vs DataDog
- ❌ Two systems to manage
**Related Issues**: #33

---

## 🔄 Future Considerations

### Phase 2 Upgrades
- [ ] GraphQL API layer
- [ ] Microservices architecture
- [ ] Kubernetes orchestration
- [ ] Multi-tenant architecture
- [ ] Real-time collaboration

### Cost Optimization
- [ ] Spot instances for OCR
- [ ] S3 intelligent tiering
- [ ] Lambda for sporadic tasks
- [ ] CDN for static assets

---

*Last Updated: 2025-01-27*
*Review Schedule: Weekly with tech team*