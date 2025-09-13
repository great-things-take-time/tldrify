#!/bin/bash

# Create GitHub Issues from Task Master tasks using GitHub CLI
echo "🚀 Creating GitHub Issues from Task Master tasks..."

REPO="great-things-take-time/tldrify"

# Task 2 (Task 1 already created)
gh issue create --repo "$REPO" \
  --title "[Task 2] Implement Enhanced PDF Upload System with Chunking" \
  --label "feature,high-priority,backend" \
  --body "## 📋 Task Overview
Build robust PDF upload system supporting files up to 100MB with chunked upload, progress tracking, and proper validation

## 🎯 Priority
**High**

## 🔗 Dependencies
- Depends on: Task #1 (Development Environment Setup)

## ✅ Definition of Done
- [ ] Drag-and-drop interface implemented
- [ ] Chunked upload for files > 10MB
- [ ] Progress bar with percentage
- [ ] File validation (PDF only, size limits)
- [ ] Error handling and retry mechanism
- [ ] Mobile responsive upload UI
- [ ] Upload status persistence

---
*Task managed by Task Master - ID: 2*"

# Task 3
gh issue create --repo "$REPO" \
  --title "[Task 3] Integrate LLMWhisperer API for Advanced PDF Text Extraction" \
  --label "feature,high-priority,ai" \
  --body "## 📋 Task Overview
Implement LLMWhisperer integration for high-quality text extraction with fallback to PyMuPDF for cost-sensitive processing

## 🎯 Priority
**High**

## 🔗 Dependencies
- Depends on: Task #2 (PDF Upload System)

## ✅ Definition of Done
- [ ] LLMWhisperer API integration complete
- [ ] PyMuPDF fallback implementation
- [ ] OCR for scanned PDFs
- [ ] Support for 15+ languages
- [ ] Table and diagram extraction
- [ ] Mathematical formula preservation
- [ ] Cost tracking per extraction

---
*Task managed by Task Master - ID: 3*"

# Task 4
gh issue create --repo "$REPO" \
  --title "[Task 4] Setup PostgreSQL Database Schema and Migrations" \
  --label "database,high-priority,infrastructure" \
  --body "## 📋 Task Overview
Design and implement comprehensive database schema for documents, users, study materials, and analytics

## 🎯 Priority
**High**

## 🔗 Dependencies
- Depends on: Task #1 (Development Environment Setup)

## ✅ Definition of Done
- [ ] PostgreSQL database configured
- [ ] SQLAlchemy models created
- [ ] Alembic migrations setup
- [ ] User table with auth fields
- [ ] Document storage schema
- [ ] Study materials tables
- [ ] Analytics tracking tables
- [ ] Indexes optimized

---
*Task managed by Task Master - ID: 4*"

# Task 5
gh issue create --repo "$REPO" \
  --title "[Task 5] Implement Redis Caching Layer and Session Management" \
  --label "infrastructure,medium-priority,performance" \
  --body "## 📋 Task Overview
Setup Redis for caching frequently accessed data, session management, and as message broker for Celery

## 🎯 Priority
**Medium**

## 🔗 Dependencies
- Depends on: Task #4 (Database Schema)

## ✅ Definition of Done
- [ ] Redis server configured
- [ ] Session storage implementation
- [ ] Document cache strategy
- [ ] API response caching
- [ ] Cache invalidation logic
- [ ] Redis Sentinel for HA
- [ ] Performance benchmarks

---
*Task managed by Task Master - ID: 5*"

# Task 6
gh issue create --repo "$REPO" \
  --title "[Task 6] Setup Celery for Asynchronous Task Processing" \
  --label "infrastructure,high-priority,backend" \
  --body "## 📋 Task Overview
Configure Celery with Redis backend for handling long-running OCR and AI processing tasks

## 🎯 Priority
**High**

## 🔗 Dependencies
- Depends on: Task #5 (Redis Setup)

## ✅ Definition of Done
- [ ] Celery worker configuration
- [ ] Task queue setup
- [ ] Retry logic implementation
- [ ] Task monitoring dashboard
- [ ] Error handling and DLQ
- [ ] Performance tuning
- [ ] Docker configuration for workers

---
*Task managed by Task Master - ID: 6*"

# Task 7
gh issue create --repo "$REPO" \
  --title "[Task 7] Build AI-Powered Summarization Engine" \
  --label "feature,high-priority,ai" \
  --body "## 📋 Task Overview
Implement intelligent summarization using GPT-4 with contextual chunking and adjustable summary lengths

## 🎯 Priority
**High**

## 🔗 Dependencies
- Depends on: Task #3 (Text Extraction), Task #6 (Celery)

## ✅ Definition of Done
- [ ] GPT-4 API integration
- [ ] Contextual chunking (200-300 words)
- [ ] Summary length options (brief/standard/detailed)
- [ ] Key concept extraction
- [ ] Hierarchical summarization
- [ ] Cost optimization logic
- [ ] Quality validation metrics

---
*Task managed by Task Master - ID: 7*"

# Task 8
gh issue create --repo "$REPO" \
  --title "[Task 8] Implement Vector Database with Qdrant" \
  --label "database,medium-priority,ai" \
  --body "## 📋 Task Overview
Setup Qdrant vector database for semantic search and hybrid retrieval system combining vector search with BM25

## 🎯 Priority
**Medium**

## 🔗 Dependencies
- Depends on: Task #7 (Summarization Engine)

## ✅ Definition of Done
- [ ] Qdrant installation and configuration
- [ ] Voyage-3-lite embeddings integration
- [ ] Vector indexing pipeline
- [ ] Hybrid search implementation (70% vector, 30% BM25)
- [ ] Search API endpoints
- [ ] Performance benchmarks
- [ ] Relevance tuning

