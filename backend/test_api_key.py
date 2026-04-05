import argparse
import os
import sys

from dotenv import load_dotenv
from zhipuai import ZhipuAI


def mask_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Test ZhipuAI API key connectivity.")
    parser.add_argument("--api-key", default="", help="API key (overrides ZHIPUAI_API_KEY env var)")
    parser.add_argument("--model", default=os.getenv("GLM_MODEL", "glm-5.1"), help="Model name to test")
    parser.add_argument(
        "--base-url",
        default="https://api.z.ai/api/coding/paas/v4",
        help="ZhipuAI base URL",
    )
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("ZHIPUAI_API_KEY", "")
    if not api_key:
        print("FAIL: Missing API key. Set ZHIPUAI_API_KEY in environment or pass --api-key.")
        return 2

    print("Starting API key check...")
    print(f"Model: {args.model}")
    print(f"Base URL: {args.base_url}")
    print(f"API key: {mask_key(api_key)}")

    client = ZhipuAI(api_key=api_key, base_url=args.base_url)

    try:
        response = client.chat.completions.create(
            model=args.model,
            messages=[
                {"role": "system", "content": "You are a health-check assistant."},
                {"role": "user", "content": "Reply with exactly: OK"},
            ],
            temperature=0,
            max_tokens=5,
        )

        text = ""
        if response and getattr(response, "choices", None):
            first = response.choices[0]
            if getattr(first, "message", None):
                text = (first.message.content or "").strip()

        print("PASS: API key is valid and the model responded.")
        print(f"Response preview: {text if text else '<empty>'}")
        return 0

    except Exception as exc:
        error_text = str(exc)
        print("FAIL: API check failed.")
        print(f"Error: {error_text}")

        lowered = error_text.lower()
        if "401" in error_text or "unauthorized" in lowered or "invalid" in lowered:
            print("Hint: API key may be invalid or expired.")
        elif "model" in lowered and ("not exist" in lowered or "不存在" in error_text):
            print("Hint: API key may be valid, but model name is wrong. Try --model with a valid model.")
        elif "timeout" in lowered or "connection" in lowered or "network" in lowered:
            print("Hint: Network or endpoint issue. Verify internet access and base URL.")

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
