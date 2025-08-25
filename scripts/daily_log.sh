#!/bin/bash

# Daily log automation script
DATE=$(date +'%Y-%m-%d')
TIME=$(date +'%H:%M')
LOG_FILE="docs/daily-log/${DATE}.md"

# Create log file if it doesn't exist
if [ ! -f "$LOG_FILE" ]; then
    cat > "$LOG_FILE" << EOF
# 📅 Daily Log - ${DATE}

## 🎯 Today's Goal
- [ ] 

## ✅ Completed
- [ ] 

## 🚧 In Progress
- [ ] 

## 📝 Key Decisions

## 💡 Insights & Notes

## 🐛 Issues & Blockers

## 🔗 References

## 📊 Metrics
- Commits: 
- Files Created: 
- Tests Passed: 

## 🚀 Tomorrow's Plan
- [ ] 

---
Previous: [$(date -v-1d +'%Y-%m-%d').md]($(date -v-1d +'%Y-%m-%d').md) | Next: [$(date -v+1d +'%Y-%m-%d').md]($(date -v+1d +'%Y-%m-%d').md)
EOF
    echo "✅ Created daily log: $LOG_FILE"
else
    echo "📝 Daily log already exists: $LOG_FILE"
fi

# Open in default editor
${EDITOR:-code} "$LOG_FILE"