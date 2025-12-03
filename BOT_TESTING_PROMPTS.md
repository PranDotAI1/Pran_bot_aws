# 🧪 Pran.AI Chatbot Testing Guide

## 📍 Testing URL
**Amplify App**: https://main.d1fw711o7cx5w2.amplifyapp.com/

## 🎯 Testing Objectives

This document provides comprehensive test prompts to verify all chatbot capabilities including:
- Basic conversation flow
- Doctor search and recommendations
- Appointment booking
- Insurance information
- Symptom assessment
- RAG (database retrieval) functionality
- "Yes/No" handling
- Duplicate prevention

---

## 🧪 Test Scenarios

### 1. Basic Conversation & Greeting

#### Test Case 1.1: Simple Greeting
**Prompt**: `Hello`

**Expected Response**:
- Single response (not duplicates)
- Greeting from Dr. AI
- Mentions capabilities (appointments, insurance, finding doctors, etc.)

**Pass Criteria**: ✅ Single response, friendly greeting

---

#### Test Case 1.2: Time-based Greeting
**Prompt**: `Good morning`

**Expected Response**:
- Appropriate greeting
- Offers help

**Pass Criteria**: ✅ Single response, contextual greeting

---

#### Test Case 1.3: How can you help?
**Prompt**: `How can you help me?`

**Expected Response**:
- List of capabilities
- Examples of what the bot can do
- Encouragement to ask questions

**Pass Criteria**: ✅ Comprehensive list of services

---

### 2. Symptom Assessment & Doctor Recommendations

#### Test Case 2.1: General Symptoms
**Prompt**: `I am suffering from viral`

**Expected Response**:
- Acknowledges health concern
- Offers to find appropriate doctor
- Asks if user wants to search for doctors

**Pass Criteria**: ✅ Empathetic response, actionable next step

---

#### Test Case 2.2: Affirmative Response (CRITICAL)
**Setup**: After Test Case 2.1
**Prompt**: `yes`

**Expected Response**:
- **SINGLE response only** (NOT 10 duplicates)
- Shows list of available doctors
- Includes doctor details (name, specialty, contact)
- From database if available

**Pass Criteria**: ✅ SINGLE response, shows doctors list

---

#### Test Case 2.3: Specific Symptom
**Prompt**: `I have fever and cough`

**Expected Response**:
- Recommends general physician
- Offers to find available doctors
- May show doctor list from database

**Pass Criteria**: ✅ Appropriate specialty recommendation

---

#### Test Case 2.4: Specific Specialty Request
**Prompt**: `I need a gynecologist`

**Expected Response**:
- Acknowledges request
- Shows available gynecologists from database
- Includes contact information
- Offers to book appointment

**Pass Criteria**: ✅ Shows gynecologist list from database

---

### 3. Doctor Search

#### Test Case 3.1: General Doctor Search
**Prompt**: `suggest me some doctors`

**Expected Response**:
- List of available doctors from database
- Doctor details (name, specialty, department, phone)
- Offers to book appointment

**Pass Criteria**: ✅ Shows multiple doctors with details

---

#### Test Case 3.2: Specialty-specific Search
**Prompt**: `show me cardiologists`

**Expected Response**:
- List of cardiologists from database
- Doctor details
- Booking option

**Pass Criteria**: ✅ Shows cardiologist-specific list

---

#### Test Case 3.3: All Doctors
**Prompt**: `show all available doctors`

**Expected Response**:
- Comprehensive list of doctors
- Multiple specialties
- Contact information

**Pass Criteria**: ✅ Shows extensive doctor list

---

### 4. Insurance Information

#### Test Case 4.1: General Insurance Query
**Prompt**: `I need help with insurance`

**Expected Response**:
- Insurance plan recommendations
- Shows multiple plan options
- Details (premium, deductible, coverage)
- Asks if user wants more details

**Pass Criteria**: ✅ Shows insurance plans with details

---

#### Test Case 4.2: All Plans Request
**Prompt**: `all plans`

**Expected Response**:
- Comprehensive list of all insurance plans
- Detailed information for each plan
  - Basic Health Plan
  - Premium Health Plan
  - Family Health Plan
- Features and pricing
- Best suited for whom

**Pass Criteria**: ✅ Shows all plans with complete details

---

