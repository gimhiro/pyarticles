import requests
import urllib.parse as urlp
import bs4
import hashlib
import datetime
import json
import time
import os

os.makedirs("./data", exist_ok=True)
os.makedirs("./env", exist_ok=True)
with open("env/.env","a+") as f:
    pass

def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()

def is_valid_env(env):
    if len(env) != 4:
        return False
    return all(v!="" for k,v in env.items())

# envファイル読み込み
with open("env/.env") as f:
    env = {}
    for l in f.readlines():
        if len(l.split("="))==2:
            k, v = l.split("=")
            env[k.strip()] = v.strip()
print("[env] ",is_valid_env(env))

with open("env/tags") as f:
    tags = list(map(lambda s: s.strip(), f.readlines()))

# for qiita
def shorter(obj):
    labels = ["title", "tags", "url", "likes_count", "created_at"]
    obj = {k: obj[k] for k in labels}
    obj["tags"] = [tag["name"] for tag in obj["tags"]]
    obj["domain"] = "qiita"
    obj["id"] = sha256(obj["title"]+obj["domain"])
    return obj


def get_from_qiita(user_id, token):
    headers = {"Authorization": f"Bearer {token}"}

    # フォロー中のタグ一覧を取得
    tag_url = f"https://qiita.com/api/v2/users/{user_id}/following_tags"
    query = "page=1&per_page=99"
    url = f"{tag_url}?{urlp.quote(query,safe='=&-,_./')}"
    r_tag = requests.get(url, headers=headers)
    tags = "tag:"+",".join([obj["id"] for obj in r_tag.json()])
    print("[qiita] get tags")

    # フォロー中のタグの最新記事を取得
    list_url = "https://qiita.com/api/v2/items"
    query = query + f"&query={tags}"
    url = f"{list_url}?{urlp.quote(query,safe='=&-,_./')}"
    response = requests.get(url, headers=headers)
    print("[qiita] get articles")

    return [shorter(obj) for obj in response.json() if obj["likes_count"] >= 5]

# for zenn
def html2obj(html,tag):
    elem = html.select('.ArticleList_link__vf_6E')[0]
    obj = {}
    obj["title"] = elem.string
    obj["tags"] = [tag]
    obj["url"] = "https://zenn.dev/" + elem["href"]
    elems = html.select('.ArticleList_meta__E1zr4')[0].contents
    if len(elems) == 1:
        obj["likes_count"] = 0
    else:
        obj["likes_count"] = int(elems[1].text)
    obj["created_at"] = elems[0]["datetime"]
    obj["domain"] = "zenn"
    obj["id"] = sha256(obj["title"]+obj["domain"])
    return obj

def get_from_zenn(tags):
    result = {}
    for i,tag in enumerate(tags):
        # tag に紐づく記事を取得
        url = f"https://zenn.dev/topics/{tag}?order=latest"
        response = requests.get(url)
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        elems = soup.select('.ArticleList_container__JDK24')
        
        for e in elems:
            obj = html2obj(e,tag)
            if obj["likes_count"]>=5:
                result[obj["id"]] = obj
        
        time.sleep(1)
        print(f"[zenn] tag: {tag} {i+1}/{len(tags)}")
    return list(result.values())

# for slack
def post(obj):
    text = f"""*{obj["title"]}* | <{obj["url"]}|{obj["domain"]}>
    {datetime.datetime.fromisoformat(obj["created_at"]).strftime("%Y/%m/%d %H:%M")} / ☆{obj["likes_count"]}
    tag: {", ".join(obj["tags"])}"""

    requests.post("https://slack.com/api/chat.postMessage",data={
        "token":env["slack_xoxb_token"],
        "channel":env["slack_channel"],
        "text":text
    })
    
def post2slack(obj_list):
    print("[slack] start.")
    for obj in obj_list:
        post(obj)
        time.sleep(5)
    requests.post("https://slack.com/api/chat.postMessage",data={
        "token":env["slack_xoxb_token"],
        "channel":f"#{env['slack_channel']}",
        "text":"==="*5
    })
    print("[slack] done.")

def main():
    q_obj_list = get_from_qiita(env["user_id"],env["qiita_token"])
    z_obj_list = get_from_zenn(tags)
    obj_list = q_obj_list + z_obj_list

    dto = {obj["id"]:obj for obj in obj_list}
    try:
        with open("data/articles.json","r") as f:
            dfrom = json.load(f)
    except:
        with open("data/articles.json","w") as f:
            json.dump({}, f, indent=2)
            dfrom = {}

    new_id = set(dto.keys()) - set(dfrom.keys())
    print(f"[all] {len(new_id)} new item(s)")
    if len(new_id)>0:
        obj_list = [obj for obj in obj_list if obj["id"] in new_id]

        post2slack(obj_list)

        for obj in obj_list:
            dfrom[obj["id"]] = obj

        with open('data/articles.json', 'w') as f:
            json.dump(dfrom, f, indent=2)
    print("[all] done")

if is_valid_env(env):
    main()