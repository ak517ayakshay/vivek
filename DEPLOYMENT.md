# 🚀 Deploying Ayush Herbal Software to Vercel

## Option 1: Vercel + External Database (Recommended)

### Step 1: Set up External Database

**Choose one of these options:**

#### A) PlanetScale (MySQL) - Free Tier
1. Go to [PlanetScale](https://planetscale.com)
2. Create a new database
3. Get your connection string
4. Add to Vercel environment variables

#### B) Supabase (PostgreSQL) - Free Tier
1. Go to [Supabase](https://supabase.com)
2. Create a new project
3. Get your connection string
4. Add to Vercel environment variables

#### C) Railway (PostgreSQL) - Free Tier
1. Go to [Railway](https://railway.app)
2. Create a new PostgreSQL database
3. Get your connection string
4. Add to Vercel environment variables

### Step 2: Update Database Connection

Replace the `get_conn()` function in `api/index.py` with your database connection:

```python
import psycopg2  # For PostgreSQL
# or
import pymysql   # For MySQL

def get_conn():
    # For Supabase/Railway (PostgreSQL)
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    conn.row_factory = psycopg2.Row
    return conn
    
    # OR for PlanetScale (MySQL)
    # conn = pymysql.connect(os.environ.get('DATABASE_URL'))
    # return conn
```

### Step 3: Deploy to Vercel

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   vercel
   ```

4. **Add Environment Variables:**
   - Go to Vercel Dashboard
   - Select your project
   - Go to Settings > Environment Variables
   - Add:
     - `DATABASE_URL`: Your database connection string
     - `SECRET_KEY`: A random secret key

## Option 2: Vercel + Vercel Postgres (Paid)

### Step 1: Create Vercel Postgres Database

1. Go to Vercel Dashboard
2. Create a new project
3. Add Vercel Postgres integration
4. Get your connection string

### Step 2: Update Requirements

Add to `requirements.txt`:
```
psycopg2-binary==2.9.7
```

### Step 3: Update Database Connection

```python
import psycopg2

def get_conn():
    conn = psycopg2.connect(os.environ.get('POSTGRES_URL'))
    return conn
```

## Option 3: Static Frontend + Serverless Backend

### Frontend (Vercel)
- Deploy static files to Vercel
- Use Vercel's static hosting

### Backend (Vercel Functions)
- Convert Flask routes to Vercel serverless functions
- Each route becomes a separate function

## 🎯 **Recommended Approach**

**Use Option 1 with Supabase** because:
- ✅ Free tier available
- ✅ Easy to set up
- ✅ Good performance
- ✅ Built-in dashboard
- ✅ Automatic backups

## 📋 **Deployment Checklist**

- [ ] Choose database provider
- [ ] Set up database
- [ ] Update connection code
- [ ] Add environment variables
- [ ] Test locally
- [ ] Deploy to Vercel
- [ ] Test production deployment
- [ ] Set up custom domain (optional)

## 🔧 **Environment Variables Needed**

```
DATABASE_URL=your_database_connection_string
SECRET_KEY=your_random_secret_key
FLASK_ENV=production
```

## 🚨 **Important Notes**

1. **SQLite won't work on Vercel** - you need a proper database
2. **File uploads** need special handling on Vercel
3. **Sessions** should use database or Redis
4. **Static files** should be in `public` folder
5. **Cold starts** may cause delays on free tier

## 🆓 **Free Tier Limits**

- **Vercel**: 100GB bandwidth, 1000 serverless function executions
- **Supabase**: 500MB database, 2GB bandwidth
- **PlanetScale**: 1 billion reads, 10 million writes
- **Railway**: $5 credit monthly

## 🎉 **After Deployment**

Your Ayush Herbal Software will be available at:
`https://your-project-name.vercel.app`

## 🆘 **Troubleshooting**

### Common Issues:
1. **Database connection errors** - Check connection string
2. **Import errors** - Add missing packages to requirements.txt
3. **Template not found** - Check file paths
4. **Environment variables** - Make sure they're set in Vercel dashboard

### Debug Steps:
1. Check Vercel function logs
2. Test database connection locally
3. Verify environment variables
4. Check function timeout settings
