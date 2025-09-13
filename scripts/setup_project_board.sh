#!/bin/bash

# Setup GitHub Project Board for TLDRify

echo "🚀 Setting up GitHub Project Board..."

REPO="great-things-take-time/tldrify"

# Create project (Note: This requires GitHub CLI beta features)
echo "Creating project board..."
gh project create \
  --owner great-things-take-time \
  --title "TLDRify MVP Development" \
  --description "8-week MVP development roadmap for TLDRify PDF learning platform" \
  --public

# Get project ID (you'll need to get this from the GitHub UI)
echo "📝 Manual steps required:"
echo "1. Go to: https://github.com/orgs/great-things-take-time/projects"
echo "2. Click on 'TLDRify MVP Development' project"
echo "3. Add all issues to the project board"
echo "4. Create the following columns:"
echo "   - 📋 Backlog"
echo "   - 🚀 Ready"
echo "   - 🔄 In Progress"
echo "   - 👀 Review"
echo "   - ✅ Done"
echo ""
echo "5. Set up automation rules:"
echo "   - When issue opened → Add to Backlog"
echo "   - When issue assigned → Move to In Progress"
echo "   - When issue closed → Move to Done"
echo ""
echo "6. Add milestones:"
echo "   - Week 1-2: Core Infrastructure"
echo "   - Week 3-4: AI Integration"
echo "   - Week 5-6: Smart Features"
echo "   - Week 7-8: Polish & Launch"

# Create labels if they don't exist
echo "Creating labels..."
gh label create "high-priority" --color "d73a4a" --description "High priority tasks" --repo "$REPO" 2>/dev/null || true
gh label create "medium-priority" --color "fbca04" --description "Medium priority tasks" --repo "$REPO" 2>/dev/null || true
gh label create "low-priority" --color "0e8a16" --description "Low priority tasks" --repo "$REPO" 2>/dev/null || true
gh label create "setup" --color "1d76db" --description "Setup and configuration" --repo "$REPO" 2>/dev/null || true
gh label create "feature" --color "a2eeef" --description "New feature" --repo "$REPO" 2>/dev/null || true
gh label create "infrastructure" --color "c5def5" --description "Infrastructure and DevOps" --repo "$REPO" 2>/dev/null || true
gh label create "ai" --color "7057ff" --description "AI/ML related" --repo "$REPO" 2>/dev/null || true
gh label create "backend" --color "d4c5f9" --description "Backend development" --repo "$REPO" 2>/dev/null || true
gh label create "frontend" --color "008672" --description "Frontend development" --repo "$REPO" 2>/dev/null || true
gh label create "database" --color "ee0701" --description "Database related" --repo "$REPO" 2>/dev/null || true
gh label create "security" --color "b60205" --description "Security related" --repo "$REPO" 2>/dev/null || true
gh label create "performance" --color "ffd93d" --description "Performance optimization" --repo "$REPO" 2>/dev/null || true
gh label create "fullstack" --color "5319e7" --description "Full stack development" --repo "$REPO" 2>/dev/null || true
gh label create "observability" --color "bfd4f2" --description "Monitoring and observability" --repo "$REPO" 2>/dev/null || true

echo "✅ Labels created successfully!"

# Create milestones
echo "Creating milestones..."
gh api repos/$REPO/milestones \
  --method POST \
  --field title="Week 1-2: Core Infrastructure" \
  --field description="Setup development environment, database, and basic upload system" \
  --field due_on="2025-02-08T23:59:59Z" || true

gh api repos/$REPO/milestones \
  --method POST \
  --field title="Week 3-4: AI Integration" \
  --field description="Integrate LLMWhisperer, implement text extraction and basic AI features" \
  --field due_on="2025-02-22T23:59:59Z" || true

gh api repos/$REPO/milestones \
  --method POST \
  --field title="Week 5-6: Smart Features" \
  --field description="Build summarization engine, question generation, and study tools" \
  --field due_on="2025-03-08T23:59:59Z" || true

gh api repos/$REPO/milestones \
  --method POST \
  --field title="Week 7-8: Polish & Launch" \
  --field description="Frontend polish, authentication, monitoring, and MVP launch preparation" \
  --field due_on="2025-03-22T23:59:59Z" || true

echo "✅ Milestones created successfully!"

echo ""
echo "📊 Project board setup complete!"
echo "View your project at: https://github.com/orgs/great-things-take-time/projects"
echo "View issues at: https://github.com/$REPO/issues"