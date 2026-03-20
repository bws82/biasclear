# BiasClear — Operations Checklist

**Last updated:** 2026-03-20

## Post-Deploy Verification

After every deploy to production, verify:

1. **Health endpoint responds:**
   ```bash
   curl -s https://biasclear.com/health | python3 -m json.tool
   ```
   Confirm: `llm_available: true`, `llm_status: "ready"` or `"no_requests_yet"` (if just started)

2. **Run a live full scan:**
   ```bash
   curl -s -X POST https://biasclear.com/scan \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_KEY" \
     -d '{"text":"Experts agree there is no reasonable alternative.","mode":"full","domain":"general"}'
   ```
   Confirm: `source: "llm+local"`, `degraded: false`

3. **Run the smoke check script:**
   ```bash
   scripts/smoke_check.sh
   ```

4. **Check Render logs** for the startup smoke check line:
   - Green: `LLM smoke check PASSED`
   - Red: `LLM smoke check FAILED` — investigate immediately

## Secret Handling

- **Never** put real API keys in chat messages, screenshots, or code comments
- **Never** commit `.env` files to git
- Store all secrets in Render's environment variable dashboard
- When sharing credentials, use the Render dashboard edit mode — never paste in chat
- If a key is compromised, rotate it immediately in both AWS IAM and Render

## Provider Truth Verification

If you suspect LLM drift or provider issues:

1. **Check health endpoint** — `llm_status` and `llm_canary` fields tell the truth
2. **Compare SHA-256 hashes** when debugging credential issues:
   ```bash
   # On the Render shell
   python3 -c "import os,hashlib; s=os.environ.get('AWS_SECRET_ACCESS_KEY',''); print('sha256='+hashlib.sha256(s.encode()).hexdigest())"
   ```
3. **Test AWS directly** on the Render shell:
   ```bash
   python3 -c "import boto3; c=boto3.client('sts',region_name='us-east-1'); print(c.get_caller_identity()['Account'])"
   ```
4. **Never change `BIASCLEAR_LLM_PROVIDER`** unless you have verified the new provider works first

## Credential Rotation Procedure

1. Generate new credentials in the provider's dashboard (AWS IAM, Google Cloud, etc.)
2. Update the environment variable in Render (edit mode, paste, save)
3. Click "Save, rebuild, and deploy" to pick up the new value
4. Verify the deploy goes live (green checkmark in Events)
5. Run the post-deploy verification steps above
6. Revoke the old credentials only after verifying the new ones work

## Incident Response

If `/health` shows `llm_available: false`:

1. Check `llm_status` for the specific failure mode (see PRODUCTION_DEPLOYMENT_SOURCE_OF_TRUTH.md for status values)
2. Check `llm_canary.consecutive_failures` — if > 0, the canary is also failing
3. Check Render logs for `InvalidSignatureException`, `circuit_open`, or credential errors
4. If credential issue: verify SHA-256 hash on the Render shell (see above)
5. If rate limiting: wait for rate limit window to expire, or switch to a less-loaded provider
6. If infrastructure issue: check [Render Status](https://status.render.com) and [AWS Health Dashboard](https://health.aws.amazon.com)
