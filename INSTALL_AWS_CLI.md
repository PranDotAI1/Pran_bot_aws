# Install AWS CLI - Quick Guide

To fix the backend, you need AWS CLI installed and configured.

---

## 🚀 **Quick Install (macOS)**

### **Option 1: Using Homebrew (Recommended - 2 minutes)**

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install AWS CLI
brew install awscli

# Verify installation
aws --version
```

### **Option 2: Using Official Installer (3 minutes)**

```bash
# Download installer
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"

# Install
sudo installer -pkg AWSCLIV2.pkg -target /

# Verify installation
aws --version
```

---

## 🔑 **Configure AWS Credentials**

After installing, configure your AWS credentials:

```bash
aws configure
```

You'll be prompted for:

```
AWS Access Key ID: [Enter your key]
AWS Secret Access Key: [Enter your secret]
Default region name: us-east-1
Default output format: json
```

### **Where to Get AWS Credentials:**

1. **AWS Console** → IAM → Users → Your User → Security Credentials
2. Click "Create access key"
3. Download the credentials
4. Use them in `aws configure`

---

## ✅ **Test Configuration**

```bash
# Test if AWS CLI works
aws sts get-caller-identity

# Expected output:
{
    "UserId": "...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::..."
}
```

---

## 🔧 **Then Run the Fix Script**

Once AWS CLI is installed and configured:

```bash
cd /Users/viditagarwal/Downloads/pran_chatbot-main
./fix_backend_now.sh
```

---

## ⏱️ **Total Time**

- Install AWS CLI: 2-3 minutes
- Configure credentials: 1 minute
- Run fix script: 3-5 minutes
- **Total: 6-9 minutes end-to-end**

---

## 🚨 **If You Don't Have AWS Access**

Contact your AWS admin and ask them to:
1. Give you IAM access to ECS
2. Provide you with Access Key ID and Secret Access Key
3. Or ask them to restart the service for you

Send them: `URGENT_FIX_BACKEND_DOWN.md`
