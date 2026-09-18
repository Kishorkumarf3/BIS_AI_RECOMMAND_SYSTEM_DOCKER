"""
Script to automatically create and deploy the FastAPI backend Docker container to Hugging Face Spaces.

Usage:
    python deploy_to_hf.py <HF_WRITE_TOKEN>
    OR
    $env:HF_TOKEN="hf_xxx"; python deploy_to_hf.py
"""

import os
import sys
from pathlib import Path

# Fix Unicode printing issues on Windows terminals
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from huggingface_hub import HfApi, login
except ImportError:
    print("Error: huggingface_hub package is required. Run 'pip install huggingface_hub'")
    sys.exit(1)


def main():
    token = os.getenv("HF_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1].strip()

    if not token:
        print("=" * 60)
        print("Hugging Face Space Deployment Tool")
        print("=" * 60)
        print("Please provide a Hugging Face Write Token.")
        print("Get your token at: https://huggingface.co/settings/tokens (Role: Write)")
        print("\nUsage:")
        print("    python deploy_to_hf.py <YOUR_HF_WRITE_TOKEN>")
        print("=" * 60)
        token = input("\nEnter HF Write Token: ").strip()

    if not token:
        print("❌ Error: Hugging Face Token is required to deploy.")
        sys.exit(1)

    print("\nAuthenticating with Hugging Face...")
    try:
        login(token=token)
        api = HfApi(token=token)
        user_info = api.whoami()
        username = user_info["name"]
        print(f"✅ Successfully authenticated as user: '{username}'")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)

    space_name = "bis-recommendation-backend"
    repo_id = f"{username}/{space_name}"

    print(f"\nCreating/Verifying Docker Space '{repo_id}' on Hugging Face...")
    try:
        api.create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="docker",
            private=False,
            exist_ok=True,
        )
        print(f"✅ Space '{repo_id}' is ready.")
    except Exception as e:
        print(f"⚠️ Notice when creating repo via API: {e}")
        print("\n👉 Note for Hugging Face Free Tier:")
        print(f"Please create the Space once manually on the web:")
        print(f"1. Go to: https://huggingface.co/new-space")
        print(f"2. Space name: {space_name}")
        print(f"3. Space SDK: Docker -> Blank")
        print(f"4. Click 'Create Space'")
        print("Then run this script again to upload your backend files!")

    backend_dir = Path(__file__).resolve().parent

    print(f"\nUploading backend files from '{backend_dir}' to Space '{repo_id}'...")
    try:
        api.upload_folder(
            folder_path=str(backend_dir),
            repo_id=repo_id,
            repo_type="space",
            ignore_patterns=[
                "venv/**",
                "__pycache__/**",
                "*.pyc",
                ".git/**",
                ".env",
                "deploy_to_hf.py",
            ],
        )
        print("✅ Files uploaded successfully.")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        sys.exit(1)

    space_url = f"https://{username}-{space_name.lower()}.hf.space"
    space_page = f"https://huggingface.co/spaces/{repo_id}"

    print("\n" + "=" * 60)
    print("🚀 DEPLOYMENT INITIATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📌 Space Management Page: {space_page}")
    print(f"🌐 Public API Base URL:  {space_url}")
    print(f"💓 Health Check Endpoint: {space_url}/api/v1/health")
    print(f"📚 Swagger Documentation: {space_url}/docs")
    print("=" * 60)
    print("\nNext Steps for Vercel Integration:")
    print("1. Go to Vercel -> Project Settings -> Environment Variables.")
    print("2. Add/Update: VITE_API_BASE")
    print(f"   Value: {space_url}")
    print("3. Redeploy your frontend on Vercel.")
    print("=" * 60)


if __name__ == "__main__":
    main()
