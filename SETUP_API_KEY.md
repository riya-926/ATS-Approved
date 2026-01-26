# Setting Up Your Anthropic API Key

## Step 1: Install Dependencies

First, install the required packages:

```bash
pip install -r requirements.txt
```

This will install:
- `anthropic` - Anthropic SDK for Claude API
- `python-dotenv` - For loading environment variables

## Step 2: Create .env File

Create a file named `.env` in the project root directory (same level as `requirements.txt`).

**Windows (PowerShell):**
```powershell
New-Item -Path .env -ItemType File
```

**Windows (Command Prompt):**
```cmd
type nul > .env
```

**Mac/Linux:**
```bash
touch .env
```

## Step 3: Add Your API Key

Open the `.env` file and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Important:**
- Replace `sk-ant-api03-...` with your actual API key from Anthropic
- Do NOT include quotes around the key
- Do NOT commit this file to git (it's already in .gitignore)

## Step 4: Get Your API Key

If you don't have your API key yet:

1. Go to https://console.anthropic.com/
2. Sign in or create an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (it starts with `sk-ant-api03-`)

## Step 5: Test It

Run the test script to verify everything works:

```bash
python scripts/test_rewrite.py path/to/resume.docx path/to/job_description.txt
```

If you see an error about the API key, double-check:
- The `.env` file is in the project root
- The key is correct (no extra spaces, quotes, etc.)
- You've installed dependencies: `pip install -r requirements.txt`

## Security Notes

✅ **DO:**
- Keep your `.env` file local (never commit to git)
- Use different API keys for development and production
- Rotate your keys periodically

❌ **DON'T:**
- Share your API key publicly
- Commit `.env` to version control
- Hard-code the API key in your code

The `.env` file is already in `.gitignore`, so it won't be committed to git.
