#!/usr/bin/env python3
"""Simple Vertex AI connectivity test.

This script attempts to initialize Vertex AI and list endpoints in the configured
project/location. It prints helpful errors if authentication or dependencies are
missing.
"""
import sys
import os

try:
    import google.auth
    from google.cloud import aiplatform
    from google.cloud.aiplatform.gapic import EndpointServiceClient
except Exception as e:
    print("ERROR: missing dependency or import failure:", e)
    print("Make sure 'google-cloud-aiplatform' is installed in your environment.")
    sys.exit(2)


def main():
    try:
        creds, project = google.auth.default()
    except Exception as e:
        print("ERROR: google.auth.default() failed:", e)
        print("Make sure you have authenticated (e.g., 'gcloud auth application-default login').")
        return 2

    project = project or os.environ.get("GOOGLE_CLOUD_PROJECT") or "triumph-in-the-skies"
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

    print(f"Using project={project}, location={location}")

    try:
        aiplatform.init(project=project, location=location)
    except Exception as e:
        print("ERROR: aiplatform.init failed:", e)
        return 3

    client = EndpointServiceClient()
    parent = f"projects/{project}/locations/{location}"

    try:
        endpoints = list(client.list_endpoints(parent=parent))
        print(f"Found {len(endpoints)} endpoints.")
        for i, ep in enumerate(endpoints[:5], start=1):
            print(f"{i}. name={ep.name}, display_name={getattr(ep, 'display_name', '')}")
        print("Vertex AI API connectivity test: SUCCESS")
        return 0
    except Exception as e:
        print("ERROR: API call failed:", e)
        print("Possible causes: insufficient IAM permissions, wrong project/location, or networking issues.")
        return 4


if __name__ == '__main__':
    sys.exit(main())
