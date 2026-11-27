# Cloud prerequisites: AWS, R2, Bitwarden

Manual setup in the cloud consoles, before you bootstrap the cluster. Never commit or paste any
value from this guide into chat. Use one AWS region throughout (`us-east-2`
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

Paste each into Bitwarden right away (step 8). `ENCRYPTION_KEY` must never
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

- Name: any globally unique name. The current one is `backup.bucket` in
  `k8s/bootstrap/charts/infisical/values.yaml`. If you pick a different name,
  update that value.
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

### 6d. Application database backups

Some app databases (the ones whose chart has a `ScheduledBackup`, see
[What is backed up](../recover/02-what-is-backed-up.md)) back up to their own R2
bucket, separate from Velero's and Infisical's.

1. In **R2 Object Storage**, **Overview**, click **Create bucket**. Set **Bucket
   name** to `homelab-db-backups`, **Location** Automatic, **Default storage
   class** Standard, and click **Create bucket**.
2. On the R2 **Overview** page click **Manage** next to **API Tokens**, then
   **Create Account API token**. Set **Token name** to `homelab-db-backups`,
   **Permissions** to Object Read & Write, **Specify bucket(s)** to Apply to
   specific buckets only with `homelab-db-backups`, and **TTL** Forever. Click
   **Create API Token**.
3. Copy the **Access Key ID** and the **Secret Access Key** (shown once) into
   Bitwarden, item `Cloudflare R2 homelab-db-backups` (step 8).
4. Add them to Infisical, once for each app that backs up to this bucket. Open
   <https://infisical.mdeleon.dev>, the project of the app's stack, **Secrets**,
   the `prod` environment, and the folder named after the app. Add two secrets:
   `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY`. Do this before the pull request
   that enables the backup is merged, or the database cannot archive its logs.

## 7. Cloudflare DNS token

cert-manager uses this token to prove domain ownership to Let's Encrypt. It is
separate from the R2 tokens above.

1. In <https://dash.cloudflare.com>, click your profile icon (top right), then
   **My Profile**, then **API Tokens**.
2. Click **Create Token**. Next to the **Edit zone DNS** template, click **Use
   template**.
3. Under **Zone Resources**, set **Include**, **Specific zone**, and choose
   `mdeleon.dev`.
4. Click **Continue to summary**, then **Create Token**.
5. Copy the token shown. It appears once. Save it in Bitwarden now (step 8).

## 8. Bitwarden

Everything a rebuild needs must be in Bitwarden before you start, so that a
person who has never touched this cluster can find it. Create a folder named
`homelab-infisical-bootstrap` and add these items. Use these exact names.

| Item name | Fields to store | Created in |
|---|---|---|
| `AWS root login` | email, password | step 1 |
| `AWS IAM homelab-infisical-bootstrap` | access key ID, secret access key | step 5 |
| `Infisical ENCRYPTION_KEY` | the 32-character value | step 2 |
| `Infisical AUTH_SECRET` | the value | step 2 |
| `Infisical REDIS_PASSWORD` | the value | step 2 |
| `Cloudflare R2 homelab-infisical-backups` | access key ID, secret access key, S3 endpoint URL, account ID | step 6 |
| `Cloudflare R2 homelab-db-backups` | access key ID, secret access key | step 6d |
| `Cloudflare DNS API token (cert-manager)` | the token | step 7 |
| `Node sudo password` | the sudo password of the user `mdeleon` on the nodes | you know it |
| `Infisical admin` | email, password | [Set up Infisical](../build/02-infisical-setup.md) |
| `Infisical dr-admin` | client ID, client secret | [Set up Infisical](../build/02-infisical-setup.md) |

If your vault uses other names, rename the items to match this table. The
recovery guide refers to them by these names.

Then check and clean up:

1. Lock and unlock Bitwarden, open the `Infisical ENCRYPTION_KEY` item and reveal
   it. It must be 32 hex characters.
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
- [ ] Cloudflare DNS token
- [ ] Every item in the table above is in Bitwarden (the last two are added
      later, in Infisical setup)

Keep these non-secret names for the bootstrap: region, S3 bucket, R2 bucket,
R2 account ID.

Next: [Install the cluster](../build/01-cluster-install.md).
