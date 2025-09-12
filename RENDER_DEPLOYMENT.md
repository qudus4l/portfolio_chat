# Render Deployment Guide

This guide will help you deploy your Qudus Portfolio Chatbot to Render.

## Prerequisites

- GitHub account with your code pushed
- OpenAI API key
- Render account (free at render.com)

## Step 1: Prepare Your Repository

Make sure your repository has these files (already created):
- `render.yaml` - Render configuration
- `build.sh` - Build script for deployment
- `requirements.txt` - Python dependencies
- `main.py` - Your FastAPI application

## Step 2: Deploy to Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account

2. **Connect Repository**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your `qudus-portfolio-chat` repository

3. **Configure Service**
   - **Name**: `qudus-portfolio-chat`
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`

4. **Set Environment Variables**
   - Click "Environment" tab
   - Add these variables:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     PORTFOLIO_DOMAIN=https://www.qudus4l.tech
     ```
   
   **Note**: The API automatically supports both HTTP and HTTPS versions of your domain, so CORS should work regardless of the protocol.

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes first time)

## Step 3: Configure Custom Domain (Optional)

1. **In Render Dashboard**:
   - Go to your service
   - Click "Settings" → "Custom Domains"
   - Add your domain (e.g., `api.qudus4l.tech`)

2. **Update DNS**:
   - Add CNAME record in your domain provider:
     ```
     api.qudus4l.tech → your-app-name.onrender.com
     ```

3. **Update CORS**:
   - Update `PORTFOLIO_DOMAIN` environment variable to your new domain
   - Redeploy if needed

## Step 4: Test Your Deployment

1. **Health Check**:
   ```bash
   curl https://your-app-name.onrender.com/
   ```

2. **Chat Endpoint**:
   ```bash
   curl -X POST https://your-app-name.onrender.com/api/chat \
     -H "Content-Type: application/json" \
     -d '{"query": "What are Qudus skills?"}'
   ```

## Step 5: Update Your Frontend

Update your portfolio website to use the new API URL:
```javascript
// Replace Railway URL with Render URL
const API_URL = 'https://your-app-name.onrender.com/api/chat';
```

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify `build.sh` has execute permissions

### App Crashes
- Check application logs
- Verify environment variables are set
- Check OpenAI API key is valid

### CORS Issues
- Verify `PORTFOLIO_DOMAIN` matches your frontend domain
- Check both HTTP and HTTPS versions are allowed

## Free Tier Limitations

- **Sleep after 15 minutes** of inactivity
- **750 hours/month** (enough for personal use)
- **Cold starts** - first request after sleep takes ~30 seconds

## Monitoring

- **Logs**: Available in Render dashboard
- **Metrics**: Basic metrics provided
- **Alerts**: Email notifications for failures

## Next Steps

1. Monitor your app for the first few days
2. Consider upgrading to paid plan for production use
3. Set up monitoring and alerts
4. Optimize for cold start performance if needed

## Support

- [Render Documentation](https://render.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GitHub Issues](https://github.com/qudus4l/qudus-portfolio-chat/issues)
