import os

import streamlit as st

st.set_page_config(page_title="Intent Router Agent", page_icon="🧭", layout="wide")

EXAMPLES = {
    "Bug (with ID)": "Hey, the payment screen freezes every time I click submit! User ID is CUST_882. Fix this bug immediately!",
    "Critical billing": "CRITICAL: I was charged $500 twice on my account today! Need a refund right now!",
    "Refund request": "Please refund my subscription charge from yesterday for customer CUST_991.",
    "Feature request": "It would be great if the dashboard supported CSV export. CUST_310.",
    "Out of scope": "What is the capital of France, and can you recommend a good pasta recipe?",
}


@st.cache_resource(show_spinner="Loading router engine...")
def load_engine():
    # Streamlit Cloud secrets are exposed as env vars; the engine reads os.getenv at import.
    import router_engine

    return router_engine


def run_dispatch(engine, message: str):
    return engine.route_and_execute_ticket(message)


# ---------- state ----------
st.session_state.setdefault("message", "")
st.session_state.setdefault("history", [])
st.session_state.setdefault("show_result", False)

# ---------- sidebar ----------
with st.sidebar:
    st.header("Controls")
    show_raw = st.toggle("Show raw ticket JSON", value=True)
    show_history = st.toggle("Show history", value=True)
    if st.button("Clear history"):
        st.session_state.history = []
    st.divider()
    st.subheader("Dispatch rules (Python)")
    st.markdown(
        "1. `requires_human_escalation` → human escalation\n"
        "2. `BUG_REPORT` → mock JIRA ticket\n"
        "3. `BILLING_ISSUE` → mock refund\n"
        "4. otherwise → general queue"
    )
    st.caption(
        "Model: `nvidia/nemotron-3-super-120b-a12b` via NVIDIA NIM, temperature 0. "
        "All backend tools are mocks. There is no data upload: the router is stateless."
    )

# ---------- main ----------
st.title("🧭 Structured Intent Extractor & Tool Router")
st.caption("Support message → LCEL prompt + NIM LLM → Pydantic ticket → Python dispatch rules → mock handler")

st.write("**Try an example:**")
cols = st.columns(len(EXAMPLES))
for col, (label, text) in zip(cols, EXAMPLES.items()):
    if col.button(label, use_container_width=True):
        st.session_state.message = text
        st.session_state.show_result = False

st.text_area("Support message", key="message", height=100,
             on_change=lambda: st.session_state.update(show_result=False))

if st.button("Route ticket", type="primary"):
    msg = st.session_state.message.strip()
    if not msg:
        st.warning("Enter a message first.")
    elif not os.getenv("NVIDIA_NIM_API_KEY") and not os.path.exists(".env"):
        st.error("NVIDIA_NIM_API_KEY is not set (env var, .env, or Streamlit secrets).")
    else:
        try:
            engine = load_engine()
            with st.spinner("Calling model..."):
                ticket, result = run_dispatch(engine, msg)
            st.session_state.history.insert(
                0, {"message": msg, "ticket": ticket.model_dump(mode="json"), "result": result}
            )
            st.session_state.show_result = True
        except Exception as e:  # surface API/parse errors instead of a stack trace
            st.error(f"{type(e).__name__}: {e}")

if st.session_state.history and st.session_state.show_result:
    latest = st.session_state.history[0]
    t = latest["ticket"]
    st.subheader("Final backend result")
    st.success(latest["result"])

    st.subheader("Intermediate evidence: extracted ticket")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Category", t["category"])
    c2.metric("Priority", t["priority"])
    c3.metric("Customer ID", t["customer_id"] or "None")
    c4.metric("Human escalation", "Yes" if t["requires_human_escalation"] else "No")
    st.write(f"**Summary:** {t['summary']}")
    if show_raw:
        st.json(t)

    if show_history and len(st.session_state.history) > 1:
        st.subheader("History")
        for h in st.session_state.history[1:]:
            with st.expander(f"{h['ticket']['category']} / {h['ticket']['priority']}: {h['message'][:70]}"):
                st.write(h["result"])
                st.json(h["ticket"])
