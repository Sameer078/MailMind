from typing import TypedDict, Literal, NotRequired
from mongo_service import scam_score, save_mail
from llm_process import scam_detection, reply_generator, task_analyze
from datetime import datetime
from llm_guardrails import mail_filter
from langgraph.graph import END, StateGraph, START
from langchain_core.runnables import RunnableLambda

# ---------- Define State Types ----------
class MailMindState(TypedDict):
    input_email: dict
    email_metadata: dict
    email_body: str
    is_safe: NotRequired[Literal["pass", "block"]]
    scam_status: NotRequired[Literal["SCAM", "LEGIT"]]
    replySubject: NotRequired[str]
    replyBody: NotRequired[str]
    reason: NotRequired[str]
    scam_score: NotRequired[float]
    totalMails: NotRequired[int]
    scam_count: NotRequired[int]
    isWork: NotRequired[bool]
    work_type: NotRequired[str]
    work_details: NotRequired[dict]

# ---------- Extract Email ----------
def extract_email(state: MailMindState) -> MailMindState:
    input_email = state.get("input_email", "")
    metadata = {
        "mail_id":input_email.get("mail_id",""),
        "from": input_email.get("from"),
        "subject": input_email.get("subject"),
        "timestamp": input_email.get("timestamp"),
        "mailer": input_email.get("mailer"),
        "reciever": input_email.get("reciever"),
    }
    body = input_email.get("body", "")
    return {**state, "email_metadata": metadata, "email_body": body}

# ---------- Scam Score ----------
def get_scam_score(state: MailMindState) -> MailMindState:
    sender_email = state["email_metadata"]["from"]
    scam_result = scam_score(sender_email)
    return {
        **state,
        "scam_score": scam_result['scam_score'],
        "totalMails": scam_result['total_count'],
        "scam_count": scam_result['scam_count'],
    }

# ---------- Scam Detection (LLM with structured output) ----------
def detect_scam(state: MailMindState) -> MailMindState:
    state_partial = {
            "email_body": state["email_body"],
            "scam_score": state["scam_score"],
            "scam_count": state["scam_count"],
            "totalMails": state["totalMails"],
        }
    parsed = scam_detection(state_partial)
    return {**state, "scam_status": parsed.classification, "reason": parsed.reasoning}

# ---------- Generate Reply ----------
def generate_reply(state: MailMindState) -> MailMindState:
    parsed = reply_generator(state["email_body"])
    return {**state, "replyBody": parsed.replyBody, "replySubject": parsed.replySubject}

# ---------- Analyze Mail ----------
def analyze_mail(state: MailMindState) -> MailMindState:
    parsed = task_analyze(state["email_body"])
    return {
        **state,
        "isWork": parsed.isWork,
        "work_type": parsed.work_type,
        "work_details": parsed.work_details,
    }

# ---------- Store Mail ----------
def store_data(state: MailMindState) -> MailMindState:
    email_doc = {
        "email_metadata": state.get("email_metadata", {}),
        "email_body": state.get("email_body", ""),
        "scam_status": state.get("scam_status", "SCAM"),
        "reason": state.get("reason", ""),
        "created_at": datetime.now(),
    }
    if state.get("scam_status") == "LEGIT":
        email_doc["replySubject"] = state.get("replySubject", "")
        email_doc["replyBody"] = state.get("replyBody", "")
        email_doc["isWork"] = state.get("isWork", False)
        email_doc["work_type"] = state.get("work_type", "")
        email_doc["work_details"] = state.get("work_details", {})
    save_mail(email_doc)
    return state

# ---------- Mail Filter (personal info, prompt injection) LLM Guardrails ----------
def unified_email_filter(state: MailMindState) -> MailMindState:
    body = state.get("email_body", "")
    is_safe = mail_filter(body)
    return {**state, "is_safe": is_safe}



def graph_mail():
    mailmind_graph = StateGraph(MailMindState)
    mailmind_graph.add_node("extract_email", RunnableLambda(extract_email))
    mailmind_graph.add_node("filter_email", RunnableLambda(unified_email_filter))

    def filter_router(state: MailMindState) -> dict:
        if state.get("is_safe") == "pass":
            return {"next": "pass"}
        else:
            return {"next": "block"}

    mailmind_graph.add_node("filter_router", RunnableLambda(filter_router))
    mailmind_graph.add_node("get_scam_score", RunnableLambda(get_scam_score))
    mailmind_graph.add_node("detect_scam", RunnableLambda(detect_scam))
    mailmind_graph.add_node("generate_reply", RunnableLambda(generate_reply))
    mailmind_graph.add_node("analyze_mail", RunnableLambda(analyze_mail))
    mailmind_graph.add_node("store_data", RunnableLambda(store_data))

    def scam_router(state: MailMindState) -> dict:
        if state.get("scam_status") == "SCAM":
            return {"next": "stop"}
        else:
            return {"next": "process"}

    mailmind_graph.add_node("scam_router", RunnableLambda(scam_router))
    mailmind_graph.add_edge(START, "extract_email")
    mailmind_graph.add_edge("extract_email", "filter_email")
    mailmind_graph.add_edge("filter_email", "filter_router")

    mailmind_graph.add_conditional_edges(
        "filter_router",
        lambda state: state.get("next"),
        {"pass": "get_scam_score", "block": END},
    )

    mailmind_graph.add_edge("get_scam_score", "detect_scam")
    mailmind_graph.add_edge("detect_scam", "scam_router")

    mailmind_graph.add_conditional_edges(
        "scam_router",
        lambda state: state.get("next"),
        {"stop": "store_data", "process": "generate_reply"},
    )

    mailmind_graph.add_edge("generate_reply", "analyze_mail")
    mailmind_graph.add_edge("analyze_mail", "store_data")

    mailmind_graph.add_edge("store_data", END)
    mailmindRun = mailmind_graph.compile()
    return mailmindRun
