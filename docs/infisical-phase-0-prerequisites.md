# Infisical Phase 0: AWS, R2, Bitwarden setup

One-time manual setup before deploying Infisical. Never commit or paste any
value from this guide into chat. Use one AWS region throughout (`us-west-2`
below) and check the region selector before each step.

## 1. AWS account (skip if you already have one!)

Sign in to the console as root. Make sure root has MFA (click your name,
**Security credentials**, **Assign MFA device**). Nothing else to set up.

## 2. Generate three values

```bash
openssl rand -hex 16       # ENCRYPTION_KEY
openssl rand -base64 32    # AUTH_SECRET
openssl rand -hex 24       # REDIS_PASSWORD
```

Paste each into Bitwarden right away (step 6). `ENCRYPTION_KEY` must never
change once Infisical has data. Losing it loses every secret.

## 3. SSM parameters

**Systems Manager**, **Parameter Store**, **Create parameter**, three times:

| Name | Value |
|---|---|
| `/homelab/infisical/ENCRYPTION_KEY` | generated value |
| `/homelab/infisical/AUTH_SECRET` | generated value |
| `/homelab/infisical/REDIS_PASSWORD` | generated value |

For each: tier **Standard**, type **SecureString**, default KMS key.

## 4. S3 bucket

**S3**, **Create bucket**:

- Name: `<you>-homelab-infisical-backups`
- Block all public access: on
- Versioning: enable

Then **Management**, **Create lifecycle rule** named `cleanup`, applied to all
objects (tick the warning acknowledgement). Tick only these actions:

- **Permanently delete noncurrent versions of objects**: 30 days.
- **Delete expired object delete markers or incomplete multipart uploads**, then
  only **Delete incomplete multipart uploads**: 7 days.

Leave the other three actions unticked. Never tick **Expire current versions**,
because it would delete the live backups.

## 5. IAM policy, user, key

**IAM**, **Policies**, **Create policy**, **JSON**. Replace `REGION`, `ACCOUNT`
and `BUCKET`. Name it `homelab-infisical-bootstrap`.

`ACCOUNT` is your 12-digit account ID, shown in the **AWS Account** panel on the
IAM dashboard (digits only, no dashes). If you cannot find it, use `*`.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"],
      "Resource": "arn:aws:ssm:REGION:ACCOUNT:parameter/homelab/infisical/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::BUCKET/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket", "s3:GetBucketLocation"],
      "Resource": "arn:aws:s3:::BUCKET"
    }
  ]
}
```

**IAM**, **Users**, **Create user** `homelab-infisical-bootstrap`:

- No console access.
- **Attach policies directly**, set the filter to **Customer managed**, and
  search for `homelab-infisical-bootstrap`. It only appears after you have
  created it above. Never attach AdministratorAccess to this user.
- Open the user, **Security credentials**, **Create access key**, use case
  **Application running outside AWS**.
- Copy both keys to Bitwarden. The secret is shown once.

## 6. Cloudflare R2

Sign in at <https://dash.cloudflare.com>. If you already use R2 for Velero, R2
is enabled; skip the payment prompt.

### 6a. Create the bucket

1. In the left sidebar open **R2 Object Storage** (under **Storage & databases**),
   then **Overview**.
2. Click **Create bucket**.
3. **Bucket name:** `homelab-infisical-backups`. **Location:** Automatic.
   **Default storage class:** Standard.
4. Click **Create bucket**.

If R2 asks to be enabled, add a payment method. Usage inside the free
allowance (10 GB) is not charged.

### 6b. Create the API token

1. On the R2 **Overview** page, find **API Tokens** (right side) and click
   **Manage**, or **Manage API Tokens**.
2. Click **Create Account API token**. A user token also works.
3. Fill in:
   - **Token name:** `homelab-infisical-backups`
   - **Permissions:** Object Read & Write
   - **Specify bucket(s):** Apply to specific buckets only, then choose
     `homelab-infisical-backups`
   - **TTL:** Forever
4. Click **Create API Token**.
5. The next page shows the credentials once. Copy these to Bitwarden:
   - **Access Key ID**
   - **Secret Access Key** (shown only this once)
   - The **S3 endpoint** URL, `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`

You do not need the **Token value** shown on that page.

Use a different token from Velero's, so revoking one never affects the other.

### 6c. Find the account ID

It is the hex string in the S3 endpoint URL above. It also appears on the R2
**Overview** page in the right sidebar under **Account Details**.

## 7. Bitwarden

Folder `homelab-infisical-bootstrap` with these items:

- AWS root login
- IAM access key and secret
- `ENCRYPTION_KEY`, `AUTH_SECRET`, `REDIS_PASSWORD`
- R2 token and account ID

Then check and clean up:

1. Lock and unlock Bitwarden, open the `ENCRYPTION_KEY` item and reveal it. It
   must be 32 hex characters.
2. In **Systems Manager**, **Parameter Store**, open
   `/homelab/infisical/ENCRYPTION_KEY` and click **Show** on the decrypted
   value. It must match Bitwarden exactly.
3. Close the terminal window you used for `openssl`, so the values are not left
   in its scrollback.

## Done when

- [ ] Three SecureString parameters under `/homelab/infisical/`
- [ ] S3 bucket with versioning and lifecycle rule
- [ ] IAM user with only the one policy and an access key
- [ ] R2 bucket and scoped token
- [ ] Everything in Bitwarden

Non-secret names Phase 1 needs: region, S3 bucket, R2 bucket, R2 account ID.
