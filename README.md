# gmail_sorter
This can be used by ceo's to sort their gmail, it utilizes the gpt API and the gamil api in order to do this. 

## Environment setup

Use the template to store your API credentials locally:

1. Copy `.env.example` to `.env` (if needed).
2. Replace placeholder values in `.env` with your real keys.

Required variables:

- `OPENAI_API_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_TOKEN_PATH`

Optional variable:

- `GOOGLE_PROJECT_ID`

## Test Gmail API access

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Gmail access test:

```bash
python -m unittest test_gmail_api_access.py -v
```

Notes:

- The first run may open a browser for Google OAuth consent.
- The token file is written to `GOOGLE_TOKEN_PATH` after successful auth.
- Use a token path like `token.json` instead of your client credentials file.

If you get `Error 400: redirect_uri_mismatch`:

1. Use `GOOGLE_REDIRECT_URI=http://localhost:8080/` in `.env`.
2. In Google Cloud Console -> APIs & Services -> Credentials -> your OAuth client, add `http://localhost:8080/` to Authorized redirect URIs.
3. Prefer OAuth client type `Desktop app` for local scripts.
4. Confirm Gmail API is enabled in your project and your OAuth consent screen is configured.
