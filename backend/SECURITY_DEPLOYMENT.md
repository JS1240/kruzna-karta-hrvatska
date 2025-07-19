# Security Deployment Guide - Encryption Key Migration

## 🚨 Critical Security Update

**URGENT**: The encryption key was previously stored in version control and has been compromised. This guide provides instructions for secure key deployment.

## 📋 Deployment Steps

### 1. Set Environment Variable

**For Production/Staging environments:**

```bash
# Set the new encryption key as an environment variable
export ENCRYPTION_KEY="YROvcHe0SkdBLp4L7wpp9Ym0hVQx0ewp-_1dE6ro_jI="

# For Docker deployments, add to your docker-compose.yml:
environment:
  - ENCRYPTION_KEY=YROvcHe0SkdBLp4L7wpp9Ym0hVQx0ewp-_1dE6ro_jI=

# For Kubernetes deployments, create a secret:
kubectl create secret generic app-secrets --from-literal=ENCRYPTION_KEY=YROvcHe0SkdBLp4L7wpp9Ym0hVQx0ewp-_1dE6ro_jI=
```

### 2. Update Environment Files

**For Development (.env files):**

```bash
# Add to backend/.env (not committed to git)
ENCRYPTION_KEY=YROvcHe0SkdBLp4L7wpp9Ym0hVQx0ewp-_1dE6ro_jI=
```

### 3. Verify Deployment

After setting the environment variable, the application will:
- Log: "Using encryption key from ENCRYPTION_KEY environment variable"
- No longer display security warnings about file-based keys

### 4. Data Migration (If Needed)

**IMPORTANT**: If you have existing encrypted data using the old key, you'll need to:

1. Backup your database before deployment
2. Decrypt existing data with the old key
3. Re-encrypt with the new key after deployment

**Migration script example:**
```python
# Run this BEFORE deploying the new key
from app.core.security import SecurityHardening

# Initialize with old key (from file)
old_security = SecurityHardening()
# Decrypt all sensitive data and store temporarily

# After deployment with new key:
new_security = SecurityHardening()
# Re-encrypt all data with new key
```

## 🔐 Security Best Practices

### Environment Variable Management

1. **Never log the encryption key value**
2. **Use secure secret management services:**
   - AWS Secrets Manager
   - Azure Key Vault  
   - Google Secret Manager
   - HashiCorp Vault

3. **Rotate keys regularly** (recommended: quarterly)

### Key Rotation Process

```bash
# Generate new key
python3 -c "import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"

# Update environment variable
export ENCRYPTION_KEY="<new_key>"

# Restart application
```

## 🚦 Fallback Behavior

The application has multiple fallback mechanisms:

1. **Primary**: `ENCRYPTION_KEY` environment variable ✅ (Secure)
2. **Fallback**: File-based key with security warning ⚠️ (Legacy)
3. **Emergency**: Generated temporary key ❌ (Development only)

## 📞 Emergency Contacts

If you encounter issues during deployment:
1. Check application logs for encryption key loading messages
2. Verify environment variable is properly set
3. Ensure key format is valid Base64

## ✅ Post-Deployment Checklist

- [ ] Environment variable `ENCRYPTION_KEY` is set
- [ ] Application logs show "Using encryption key from ENCRYPTION_KEY environment variable"
- [ ] No security warnings about file-based keys
- [ ] All encrypted data functions correctly
- [ ] Old `encryption.key` file removed from all servers
- [ ] Key value is stored securely (not in logs/configs)

---

**Generated**: $(date)  
**Key Rotation Required**: Every 90 days  
**Next Rotation Due**: $(date -d '+90 days')