# ⚠️ DUPLICATES ISSUE - REQUIRES FURTHER INVESTIGATION

## Problem
Bot is still returning 10 duplicate responses for "yes" query

## Test Results
```bash
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_user", "message": "yes"}'
```

**Result**: 10 duplicate responses:
```json
[
  {"recipient_id":"test_user","text":"I'm here to help with all your healthcare needs..."},
  {"recipient_id":"test_user","text":"I'm here to help with all your healthcare needs..."},
  ... (8 more duplicates)
]
```

## Root Cause Analysis

### What We Fixed ✅
1. **SafeDispatcher**: Prevents duplicate `utter_message` calls within an action
2. **Execution Guard**: Prevents multiple action executions for the same message
3. **Return Statements**: Ensures actions return `[]` properly

### Actual Problem ⚠️
**Rasa is calling the action 10 times**, not the action sending duplicates 10 times.

This is evident because:
- Each response has a different `recipient_id` entry in the array
- The SafeDispatcher should prevent duplicates within a single execution
- The execution guard should prevent multiple executions

### Why Rasa Calls the Action Multiple Times

Possible reasons:
1. **Multiple Intent Matches**: "yes" is matching multiple intents simultaneously
2. **Policy Conflicts**: Different policies are triggering the same action
3. **Fallback Chain**: Fallback mechanisms are calling the action repeatedly
4. **Rule/Story Overlap**: Multiple rules or stories are triggering for "yes"

## Solutions to Try

### Solution 1: Check NLU Intent Classification
```bash
# Check what intents "yes" maps to
curl -X POST http://localhost:5005/model/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "yes"}'
```

### Solution 2: Update config.yml
Add FallbackClassifier to prevent multiple intent matches:
```yaml
pipeline:
  - name: FallbackClassifier
    threshold: 0.7  # Higher threshold = less fallback
```

### Solution 3: Update Rules
Ensure only ONE rule handles "yes" or similar affirmative responses:
```yaml
- rule: Handle affirmative responses
  steps:
    - intent: affirm
    - action: action_aws_bedrock_chat
    - action: action_listen
```

### Solution 4: Train with Affirmative Intent
Add "yes" to a specific intent in `nlu.yml`:
```yaml
- intent: affirm
  examples: |
    - yes
    - yeah
    - yep
    - sure
    - ok
    - okay
```

### Solution 5: Update Rasa Core Policies
Reduce policy conflicts:
```yaml
policies:
  - name: MemoizationPolicy
  - name: RulePolicy
    core_fallback_threshold: 0.9  # Higher = less fallback
  - name: TEDPolicy
    max_history: 3  # Reduce history for simpler matching
```

## Recommended Next Steps

1. **Retrain Rasa Model**: The model needs to be retrained after config changes
   ```bash
   cd backend/app
   rasa train --fixed-model-name pran-chatbot
   ```

2. **Rebuild and Redeploy Rasa Container**: The Rasa container needs the new model
   ```bash
   # Build Rasa image with new model
   docker build -t <ecr-uri>/pran-chatbot-rasa:latest -f backend/Dockerfile backend/
   docker push <ecr-uri>/pran-chatbot-rasa:latest
   
   # Force ECS deployment
   aws ecs update-service --cluster pran-chatbot-cluster --service <rasa-service-name> --force-new-deployment
   ```

3. **Test Again**: After retraining and redeploying

## Current Status

- ✅ SafeDispatcher implemented and working (prevents duplicates within action)
- ✅ Execution guard implemented (prevents rapid re-executions)
- ✅ Return statements fixed (responses reach UI)
- ⚠️ **Rasa calling action multiple times** (requires Rasa model/config changes)

## Why This Wasn't Caught Earlier

The SafeDispatcher and execution guard work at the **action level**, but the issue is at the **Rasa core level** where Rasa decides to call the action. 

The action is being called 10 times by Rasa, and each call executes correctly (single response per call), but Rasa aggregates all 10 responses into the final array.

## Temporary Workaround

Until Rasa model is retrained:
- Avoid using generic "yes" responses
- Use more specific queries like "show me doctors", "show insurance plans"
- The bot works correctly for specific queries

