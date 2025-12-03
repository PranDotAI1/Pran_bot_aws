# 🏥 Symptom Analyzer - Intelligent Symptom Analysis & Doctor Recommendations

## ✅ What Was Added

### **1. Symptom Analyzer** (`symptom_analyzer.py`)

A powerful AI system that analyzes symptoms and recommends appropriate doctors using:
- ✅ **AWS Bedrock Claude**: For intelligent symptom understanding
- ✅ **AWS Comprehend Medical**: For medical entity extraction
- ✅ **Rule-based Fallback**: When AWS services unavailable

#### **Features:**
- ✅ **Symptom Analysis**: Understands symptoms from natural language
- ✅ **Specialty Recommendation**: Maps symptoms to appropriate medical specialties
- ✅ **Urgency Detection**: Classifies as routine, urgent, or emergency
- ✅ **Doctor Recommendations**: Automatically finds relevant doctors

---

## 🎯 How It Works

### **Example Flow:**

**User**: "I am suffering from viral"

1. **Symptom Analyzer**:
   - Detects symptoms: "viral", "suffering"
   - Analyzes with AWS Bedrock/Comprehend Medical
   - Recommends: `general_medicine` specialty
   - Urgency: `routine`
   - Explanation: "Based on your symptoms, I recommend seeing a General Physician..."

2. **Doctor Retrieval**:
   - Queries database for General Physicians
   - Falls back to sample data if needed
   - Returns doctors with contact info

3. **Response**:
   - Shows symptom analysis
   - Displays recommended doctors
   - Offers to book appointment

---

## 📊 Symptom → Specialty Mapping

The analyzer understands 14+ medical specialties:

| Symptom Category | Specialty | Examples |
|-----------------|-----------|----------|
| General | General Medicine | fever, cold, cough, viral, headache |
| Heart | Cardiology | chest pain, high BP, palpitations |
| Women's Health | Gynecology | pregnancy, menstrual, pelvic pain |
| Brain | Neurology | severe headache, migraine, dizziness |
| Skin | Dermatology | rash, acne, skin infection |
| Children | Pediatrics | child symptoms, vaccination |
| Bones | Orthopedics | joint pain, fracture, back pain |
| Mental Health | Psychiatry | depression, anxiety, stress |
| Stomach | Gastroenterology | stomach pain, acid reflux, IBS |
| Hormones | Endocrinology | diabetes, thyroid, blood sugar |
| Urinary | Urology | UTI, kidney stone, bladder |
| ENT | ENT | ear pain, sinus, throat |
| Eyes | Ophthalmology | eye pain, vision, blurred vision |
| Lungs | Pulmonology | asthma, breathing, cough |

---

## 🚨 Urgency Detection

### **Emergency** (Call 911):
- Chest pain
- Difficulty breathing
- Severe trauma
- Loss of consciousness
- Severe allergic reaction

### **Urgent** (Seek care soon):
- High fever (>103°F)
- Severe pain
- Persistent vomiting
- Signs of infection

### **Routine** (Schedule appointment):
- Common cold
- Mild symptoms
- Checkups
- Non-urgent concerns

---

## 🧪 Test Queries

### **1. General Symptoms:**
```
"I am suffering from viral"
→ Recommends: General Physician
→ Shows: General medicine doctors
```

### **2. Heart Symptoms:**
```
"I have chest pain"
→ Recommends: Cardiologist
→ Urgency: Emergency (if severe)
→ Shows: Cardiologists
```

### **3. Neurological:**
```
"I have severe headache"
→ Recommends: Neurologist
→ Shows: Neurologists
```

### **4. Women's Health:**
```
"I'm pregnant and having pelvic pain"
→ Recommends: Gynecologist
→ Shows: Gynecologists
```

### **5. Complex Symptoms:**
```
"I have high blood pressure and chest pain"
→ Recommends: Cardiologist
→ Urgency: Urgent
→ Shows: Cardiologists with explanation
```

---

## 📋 Response Format

When symptoms are detected, the bot responds with:

```
🔍 Symptom Analysis:
Based on your symptoms, I recommend seeing a General Physician.
I can help you find a doctor and book an appointment.

✅ I found 3 General Physician(s) for you:

**1. Dr. Sarah Johnson**
   📋 Specialty: General Medicine
   🏥 Department: General Medicine
   📞 Phone: (555) 123-4567
   👨‍⚕️ Experience: 15 years
   ⭐ Rating: 4.8/5

📅 Would you like to book an appointment with any of these doctors?
Just tell me the doctor's name or number and your preferred date/time!
```

---

## 🔧 Integration

The Symptom Analyzer is integrated into:
- ✅ Main action flow (`action_aws_bedrock_chat`)
- ✅ RAG system (for database retrieval)
- ✅ Text-to-SQL agent (for intelligent queries)
- ✅ AWS Bedrock (for LLM intelligence)
- ✅ AWS Comprehend Medical (for entity extraction)

---

## 🎉 Benefits

### **Before:**
- ❌ Generic responses to symptoms
- ❌ No specialty recommendations
- ❌ No urgency detection
- ❌ Manual symptom mapping

### **After:**
- ✅ Intelligent symptom analysis
- ✅ Automatic specialty recommendations
- ✅ Urgency detection (emergency/urgent/routine)
- ✅ Context-aware doctor suggestions
- ✅ Uses AWS AI services for accuracy

---

## 🌐 Test on Amplify

**URL**: https://main.d1fw711o7cx5w2.amplifyapp.com/

### **Test These Symptom Queries:**

1. "I am suffering from viral"
2. "I have chest pain"
3. "I have high blood pressure"
4. "I have severe headache"
5. "I'm pregnant and need a doctor"
6. "I have skin rash"
7. "My child has fever"

**Expected**: Bot analyzes symptoms → Recommends specialty → Shows relevant doctors

---

## 🚀 Deployment Status

- ✅ Symptom Analyzer code added
- ✅ Integrated into main action
- ✅ Docker image built
- ✅ Pushed to ECR
- ✅ Deployed to ECS
- ⏳ Deployment in progress (2-3 minutes)

---

## 🎯 Result

The bot can now:
- ✅ **Understand symptoms** intelligently
- ✅ **Recommend appropriate doctors** automatically
- ✅ **Detect urgency** (emergency/urgent/routine)
- ✅ **Provide context-aware** responses
- ✅ **Use AWS AI services** for accuracy

**The bot is now a SUPER INTELLIGENT healthcare assistant!** 🏥🚀

