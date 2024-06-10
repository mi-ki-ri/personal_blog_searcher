import json
from pathlib import Path
import time
from duckduckgo_search import DDGS
import argparse
from openai import OpenAI
from bs4 import BeautifulSoup

client = OpenAI()


def main():
    print("DuckDuckGo Search")
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", type=str, help="Keyword to search for")
    parser.add_argument(
        "-n", "--num-results", type=int, default=50, help="Number of results to return"
    )
    args = parser.parse_args()
    keyword = args.keyword
    num_results = args.num_results

    print(f"Searching for {keyword} limit {num_results} results")
    ddgs = DDGS(timeout=30)
    search_result = ddgs.text(keyword, max_results=num_results, region="jp-jp")

    # print(search_result)

    if not Path(f"./dst/{keyword}.tsv").exists():
        with open(f"./dst/{keyword}.tsv", mode="w") as f:
            f.write("Title\tURL\tPoint\n")

    for i, result in enumerate(search_result):
        time.sleep(1)
        print(f"{i}: {result}")

        url = result["href"]
        title = result["title"]

        soup = BeautifulSoup(url, "html.parser")
        raw_body = soup.text
        if len(raw_body) > 1000:
            raw_body_slice = raw_body[:1000]
        else:
            raw_body_slice = raw_body

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたはWebサイトを解釈するAIです。"},
                {
                    "role": "system",
                    "content": "以下に渡されたWebサイトを読み込み、有用な個人サイト・個人ブログかどうかを判断してください。",
                },
                {
                    "role": "system",
                    "content": "具体的には、まとめサイト・まとめブログ・商用ブログなどではないブログやサイトを高評価してください。",
                },
                {
                    "role": "system",
                    "content": "返答はJSON形式で、is_personal_site: 0.0～1.0の間で数値が変動します。",
                },
                {"role": "user", "content": raw_body_slice},
            ],
            response_format={"type": "json_object"},
            timeout=30,
        )
        print(completion.choices[0].message.content)

        json_content = json.loads(completion.choices[0].message.content)

        if json_content["is_personal_site"] < 0.4:
            continue

        point = json_content["is_personal_site"]

        with open(f"./dst/{keyword}.tsv", mode="a") as f:
            f.write(f"{title}\t{url}\t{point}\n")


if __name__ == "__main__":
    main()
