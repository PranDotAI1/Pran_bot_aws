# ⚡ Quick Test Prompts for Pran.AI Chatbot

**Test URL**: https://main.d1fw711o7cx5w2.amplifyapp.com/

## 🚀 Quick Tests (5 minutes)

Just copy and paste these prompts in order:

### 1. Basic Flow
```
Hello
```
**Expected**: Greeting from Dr. AI ✅

---

```
I am suffering from viral
```
**Expected**: Suggests finding a doctor ✅

---

```
yes
```
**Expected**: Shows doctors list (SINGLE response, not 10!) ✅

---

### 2. Doctor Search
```
suggest me some doctors
```
**Expected**: List of doctors from database ✅

---

```
I need a gynecologist
```
**Expected**: Shows gynecologists ✅

---

### 3. Insurance
```
all plans
```
**Expected**: Shows all insurance plans (SINGLE response!) ✅

---

```
tell me about insurance
```
**Expected**: Insurance recommendations ✅

---

### 4. Appointments
```
I want to book an appointment
```
**Expected**: Asks for details, shows doctors ✅

---

### 5. Wellness
```
I need diet recommendations
```
**Expected**: Wellness guidance ✅

---

### 6. Emergency
```
This is an emergency
```
**Expected**: Emergency guidance, 911 info ✅

---

## ✅ Pass Criteria

- [ ] All responses are **SINGLE** (no duplicates)
- [ ] Bot responds to every message
- [ ] Responses are relevant
- [ ] "yes" returns single response
- [ ] Shows doctors from database
- [ ] Shows insurance plans

## 🎯 Critical Test

**Most Important**: Test "yes" after any question

```
I need help with insurance
```
Then:
```
yes
```

**MUST BE**: Single response (not 10 duplicates) ✅

---

## 📊 Expected vs Before

**Before Fix**:
- "yes" → 10 duplicate responses ❌
- Bot stopped responding ❌
- Generic responses only ❌

**After Fix**:
- "yes" → 1 single response ✅
- Bot always responds ✅
- Uses database intelligently ✅

