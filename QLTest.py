import json
import math
import csv
import time
import requests
import botocore.auth
import botocore.awsrequest
import botocore.credentials

GRAPHQL_URL = "https://vh7lll5oyzdgzdlz5j4oql2kwm.appsync-api.ap-southeast-2.amazonaws.com/graphql"
REGION = "ap-southeast-2"
IDENTITY_POOL_ID = "ap-southeast-2:c17fbdb5-bd30-4b44-b90c-c2644dca6aca"

QUERY = """
query SearchCourseOrUnit($studyMode: String!, $studyTypes: [ResultTypes!]!, $page: Int!, $phrase: String, $studyLevel: String, $locationCode: String, $fieldOfEducationCode: String, $attendanceModeCode: String) {
  searchCourseOrUnit(
    studyMode: $studyMode
    studyTypes: $studyTypes
    page: $page
    phrase: $phrase
    studyLevel: $studyLevel
    locationCode: $locationCode
    fieldOfEducationCode: $fieldOfEducationCode
    attendanceModeCode: $attendanceModeCode
  ) {
    totalMatches
    results {
      id
      url
      title
      category
      description
    }
  }
}
"""

VARIABLES = {
    "studyMode": "dom",
    "studyTypes": ["UNIT"],
    "phrase": "",
    "studyLevel": "Undergraduate",
    "locationCode": "1",
    "fieldOfEducationCode": None,
    "attendanceModeCode": None,
}


def get_cognito_creds():
    cognito_url = f"https://cognito-identity.{REGION}.amazonaws.com/"
    cognito_headers = {"Content-Type": "application/x-amz-json-1.1"}

    # Step 1: mint a fresh identity from the pool
    id_resp = requests.post(
        cognito_url,
        json={"IdentityPoolId": IDENTITY_POOL_ID},
        headers={**cognito_headers, "X-Amz-Target": "AWSCognitoIdentityService.GetId"},
    )
    id_resp.raise_for_status()
    identity_id = id_resp.json()["IdentityId"]

    # Step 2: exchange it for temporary AWS credentials
    cred_resp = requests.post(
        cognito_url,
        json={"IdentityId": identity_id},
        headers={**cognito_headers, "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity"},
    )
    cred_resp.raise_for_status()
    body = cred_resp.json()
    if "Credentials" not in body:
        raise RuntimeError(f"Cognito error: {body}")
    creds = body["Credentials"]
    print(f"[auth] Got credentials — AccessKeyId prefix: {creds['AccessKeyId'][:4]}, expires: {creds['Expiration']}")
    return creds


def get_signed_headers(creds, body):
    credentials = botocore.credentials.Credentials(
        access_key=creds["AccessKeyId"],
        secret_key=creds["SecretKey"],
        token=creds["SessionToken"],
    )
    aws_req = botocore.awsrequest.AWSRequest(
        method="POST",
        url=GRAPHQL_URL,
        data=body,
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "x-amz-user-agent": "aws-amplify/4.7.14 js",
        },
    )
    botocore.auth.SigV4Auth(credentials, "appsync", REGION).add_auth(aws_req)
    return dict(aws_req.headers)


def fetch_page(page, session, creds, retries=3):
    body = json.dumps({"query": QUERY, "variables": {**VARIABLES, "page": page}})
    for attempt in range(retries):
        headers = get_signed_headers(creds, body)
        resp = session.post(GRAPHQL_URL, data=body, headers=headers)
        if resp.status_code == 403:
            raise PermissionError(f"403 on page {page} — credentials rejected")
        if resp.ok:
            return resp.json()["data"]["searchCourseOrUnit"]
        print(f"Page {page} attempt {attempt + 1} failed ({resp.status_code}), retrying...")
        time.sleep(2 ** attempt)
    raise requests.exceptions.HTTPError(f"Failed to fetch page {page} after {retries} attempts")


def write_units(writer, units):
    for unit in units:
        writer.writerow([unit["id"], unit["title"], unit["url"], unit["category"], unit["description"]])


def UnitScraper(output_path: str, start_page: int = 1):
    creds = get_cognito_creds()
    session = requests.Session()

    def fetch_with_retry(page):
        nonlocal creds
        for attempt in range(3):
            try:
                return fetch_page(page, session, creds)
            except PermissionError:
                if attempt == 2:
                    raise
                wait = 90 * (attempt + 1)
                print(f"403 on page {page} — rate limited, waiting {wait}s...")
                time.sleep(wait)
                creds = get_cognito_creds()
        raise PermissionError(f"Failed to fetch page {page} after retries")

    first = fetch_with_retry(start_page)
    total_matches = first["totalMatches"]
    page_size = len(first["results"])
    total_pages = math.ceil(total_matches / page_size)

    if start_page == 1:
        print(f"Total units: {total_matches}, pages: {total_pages}")
    else:
        print(f"Resuming from page {start_page}/{total_pages}")

    file_mode = "w" if start_page == 1 else "a"

    with open(output_path, file_mode, newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if start_page == 1:
            writer.writerow(["id", "title", "url", "category", "description"])
        write_units(writer, first["results"])

        for page in range(start_page + 1, total_pages + 1):
            time.sleep(0.5)
            data = fetch_with_retry(page)
            write_units(writer, data["results"])
            print(f"Page {page}/{total_pages}")

    print(f"Done. Written to {output_path}")


if __name__ == "__main__":
    UnitScraper("output_v2.csv", start_page=170)
