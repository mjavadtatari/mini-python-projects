import os
import json
import pandas as pd
from openai import OpenAI

# ================= CONFIG =================
LIARA_AI_TOKEN = os.getenv("LIARA_AI_TOKEN")  # read from environment variable
if not LIARA_AI_TOKEN:
    raise ValueError("❌ Environment variable LIARA_AI_TOKEN is not set!")

BASE_URL = "https://ai.liara.ir/api/68dc1773f5784872a3f78303/v1"
MODEL = "openai/gpt-4o-mini"
EXCEL_FILE = "folders_with_categories.xlsx"

# ================= INIT =================
client = OpenAI(base_url=BASE_URL, api_key=LIARA_AI_TOKEN)

DIR_PATH = os.getcwd()
all_items = os.listdir(DIR_PATH)

# Only folders
folders = [item for item in all_items if os.path.isdir(
    os.path.join(DIR_PATH, item))]

# ================= LOAD EXISTING DATA =================
if os.path.exists(EXCEL_FILE):
    existing_data = pd.read_excel(EXCEL_FILE)
    existing_folders = set(existing_data["Folder Name"].tolist())
else:
    existing_data = pd.DataFrame(columns=["Folder Name", "Category"])
    existing_folders = set()

# New folders = those not yet categorized
new_folders = [f for f in folders if f not in existing_folders]

# ================= REMOVE MISSING FOLDERS FROM EXCEL =================
# Keep only rows where folder still exists
existing_data = existing_data[existing_data["Folder Name"].isin(folders)]

# ================= ASK AI FOR CATEGORIZATION (ONLY FOR NEW FOLDERS) =================
new_categorized = []
if new_folders:
    # Create mapping: id -> folder name
    folders_with_id = [{"id": i, "name": f}
                       for i, f in enumerate(new_folders, start=1)]

    prompt = f"""
    You are given a list of folders with IDs:

    {json.dumps(folders_with_id, indent=2, ensure_ascii=False)}

    Categorize each folder into exactly one of these categories:
    [dotnet, react, nextjs, vuejs, security, linux, python, devops].

    Return ONLY valid JSON in this format:
    [
      {{"id": 1, "category": "dotnet"}},
      {{"id": 2, "category": "vuejs"}}
    ]

    ⚠️ Do not include code blocks, markdown, or folder names. Only raw JSON.
    """

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = completion.choices[0].message.content.strip()

    # Remove markdown code fences if present
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        response_text = response_text.lstrip("json").strip(" \n")

    # Parse JSON
    try:
        categorized = json.loads(response_text)
    except json.JSONDecodeError:
        print("❌ Could not parse JSON from response. Raw response:")
        print(response_text)
        categorized = [{"id": f["id"], "category": "uncategorized"}
                       for f in folders_with_id]

    # Join ids with folder names
    id_to_name = {f["id"]: f["name"] for f in folders_with_id}
    new_categorized = [{"Folder Name": id_to_name[c["id"]],
                        "Category": c["category"].capitalize()} for c in categorized]

# ================= MERGE OLD + NEW DATA =================
final_df = existing_data.copy()

# Add new categorizations
new_count = 0
if new_categorized:
    df_new = pd.DataFrame(new_categorized)
    final_df = pd.concat([final_df, df_new], ignore_index=True)
    new_count = len(df_new)

# Ensure consistent capitalization
final_df["Category"] = final_df["Category"].str.capitalize()

# ================= EXPORT TO EXCEL =================
final_df.to_excel(EXCEL_FILE, index=False)

print(
    f"✅ Excel file updated: {EXCEL_FILE} ({new_count} new folders categorized)")
