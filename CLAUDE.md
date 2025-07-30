# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリでコードを扱う際のガイダンスを提供します。

## プロジェクト概要

これはAgri_AI6プロジェクトです - LINEメッセージングを通じて農業従事者にインテリジェントなサポートを提供する農業AIエージェントシステムです。マルチエージェントアーキテクチャにはLangGraphを、ハイブリッド検索機能にはMongoDB Atlasを使用します。

**現在のステータス**: このリポジトリには包括的な設計ドキュメントが含まれていますが、実装コードはまだありません。`docs/`フォルダ内の詳細な仕様に基づいて開発準備が整ったグリーンフィールドプロジェクトです。

## アーキテクチャ

### コアコンポーネント

システムはLangGraphを使用した**スーパーバイザー・ワーカー マルチエージェントパターン**に従います：

1. **SupervisorAgent**: LINE webhookメッセージを受信し、ユーザーの意図を分析し、専門エージェントにタスクを委譲する中央オーケストレーター
2. **ReadAgent**: MongoDB Atlasハイブリッド検索（キーワード検索とベクトル検索の組み合わせ）を使用した情報検索を処理
3. **WriteAgent**: 作業記録の登録と確認ワークフローを含むデータ書き込み操作を管理

### 技術スタック

- **AI/エージェント**: Python 3.9+, LangChain, LangGraph
- **LLM**: Google Gemini Pro/Flash とテキスト埋め込みモデル
- **データベース**: MongoDB Atlas
  - Atlas Search: BM25アルゴリズムによるキーワード検索
  - Atlas Vector Search: 埋め込みを使用したセマンティック検索
  - `$rankFusion`ステージを使用した最適なハイブリッド検索
- **インターフェース**: LINE Messaging API と LIFF (LINE Front-end Framework)
- **インフラ**: Google Cloud Functions (webhook), Google Cloud Run (エージェント実行), Google Cloud Pub/Sub (非同期通知)
- **監視**: LangSmith

### データベース設計

MongoDBコレクションは農業データをサポートする柔軟なスキーマを使用：

- **farms**: 基本的な農場情報
- **users**: 作業者データとのLINEアカウント統合
- **fields**: 農場固有データのための拡張可能な`custom_properties`を持つ圃場詳細
- **work_records**: 作業タイプに基づく動的な`details`を持つ日々の作業記録

重要な設計原則: **「固定されたコア情報 + 農家ごとに自由に拡張できるカスタム情報」**

## 開発フェーズ

プロジェクトは4つのフェーズで計画されています：

1. **Phase 1 (3週間)**: Supervisor + ReadAgentによるLINE Q&Aのためのハイブリッド検索を実装した基本基盤
2. **Phase 2 (3週間)**: LINE経由の作業記録登録のためのWriteAgent + 基本LIFFダッシュボード
3. **Phase 3 (4週間)**: 作業提案のためのRecommendationAgent + 高度なLIFF機能
4. **Phase 4 (4週間)**: プロアクティブ通知のためのNotificationAgent + 非同期処理インフラ

## 主要な技術概念

### ハイブリッド検索戦略
- **キーワード検索**: 特定の製品名、型番、固有名詞に効果的
- **ベクトル検索**: 曖昧な表現、文脈理解に効果的
- **組み合わせアプローチ**: MongoDBの`$rankFusion`とReciprocal Rank Fusion (RRF)アルゴリズムを使用

### 状態管理
会話コンテキストのためにLangGraphで`AgriAgentState`を使用：
```python
class AgriAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    thread_id: str
    next_agent: str
    pending_confirmation: Dict[str, Any]
```

### LINE統合
- **チャットインターフェース**: 自然言語による作業報告とシンプルなQ&A
- **LIFFインターフェース**: リッチUIダッシュボード、作業計画可視化、複雑なデータ入力フォーム

## 重要なドキュメント

最も重要な設計ドキュメント：
- `docs/LangGraph_マルチエージェント_要件定義書_v4.md`: メイン要件仕様書 (v4.1)
- `docs/企画書：LangGraphとMongoDBハイブリッド検索を活用した次世代LINE AIエージェントの構築.md`: 技術アーキテクチャの詳細
- `docs/2025-07-26_農場管理AIエージェント完全開発ガイドのコピー.md`: MongoDBの柔軟性に焦点を当てた開発ガイド

## 開発ガイドライン

### システム実装時：

1. **Phase 1から開始**: 基本的なLINE webhook → LangGraph → MongoDB Atlasフローを実装
2. **MongoDB Atlas機能を使用**: 別々のベクトルデータベースではなくネイティブハイブリッド検索を活用
3. **柔軟性のための設計**: 農場がスキーマを動的に拡張できるようにMongoDBのドキュメントモデルを使用
4. **非同期処理の実装**: LINE webhookレスポンスは即座である必要があり、重いAI処理にはバックグラウンドタスクを使用
5. **状態永続化**: 会話継続のためにMongoDBをLangGraphチェックポインターとして使用
6. **既存資産の移行**: システムは「Agri_AI3」の上に構築 - 既存の11個のLangChainツールとMongoDBスキーマを可能な限り再利用

### アーキテクチャの決定事項

- **単一データベースアプローチ**: MongoDB Atlasがすべてのデータタイプ（ドキュメント、ベクトル、検索インデックス、会話状態）を処理してデータ同期の複雑さを排除
- **グラフベースエージェント制御**: LangGraphは線形チェーンに対して複雑なエージェント相互作用の明示的な制御フローを提供
- **LINEファーストインターフェース**: 複雑な可視化にはLIFFを使用した自然言語プライマリインターフェース
- **ハイブリッド検索最適化**: 農業ドメインクエリのための精密なキーワードマッチングとセマンティック理解の組み合わせ

## ビジネスコンテキスト

このシステムは以下を必要とする農業従事者をターゲットとします：
- 圃場にいる間の「次に何をすべきか」決定への即座のアクセス
- 思考/決定時間を10分から0分への短縮
- LINEを通じた自然言語による作業記録
- 過去の作業とコンテキスト推奨のAI記憶

目標は、使用とともに賢くなり、農業意思決定の認知負荷を排除するAIパートナーを作成することです。