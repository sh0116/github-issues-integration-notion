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
issues = repo.get_issues(state='all')  # 'all'로 설정하여 열린 이슈와 닫힌 이슈 모두 가져옴

query = notion.databases.query(database_id=database_id)
notion_issues = {page["properties"]["Title"]["title"][0]["text"]["content"]: page["id"] for page in query["results"] if "Title" in page["properties"]}

for issue in issues:
    # 기본 properties 설정. 'Name' 대신에 실제 Notion 데이터베이스에 정의된 제목 속성의 이름을 사용하세요.
    properties = {
        "Title": { # 'Name' 대신 Notion에서 사용하는 정확한 필드 이름을 사용해야 합니다.
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
                        "content": issue.body or "No description", # 본문이 없는 경우 대체 텍스트 제공
                    },
                },
            ],
        },
        # 'Comments'를 'rich_text' 유형으로 처리합니다.
        "Comments": {
            "rich_text": [
                {
                    "text": {
                        "content": str(issue.comments), # 댓글 수를 문자열로 변환
                    },
                },
            ],
        },
        "Created At": {
            "date": {
                "start": issue.created_at.isoformat(),
                "end": None,
            },
        },
        # 이슈가 닫혔을 경우에만 'Closed At' 속성 추가
        "State": {
            "select": {
                "name": issue.state,
            },
        },
    }

    if issue.closed_at:
        properties["Closed At"] = {
            "date": {
                "start": issue.closed_at.isoformat(),
                "end": None,
            },
        }

    # Notion에 해당 이슈가 이미 존재하는지 확인
    if issue.title in notion_issues:
        # 해당 이슈를 업데이트
        notion.pages.update(page_id=notion_issues[issue.title], properties=properties)
    else:
        # 새로운 이슈를 생성
        notion.pages.create(parent={"database_id": database_id}, properties=properties)

