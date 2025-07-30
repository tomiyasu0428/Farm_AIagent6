import os
from typing import Annotated, List, Literal
from typing_extensions import TypedDict

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

# --- 環境変数の読み込みとLLMの初期化 ---
load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")


# --- エージェントの定義 ---

class AgentState(TypedDict):
    """エージェントの状態を管理するクラス"""
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: Literal["ReadAgent", "WriteAgent", "end"]


def supervisor_agent(state: AgentState):
    """ユーザーの意図を解釈し、次のエージェントを決定する司令塔"""
    print("---SUPERVISOR---")
    last_message = state['messages'][-1].content
    
    # LLMに次のアクションを問い合わせる
    prompt = f"""あなたは農業アシスタントの司令塔です。ユーザーからの以下のメッセージに対して、次に呼び出すべき最適なエージェントを選択してください。
- 情報を検索・要約する場合は "ReadAgent"
- 何かを記録・保存する場合は "WriteAgent"
- どちらでもない、あるいは対話が終了する場合は "end"
とだけ答えてください。

ユーザーメッセージ: "{last_message}"
"""
    response = llm.invoke(prompt)
    # LLMの応答から余分な空白やマークダウンを削除
    next_agent_name = response.content.strip().replace("`", "")
    
    print(f"Supervisor selected: {next_agent_name}")
    # 状態を更新
    return {"next_agent": next_agent_name}

def read_agent(state: AgentState):
    """情報検索を担当するエージェント（ダミー）"""
    print("---READ AGENT---")
    # TODO: MongoDBハイブリッド検索を実装
    response_text = "ReadAgentが応答: 情報を検索しました（現在はダミー応答です）。"
    return {"messages": [AIMessage(content=response_text)]}

def write_agent(state: AgentState):
    """情報記録を担当するエージェント（ダミー）"""
    print("---WRITE AGENT---")
    # TODO: MongoDBへの書き込み処理を実装
    response_text = "WriteAgentが応答: 情報を記録しました（現在はダミー応答です）。"
    return {"messages": [AIMessage(content=response_text)]}

def final_response_node(state: AgentState):
    """対話の最終応答を生成するノード"""
    print("---FINAL RESPONSE---")
    # ここでは単純に最後のメッセージを返す
    # 必要に応じて、ここまでの対話履歴を要約するなどの処理を追加できる
    last_message = state["messages"][-1]
    return {"messages": [last_message]}


# --- グラフの構築 ---

workflow = StateGraph(AgentState)

# ノードの追加
workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("ReadAgent", read_agent)
workflow.add_node("WriteAgent", write_agent)
workflow.add_node("FinalResponse", final_response_node)


# エントリーポイントの設定
workflow.set_entry_point("supervisor")

# 条件付きエッジの設定
workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["next_agent"],
    {
        "ReadAgent": "ReadAgent",
        "WriteAgent": "WriteAgent",
        "end": "FinalResponse" # 対話終了時はFinalResponseノードへ
    }
)

# 各エージェントからENDへのエッジ
workflow.add_edge("ReadAgent", END)
workflow.add_edge("WriteAgent", END)
workflow.add_edge("FinalResponse", END)


# グラフをコンパイル
agent_app = workflow.compile()


# --- LINE Bot & FastAPIのセットアップ ---

app = FastAPI()

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

if not channel_secret or not channel_access_token:
    print('Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    exit(1)

handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=channel_access_token)

@app.post("/callback")
async def callback(request: Request):
    """LINEからのWebhookを受け取るエンドポイント"""
    signature = request.headers['X-Line-Signature']
    body = await request.body()
    body = body.decode()

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """テキストメッセージを処理し、LangGraphエージェントを呼び出すハンドラ"""
    
    user_message = HumanMessage(content=event.message.text)
    
    # TODO: セッション管理を実装するまでは、対話履歴は毎回リセットされる
    config = {"recursion_limit": 5} # 再帰制限を設定
    result = agent_app.invoke({"messages": [user_message]}, config=config)
    
    # 最後のメッセージがAIからのものであることを確認
    if result['messages'] and isinstance(result['messages'][-1], AIMessage):
        agent_response = result['messages'][-1]
        response_text = agent_response.content
    else:
        # Supervisorが 'end' を返した場合など、AIの応答がない場合のフォールバック
        response_text = "ご用件を承りました。他に何かありますか？"


    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response_text)]
            )
        )

@app.get("/")
async def root():
    return {"message": "Agri AI Agent is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