#### Test Case 4.3: Plan Comparison
**Prompt**: `compare insurance plans`

**Expected Response**:
- Side-by-side comparison of plans
- Key differences highlighted
- Recommendations based on needs

**Pass Criteria**: ✅ Helpful comparison information

---

### 5. Appointment Booking

#### Test Case 5.1: Book Appointment Request
**Prompt**: `I want to book an appointment`

**Expected Response**:
- Asks for symptoms or specialty preference
- Offers to find available doctors
- Guides through booking process

**Pass Criteria**: ✅ Clear guidance for booking

---

#### Test Case 5.2: Appointment with Specific Doctor
**Prompt**: `I want to book with Dr. Smith`

**Expected Response**:
- Confirms doctor name
- Asks for preferred date/time
- Shows available slots (if integrated)

**Pass Criteria**: ✅ Confirms doctor, asks for details

---

### 6. Affirmative & Negative Responses (CRITICAL)

#### Test Case 6.1: Yes After Insurance Query
**Setup**: Ask about insurance first
**Prompts**:
1. `tell me about insurance`
2. `yes`

**Expected Response for "yes"**:
- **SINGLE response** (not duplicates)
- Shows detailed insurance plans
- From database if available

**Pass Criteria**: ✅ SINGLE response, shows insurance details

---

#### Test Case 6.2: Yes After Doctor Query
**Setup**: Ask about doctors first
**Prompts**:
1. `I need a doctor`
2. `yes`

**Expected Response for "yes"**:
- **SINGLE response** (not duplicates)
- Shows available doctors from database
- Offers to book appointment

**Pass Criteria**: ✅ SINGLE response, shows doctors

---

#### Test Case 6.3: Generic Yes
**Prompt**: `yes` (without prior context)

**Expected Response**:
- **SINGLE response** (not duplicates)
- Helpful menu of options
- Asks what user needs help with

**Pass Criteria**: ✅ SINGLE response, helpful guidance

---

#### Test Case 6.4: Negative Response
**Prompt**: `no`

**Expected Response**:
- Acknowledges
- Asks what else they need help with

**Pass Criteria**: ✅ Single response, continues conversation

---

### 7. Specialized Healthcare Queries

#### Test Case 7.1: Lab Results
**Prompt**: `I want to see my lab results`

**Expected Response**:
- Offers to retrieve lab results
- Explains what results mean
- Guides on next steps

**Pass Criteria**: ✅ Helpful lab result information

---

#### Test Case 7.2: Billing Questions
**Prompt**: `I have a billing question`

**Expected Response**:
- Offers billing assistance
- Lists what it can help with (statements, charges, payment plans)
- Asks for specific billing question

**Pass Criteria**: ✅ Comprehensive billing help options

---

#### Test Case 7.3: Emergency
**Prompt**: `This is an emergency`

**Expected Response**:
- Immediate acknowledgment
- Directs to emergency services (911)
- Shows emergency contact numbers
- Offers urgent care options

**Pass Criteria**: ✅ Appropriate emergency handling

---

#### Test Case 7.4: Mental Health
**Prompt**: `I'm feeling anxious`

**Expected Response**:
- Empathetic response
- Offers mental health assessments
- Provides crisis hotline information
- Offers to find mental health professionals

**Pass Criteria**: ✅ Empathetic, provides resources

---

#### Test Case 7.5: Wellness & Lifestyle
**Prompt**: `I need diet recommendations`

**Expected Response**:
- Offers personalized diet recommendations
- Asks about dietary preferences/restrictions
- Provides wellness guidance

**Pass Criteria**: ✅ Helpful wellness information

---

### 8. RAG (Database) Verification

#### Test Case 8.1: Doctor Retrieval from Database
**Prompt**: `show me general physicians`

**Expected Behavior**:
- Retrieves doctors from PostgreSQL database
- Shows actual doctor data (if database populated)
- Falls back to helpful response if database empty

**Verify**:
- Check if response includes database data
- Verify doctor names, specialties, contact info

**Pass Criteria**: ✅ Attempts database retrieval, shows data or helpful fallback

---

#### Test Case 8.2: Insurance Plans from Database
**Prompt**: `show me all insurance plans`

**Expected Behavior**:
- Retrieves plans from database
- Shows actual plan data or defaults

**Pass Criteria**: ✅ Shows insurance plans