---
*Task managed by Task Master - ID: 8*"

# Task 9
gh issue create --repo "$REPO" \
  --title "[Task 9] Create Intelligent Question Generation System" \
  --label "feature,high-priority,ai" \
  --body "## 📋 Task Overview
Build AI-powered question generator using Bloom's taxonomy to create diverse, educational questions from documents

## 🎯 Priority
**High**

## 🔗 Dependencies
- Depends on: Task #7 (Summarization Engine)

## ✅ Definition of Done
- [ ] Bloom's taxonomy implementation
- [ ] Multiple question types (MCQ, short answer, essay)
- [ ] Difficulty level adjustment
- [ ] Answer key generation
- [ ] Question quality validation
- [ ] Export to study formats
- [ ] Performance metrics

---
*Task managed by Task Master - ID: 9*"

# Task 10
gh issue create --repo "$REPO" \
  --title "[Task 10] Build Interactive Flashcard System" \
  --label "feature,medium-priority,frontend" \
  --body "## 📋 Task Overview
Create flashcard generation from key concepts with spaced repetition scheduling and export capabilities

## 🎯 Priority
**Medium**

## 🔗 Dependencies
- Depends on: Task #9 (Question Generation)

## ✅ Definition of Done
- [ ] Automatic flashcard generation
- [ ] Interactive flip cards UI
- [ ] Spaced repetition algorithm
- [ ] Progress tracking
- [ ] Export to Anki format
- [ ] Export to Quizlet format
- [ ] Mobile responsive design

---
*Task managed by Task Master - ID: 10*"

# Task 11
gh issue create --repo "$REPO" \
  --title "[Task 11] Develop Next.js Frontend Application" \
  --label "frontend,high-priority,infrastructure" \
  --body "## 📋 Task Overview
Build modern, responsive frontend using Next.js 14 with TypeScript, implementing core UI components and pages

## 🎯 Priority
**High**

## 🔗 Dependencies
- Depends on: Task #1 (Development Environment)

## ✅ Definition of Done
- [ ] Next.js 14 project setup
- [ ] TypeScript configuration
- [ ] Tailwind CSS integration
- [ ] Component library setup
- [ ] Routing structure
- [ ] Layout components
- [ ] Authentication pages
- [ ] Dashboard skeleton

---
*Task managed by Task Master - ID: 11*"

# Task 12
gh issue create --repo "$REPO" \
  --title "[Task 12] Implement Document Viewer with Annotations" \
  --label "feature,medium-priority,frontend" \
  --body "## 📋 Task Overview
Create high-fidelity PDF viewer with highlighting, annotations, and note-taking capabilities

## 🎯 Priority
**Medium**

## 🔗 Dependencies
- Depends on: Task #11 (Frontend Application)

## ✅ Definition of Done
- [ ] PDF.js integration
- [ ] Page navigation controls
- [ ] Zoom and pan functionality
- [ ] Text highlighting tool
- [ ] Annotation system
- [ ] Note-taking sidebar
- [ ] Save/load annotations
- [ ] Mobile touch support

---
*Task managed by Task Master - ID: 12*"

# Task 13
gh issue create --repo "$REPO" \
  --title "[Task 13] Build Real-time Progress Tracking System" \
  --label "feature,medium-priority,fullstack" \
  --body "## 📋 Task Overview
Implement Server-Sent Events (SSE) for real-time updates during document processing and study sessions

## 🎯 Priority
**Medium**

## 🔗 Dependencies
- Depends on: Task #11 (Frontend), Task #6 (Celery)

## ✅ Definition of Done
- [ ] SSE backend implementation
- [ ] Frontend event listeners
- [ ] Progress bar components
- [ ] Status notifications
- [ ] Processing queue display
- [ ] Error state handling
- [ ] Reconnection logic
- [ ] Mobile optimization

---
*Task managed by Task Master - ID: 13*"

# Task 14
gh issue create --repo "$REPO" \
  --title "[Task 14] Implement User Authentication and Authorization" \
  --label "security,high-priority,fullstack" \
  --body "## 📋 Task Overview
Build secure authentication system with JWT tokens, role-based access control, and social login options

## 🎯 Priority
**High**

## 🔗 Dependencies
- Depends on: Task #4 (Database), Task #11 (Frontend)

## ✅ Definition of Done
- [ ] JWT token implementation
- [ ] User registration flow
- [ ] Email verification
- [ ] Password reset functionality
- [ ] OAuth2 social login (Google, GitHub)
- [ ] Role-based permissions
- [ ] Session management
- [ ] Security best practices

---
*Task managed by Task Master - ID: 14*"

# Task 15
gh issue create --repo "$REPO" \
  --title "[Task 15] Setup Monitoring, Analytics, and Error Tracking" \
  --label "infrastructure,low-priority,observability" \
  --body "## 📋 Task Overview
Implement comprehensive monitoring with Sentry, CloudWatch, and custom analytics for user behavior tracking

## 🎯 Priority
**Low**

## 🔗 Dependencies
- Depends on: Task #14 (Authentication)

## ✅ Definition of Done
- [ ] Sentry error tracking setup
- [ ] CloudWatch metrics
- [ ] Custom analytics events
- [ ] Performance monitoring
- [ ] User behavior tracking
- [ ] Dashboard creation
- [ ] Alert configuration
- [ ] GDPR compliance

---
*Task managed by Task Master - ID: 15*"

echo "✅ All 15 tasks created successfully!"
echo "View issues at: https://github.com/$REPO/issues"