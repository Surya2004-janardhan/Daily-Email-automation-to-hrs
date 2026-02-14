# Testing Guide for LinkedIn Automation

## After Merging This PR

### Option 1: Manual Workflow Test
1. Go to GitHub Actions tab
2. Select "LinkedIn Outreach Automation" workflow
3. Click "Run workflow"
4. Set limit to 1 or 2 (for safety)
5. Monitor the run and check:
   - ✅ No more `no_connect_button` errors
   - ✅ Successful connections or specific failure reasons (e.g., `already_connected`, `pending`)

### Option 2: Local Test (Recommended for debugging)
```bash
cd inb
python linkedin_outreach.py \
  --cookie "YOUR_LINKEDIN_COOKIE" \
  --excel "linkedin-data.xlsx" \
  --limit 1 \
  --debug
```

**Debug mode will show:**
- All buttons found on the page
- Which selector method successfully found the Connect button
- Detailed error messages if any step fails

### Expected Behavior After Fix

✅ **Success Cases:**
- `sent` - Connection request with message sent successfully
- `already_connected` - Profile already connected
- `pending` - Connection request already pending

⚠️ **Acceptable Cases:**
- `follow_only` - Profile doesn't allow connection (only Follow)
- `session_expired` - Cookie needs refresh

❌ **Should Not Occur (Fixed):**
- `no_connect_button` - This was the main issue and should now be resolved

## Monitoring

### Check Workflow Logs
Look for patterns like:
```
[1/20] John Doe
  🏢 Company XYZ
  🔗 john-doe
  ✅ Message sent with connection request!
```

Instead of:
```
[1/20] John Doe
  🏢 Company XYZ
  🔗 john-doe
  ❌ Failed: no_connect_button
```

### Success Metrics
- **Before Fix**: 0/20 successful (100% `no_connect_button`)
- **After Fix Target**: >80% success rate (sent/already_connected/pending)

## Troubleshooting

### If Still Seeing `no_connect_button`:
1. Enable debug mode (`--debug` flag)
2. Check which buttons are found on the page
3. LinkedIn may have changed UI again - compare with debug output
4. Update selectors in `inb/linkedin_outreach.py` based on findings

### If Seeing `session_expired`:
1. Cookie `li_at` needs to be refreshed
2. Get new cookie from browser while logged into LinkedIn
3. Update GitHub secret `LINKEDIN_COOKIE`

### If Seeing Modal Errors:
1. Check modal selector updates
2. Verify "Add a note" button still exists in current LinkedIn UI
3. May need to adjust wait times or selectors

## Safety Notes

- Daily limit: 25 connection requests (hardcoded)
- Random delays: 5-12 seconds between attempts
- Quota tracking prevents exceeding daily limit
- Use `--limit` parameter to control batch size

## Rolling Back

If issues persist:
```bash
git revert HEAD~3  # Revert last 3 commits
```

Then investigate the specific LinkedIn UI changes needed.