---

### 9. Multi-turn Conversations

#### Test Case 9.1: Complete Doctor Search Flow
**Conversation Flow**:
1. User: `Hello`
2. Bot: *Greets*
3. User: `I have a headache`
4. Bot: *Suggests doctor*
5. User: `yes`
6. Bot: *Shows doctors* ← Should be SINGLE response
7. User: `I want to book with the first doctor`
8. Bot: *Helps book appointment*

**Pass Criteria**: ✅ Smooth flow, single responses, context maintained

---

#### Test Case 9.2: Insurance Exploration Flow
**Conversation Flow**:
1. User: `I need insurance`
2. Bot: *Shows plans*
3. User: `tell me more about the premium plan`
4. Bot: *Details about premium plan*
5. User: `yes, I'm interested`
6. Bot: *Next steps for enrollment*

**Pass Criteria**: ✅ Context-aware, helpful responses

---

### 10. Edge Cases & Error Handling

#### Test Case 10.1: Gibberish Input
**Prompt**: `asdfghjkl`

**Expected Response**:
- Graceful handling
- Asks user to clarify
- Offers menu of options

**Pass Criteria**: ✅ No errors, helpful fallback

---

#### Test Case 10.2: Very Long Message
**Prompt**: `I have been suffering from fever, cold, cough, body pain, headache, and I'm not sure what kind of doctor I should see and I also want to know about insurance plans and how to book an appointment and what are the available time slots and can you help me with everything?`

**Expected Response**:
- Handles long message
- Addresses main concerns
- Doesn't crash or timeout

**Pass Criteria**: ✅ Comprehensive response, no errors

---

#### Test Case 10.3: Special Characters
**Prompt**: `Hello! How are you? I need help :)`

**Expected Response**:
- Handles special characters
- Normal helpful response

**Pass Criteria**: ✅ No errors, normal response

---

#### Test Case 10.4: Multiple Questions
**Prompt**: `What doctors do you have? What insurance plans? Where are you located?`

**Expected Response**:
- Addresses all questions or prioritizes
- Provides comprehensive answer

**Pass Criteria**: ✅ Handles multiple questions

---

## 🎯 Critical Tests (MUST PASS)

### Priority 1: No Duplicates
- [ ] Test "yes" returns **SINGLE response** (not 10)
- [ ] Test "all plans" returns **SINGLE response**
- [ ] Test "suggest doctors" returns **SINGLE response**

### Priority 2: Always Responds
- [ ] Bot responds to every message (never silent)
- [ ] No "Sorry, I couldn't process" errors
- [ ] Shows helpful fallback for unrecognized queries

### Priority 3: Database Integration
- [ ] Doctor searches retrieve from database
- [ ] Insurance plans show database data
- [ ] Responses reference specific database information

### Priority 4: Intelligent Responses
- [ ] Context-aware (remembers conversation)
- [ ] "Yes" understands what it refers to
- [ ] Uses AWS Bedrock for intelligent responses

---

## 📊 Test Results Template

Use this template to record results:

```
Test Date: __________
Tester Name: __________

| Test Case | Prompt | Response Count | Quality | Pass/Fail | Notes |
|-----------|--------|----------------|---------|-----------|-------|
| 1.1 | Hello | | | | |
| 1.2 | Good morning | | | | |
| 2.1 | I am suffering from viral | | | | |
| 2.2 | yes (after 2.1) | | | | |
| 3.1 | suggest me some doctors | | | | |
| 4.1 | I need help with insurance | | | | |
| 4.2 | all plans | | | | |
| 6.1 | yes (after insurance) | | | | |
| 6.2 | yes (after doctor query) | | | | |
| 7.3 | This is an emergency | | | | |

CRITICAL CHECKS:
- [ ] All "yes" responses return SINGLE message (not 10 duplicates)
- [ ] Bot responds to every query (never silent)
- [ ] Responses are relevant and helpful
- [ ] Database data is shown when available
```

---

## 🚀 Quick Test Commands (API Testing)

If you want to test the API directly (not through UI):

