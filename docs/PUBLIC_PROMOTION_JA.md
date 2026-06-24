# ELF-mcp-server 宣伝文ドラフト

ELF-mcp-server は、ELF/MAGIC の入力ファイル作成を支援するための公開 MCP サーバです。公開パッケージには、ELF/MAGIC で読みやすい `.mai` / `.meg` 入力デッキ 1600 例、合計 3200 入力ファイルを収録し、モータ、変圧器、MRI、WPT、誘導加熱、加速器用電磁石、アクチュエータ、磁気ギア、NDT、数値検証アンカーなどを横断的に扱えるようにしました。

単なる例題集ではなく、MCP クライアントがユーザーのプロンプトから適切な入力デッキ family を選び、代表例を開き、検証レベルを確認し、次に見るべき recipe へ進めるための知識ベースとして整備しています。全 family は公開 manifest で `validation: passed` として管理され、674 例は `gold_numeric_invariant`、500 例は `silver_observable_contract`、426 例は `silver_proxy_energy` という品質ラベルで区別できます。

公開境界も明確にしています。パッケージに含めるのは、入力デッキ、公開ドキュメント、recipe、validation metadata だけです。solver 出力、比較ログ、機械ローカル path、非公開 provenance は含めません。そのため、研究開発で育てた知見を安全に、かつ実用的に MCP から再利用できます。

矢野様へ紹介する場合は、次の一文が一番伝わりやすいです。

> ELF/MAGIC の使い方を AI agent が迷わず学べるよう、1600 件の公開入力例、500 件の observable-contract 品質強化、品質ラベル、代表例ルーティングを備えた MCP サーバとして整備しました。

## 短い紹介文

ELF-mcp-server は、ELF/MAGIC の入力作成を AI agent が支援するための公開 MCP サーバです。1600 件の公開 `.mai` / `.meg` 入力例、500 件の observable-contract 品質強化、代表例ルーティング、品質ラベル、validation metadata を備え、モータだけでなく変圧器、MRI、WPT、誘導加熱、加速器用電磁石など広い応用例を横断できます。公開物は入力デッキとドキュメントに限定し、solver 出力や非公開 provenance は含めません。
