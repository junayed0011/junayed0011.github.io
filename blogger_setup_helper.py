import os
import sys
import json
import urllib.parse
import http.server
import socketserver
import threading
import webbrowser
import requests

# Shared state to capture the code from the local server
oauth_code = None
server_port = 8080
redirect_uri = f"http://localhost:{server_port}/"

class OAuthRedirectHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global oauth_code
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if "code" in params:
            oauth_code = params["code"][0]
            html_response = """
            <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body {
                        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                        background-color: #0A0B0E;
                        color: #FAF9F6;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .card {
                        background: #12141C;
                        padding: 40px;
                        border-radius: 12px;
                        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
                        text-align: center;
                        max-width: 450px;
                        border: 1px solid #1E2235;
                    }
                    h1 { color: #FF3366; margin-top: 0; font-size: 24px; }
                    p { color: #9EA2B6; line-height: 1.6; font-size: 15px; }
                    .badge {
                        background: rgba(16, 185, 129, 0.1);
                        color: #10B981;
                        padding: 6px 12px;
                        border-radius: 20px;
                        font-weight: 600;
                        font-size: 13px;
                        display: inline-block;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="card">
                    <span class="badge">Success</span>
                    <h1>Authorization Successful!</h1>
                    <p>Google Blogger has been successfully authorized. You can now close this browser tab and return to your terminal to retrieve your credentials.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html_response.encode("utf-8"))
        else:
            self.wfile.write(b"No authorization code detected. Please try again.")

    def log_message(self, format, *args):
        # Suppress standard logging to keep terminal output clean
        return

def run_local_server():
    """Runs a local server to handle OAuth redirect response."""
    handler = OAuthRedirectHandler
    with socketserver.TCPServer(("", server_port), handler) as httpd:
        # Serve one request and shutdown
        httpd.handle_request()

def main():
    print("=" * 70)
    print("           GOOGLE BLOGGER OAUTH2 DYNAMIC CREDENTIALS SETUP")
    print("=" * 70)
    print("This utility helps you obtain your Blogger BLOG ID and OAuth REFRESH TOKEN")
    print("for seamless deployment inside GitHub Actions or local automated scripts.")
    print("-" * 70)
    
    print("\n[STEP 1] Google Developer Console Setup")
    print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
    print("2. Enable the 'Blogger API v3' for your project.")
    print("3. Navigate to APIs & Services > Credentials.")
    print("4. Click '+ Create Credentials' > 'OAuth client ID'.")
    print("5. Select Application type: 'Web application'.")
    print("6. In 'Authorized redirect URIs', add exactly:")
    print(f"   {redirect_uri}")
    print("7. Click Create and save your Client ID and Client Secret.")
    
    print("\n" + "-" * 70)
    
    client_id = input("\nEnter your OAuth Client ID: ").strip()
    client_secret = input("Enter your OAuth Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("[ERROR] Client ID and Client Secret are required. Aborting.")
        sys.exit(1)
        
    # Generate Google OAuth Auth URL
    auth_params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/blogger",
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(auth_params)
    
    print("\n" + "-" * 70)
    print("[STEP 2] Launching Authorization Flow")
    print("Starting local receiver server on port 8080...")
    
    # Start the redirect server in a background thread
    server_thread = threading.Thread(target=run_local_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("\nOpening your default web browser to authorize the Blogger API...")
    print("If it does not open automatically, please copy and paste this URL into your browser:")
    print(f"\n{auth_url}\n")
    
    webbrowser.open(auth_url)
    
    print("Waiting for authorization code from browser redirect...")
    server_thread.join(timeout=60) # Wait up to 60 seconds
    
    global oauth_code
    if not oauth_code:
        print("\n[ERROR] Authorization timeout or failed (no code received). Please try again.")
        sys.exit(1)
        
    print("\n[STEP 3] Exchanging Auth Code for Refresh Token...")
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": oauth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        if response.status_code != 200:
            print(f"[ERROR] Token exchange failed: {response.text}")
            sys.exit(1)
            
        tokens = response.json()
        refresh_token = tokens.get("refresh_token")
        access_token = tokens.get("access_token")
        
        if not refresh_token:
            print("\n[WARNING] No refresh token returned! If you previously authorized this application,")
            print("Google only issues a refresh token the first time you consent unless you revoke access first.")
            print("To resolve, go to your Google account security settings, remove your app's access, and re-run this script.")
            
        print("\n" + "=" * 70)
        print("                         YOUR SECURE OAUTH TOKENS")
        print("=" * 70)
        print(f"BLOGGER_REFRESH_TOKEN:\n{refresh_token}\n")
        print("-" * 70)
        
        # Now let's fetch the blogs they own to retrieve the Blog ID!
        print("[STEP 4] Querying Google Blogger API to locate Blog IDs...")
        blogs_url = "https://www.googleapis.com/blogger/v3/users/self/blogs"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        blogs_response = requests.get(blogs_url, headers=headers)
        if blogs_response.status_code == 200:
            blogs_data = blogs_response.json()
            items = blogs_data.get("items", [])
            if items:
                print("\nBlogs associated with this account:")
                for blog in items:
                    print(f"\n  - Blog Name: {blog.get('name')}")
                    print(f"    BLOGGER_BLOG_ID: {blog.get('id')}")
                    print(f"    URL: {blog.get('url')}")
            else:
                print("\n[WARNING] No active Blogger blogs found in this account.")
        else:
            print(f"\n[WARNING] Failed to query active Blogger blogs list: {blogs_response.text}")
            
        print("\n" + "=" * 70)
        print("                  WHAT TO DO WITH THESE CREDENTIALS")
        print("=" * 70)
        print("Add the following as repository secrets in your GitHub repository:")
        print("1. Go to Settings > Secrets and variables > Actions > New repository secret.")
        print(f"2. Add 'BLOGGER_CLIENT_ID' -> (Value: {client_id})")
        print(f"3. Add 'BLOGGER_CLIENT_SECRET' -> (Value: {client_secret})")
        print(f"4. Add 'BLOGGER_REFRESH_TOKEN' -> (Value: {refresh_token})")
        if items:
            print(f"5. Add 'BLOGGER_BLOG_ID' -> (Value: {items[0].get('id')})")
        else:
            print("5. Add 'BLOGGER_BLOG_ID' -> (Your Blogger Blog ID)")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