```bash
# Test 1: Hello
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "tester1", "message": "Hello"}'

# Test 2: Symptoms
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "tester1", "message": "I am suffering from viral"}'

# Test 3: Yes (CRITICAL)
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "tester1", "message": "yes"}'

# Test 4: All plans
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "tester1", "message": "all plans"}'

# Test 5: Suggest doctors
curl -X POST http://pran-chatbot-alb-738129713.us-east-1.elb.amazonaws.com:8080/rasa-webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "tester1", "message": "suggest me some doctors"}'
```

---

## 📝 Detailed Test Scenarios

### Scenario A: New Patient Journey

**Conversation Flow**:
```
User: Hello
Bot: [Greets and offers help]

User: I'm new here, what can you help me with?
Bot: [Lists all capabilities]

User: I need to find a doctor for my cold
Bot: [Recommends general physician]

User: yes
Bot: [Shows available general physicians] ← MUST BE SINGLE RESPONSE

User: I'll take the first one
Bot: [Helps book appointment]
```

**Expected**: Smooth flow, context maintained, single responses

---

### Scenario B: Insurance Shopping

**Conversation Flow**:
```
User: I need insurance
Bot: [Shows insurance recommendations]

User: tell me more about insurance plans
Bot: [Shows all plans with details]

User: all plans
Bot: [Shows comprehensive plan list] ← MUST BE SINGLE RESPONSE

User: what's the difference between basic and premium?
Bot: [Explains differences]

User: I'll go with premium
Bot: [Provides enrollment guidance]
```

**Expected**: Detailed information, helpful comparisons

---

### Scenario C: Specialist Search

**Conversation Flow**:
```
User: I need a cardiologist
Bot: [Shows cardiologists from database]

User: show me all cardiologists
Bot: [Extended list with details]

User: what are their ratings?
Bot: [Shows ratings if available]

User: book with the highest rated one
Bot: [Initiates booking process]
```

**Expected**: Database retrieval, detailed information

---

### Scenario D: Emergency Handling

**Conversation Flow**:
```
User: This is an emergency
Bot: [Immediate emergency response, 911 info]

User: I need urgent care
Bot: [Shows urgent care options, locations]
```

**Expected**: Immediate, appropriate emergency guidance

---

### Scenario E: Wellness & Lifestyle

**Conversation Flow**:
```
User: I want to improve my health
Bot: [Offers wellness guidance]

User: give me diet recommendations
Bot: [Provides diet advice]

User: what about exercise?
Bot: [Provides exercise recommendations]
```

**Expected**: Comprehensive wellness support

---

## 🔍 What to Look For

### ✅ PASS Indicators
- **Single responses** for all queries (especially "yes")
- Bot responds within 2-3 seconds
- Responses are relevant and helpful
- Database data shown when available (doctors, insurance plans)
- No error messages visible to user
- Context maintained across conversation
- Professional, empathetic tone

### ❌ FAIL Indicators
- Multiple duplicate responses (especially for "yes")
- "Sorry, I couldn't process your message" errors
- Bot doesn't respond (silent)
- Irrelevant responses
- Generic responses when database data should be shown
- Error messages or stack traces visible
- Long delays (>10 seconds)

---

## 🎯 Success Criteria

**Bot is production-ready if**:
- ✅ All "yes" responses are SINGLE (not 10 duplicates)
- ✅ Bot responds to 100% of queries
- ✅ Responses are relevant and helpful
- ✅ Database integration works (shows doctors, plans from database)
- ✅ Context is maintained across conversation
- ✅ Error handling is graceful
- ✅ Response time is acceptable (<5 seconds)

---

## 🐛 Known Issues to Watch For

1. **Duplicate Responses**: If you see 10 identical responses, report immediately
2. **Silent Bot**: If bot doesn't respond at all, check network/API
3. **Generic Responses**: If bot gives generic response when it should use database, report
4. **Context Loss**: If bot doesn't remember previous conversation, report

---

## 📞 Support

**Issues found?** Report with:
- Test case number
- Exact prompt used
- Expected vs actual response
- Screenshot if possible
- Timestamp of test

---

## 🎉 Final Notes

The bot has been enhanced with:
- ✅ RAG (Retrieval Augmented Generation) for database integration
- ✅ AWS Bedrock LLM for super intelligent responses
- ✅ Duplicate prevention at multiple levels
- ✅ Context-aware conversation handling
- ✅ Comprehensive healthcare capabilities

**Test URL**: https://main.d1fw711o7cx5w2.amplifyapp.com/

**Happy Testing!** 🚀

