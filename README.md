# pyarticle
---

- モジュールのインストール
  ```
  pip install -r requirements.txt
  ```
- 次を実行する
  ```
  python article.py
  ```
- 実行後, `env/.env` ファイルが作成されるので以下を記述
  ```
  user_id=[qiita user_id]
  qiita_token=[qiita api token]
  slack_xoxb_token=[slack xoxb token]
  slack_channel=[slack channel name]
  ```
  - 参考
    - qiita api token : https://qiita.com/miyuki_samitani/items/bfe89abb039a07e652e6
    - slack api token : https://zenn.dev/kou_pg_0131/articles/slack-api-post-message
- 再度実行
