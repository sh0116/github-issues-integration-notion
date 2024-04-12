from github import Github
from github import Auth

from notion_client import Client
import env


# GitHub 설정
# using an access token
auth = Auth.Token(env.TOKEN)
g = Github(auth=auth, verify=False)

repo = g.get_repo(f"{env.OWNER}/{env.REPO_NAME}")

# Notion 설정
notion_token = env.NOTION_TOKEN
notion = Client(auth=notion_token)
database_id = env.NOTION_DB

# GitHub 이슈 가져오기
issues = repo.get_issues(state='all')  

query = notion.databases.query(database_id=database_id)
notion_issues = {page["properties"]["Title"]["title"][0]["text"]["content"]: page["id"] for page in query["results"] if "Title" in page["properties"]}
for issue in issues:

    properties = {
        "Title": { 
            "title": [
                {
                    "text": {
                        "content": issue.title,
                    },
                },
            ],
        },
        "Description": {
            "rich_text": [
                {
                    "text": {
                        "content": issue.body or "No description",
                    },
                },
            ],
        },
        "Links": {
            "url": issue.html_url
        },
        "Created At": {
            "date": {
                "start": issue.created_at.isoformat(),
                "end": issue.closed_at.isoformat() if issue.closed_at else None,
            },
        },
        "State": {
            "select": {
                "name": issue.state,
            },
        },
    }

    if issue.title in notion_issues:
        notion.pages.update(page_id=notion_issues[issue.title], properties=properties)
    else:
        notion.pages.create(parent={"database_id": database_id}, properties=properties)

