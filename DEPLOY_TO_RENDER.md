# 🚀 Deploy to Render

## Prerequisites
- GitHub account
- Render account (free)
- This code pushed to GitHub

## Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "GitHub Guardrails - Competition Entry"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2. Deploy on Render
1. Go to https://render.com
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Select the `render.yaml` file
5. Add environment variables:
   - `GEMINI_API_KEY`: AIzaSyCWDopZRqZbXT-pkQLFvJhrOWJSssUlTf4
   - `GITHUB_APP_ID`: (from GitHub App)
   - `GITHUB_WEBHOOK_SECRET`: (from GitHub App)
   - `GITHUB_PRIVATE_KEY`: (paste private key)
6. Click "Apply"

Render will:
- Create backend service
- Create GitHub app service
- Create PostgreSQL database
- Create Redis instance
- Link everything automatically

### 3. Get URLs
After deployment (5-10 minutes):
- Backend: https://guardrails-backend.onrender.com
- GitHub App: https://guardrails-app.onrender.com

### 4. Update GitHub App
In your GitHub App settings:
- Webhook URL: https://guardrails-app.onrender.com/api/github/webhooks
- Webhook secret: (same as GITHUB_WEBHOOK_SECRET)

### 5. Test
Create a PR with `examples/vulnerable-test.py`

Bot should comment within 30 seconds!

---

## Troubleshooting

### Services won't start
- Check environment variables are set
- Check logs in Render dashboard
- Verify database is ready

### Backend 500 errors
- Check GEMINI_API_KEY is set
- Check logs: `render logs guardrails-backend`

### GitHub App not responding
- Check BACKEND_URL points to backend service
- Check webhook URL is correct
- Check private key is set correctly

---

**That's it! Your solution is live!** 🎉
