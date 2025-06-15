import faiss
import pickle
from sentence_transformers import SentenceTransformer
from nearai import Environment
from tools.galaxus import find_big_drops
from tools.notes   import save_note, list_notes
from tools.search import web_search
from nearai import tools


# load index & metadata once
INDEX_FILE = "faiss_index.bin"
META_FILE  = "doc_chunks.pkl"
EMBED_MODEL = "all-MiniLM-L6-v2"

print("Loading FAISS index…")
idx = faiss.read_index(INDEX_FILE)
with open(META_FILE, "rb") as f:
    meta = pickle.load(f)
texts = meta["texts"]
metas = meta["metas"]
embedder = SentenceTransformer(EMBED_MODEL)

def search_knowledge(query: str, top_k: int = 3) -> str:
    """Find the top_k most relevant text chunks for the query."""
    q_emb = embedder.encode([query])
    D, I = idx.search(q_emb, top_k)
    results = []
    for i in I[0]:
        info = metas[i]
        text = texts[i]
        results.append(f"• ({info['path']} #chunk{info['chunk_id']}): {text[:200]}…")
    return "\n".join(results)

def register_tools(env: Environment):
    tr = env.get_tool_registry()
    # — your RAG tool —
    tr.register_tool(search_knowledge)

    # — your custom web & note tools —
    tr.register_tool(web_search)
    tr.register_tool(save_note)
    tr.register_tool(list_notes)

    # — built-ins for file I/O —
    tr.register_tool(tools.list_files, name="list_files")
    tr.register_tool(tools.read_file,  name="read_file")



def handle_research(env: Environment, raw: str):
    # strip “search:” prefix if present
    query = raw.split(":", 1)[1].strip() if ":" in raw else raw
    env.add_reply("Researching for you…")
    snippet = web_search(query)
    env.add_reply(snippet)


def handle_notes(env: Environment, msg: str):
    # If user wants to list notes
    if "list notes" in msg or "show notes" in msg:
        resp = list_notes()
        env.add_reply(resp)
    else:
        # Anything else starting with note: or remember
        # we strip the keyword and save the rest
        note_text = msg.split(":", 1)[1].strip() if ":" in msg else msg
        resp = save_note(note_text)
        env.add_reply(resp)

def handle_galaxus(env: Environment):
    url    = env.env_vars.get("GALAXUS_URL")
    rating = float(env.env_vars.get("GALAXUS_MIN_RATING"))
    reviews= int(env.env_vars.get("GALAXUS_MIN_REVIEWS"))
    threshold = float(env.env_vars.get("GALAXUS_DROP_THRESHOLD"))
    baseline_days = int(env.env_vars.get("GALAXUS_BASELINE_DAYS", "30"))
    drops  = find_big_drops(url,
                            min_rating=rating,
                            min_reviews=reviews,
                            drop_threshold=threshold,
                            baseline_days=baseline_days)
    if not drops:
        env.add_reply(f"No items with ≥{threshold}% drop on Galaxus.")
    else:
        lines = ["Found price drops:"]
        for d in drops:
            lines.append(
                f"- {d['title']}: down {d['drop_pct']}% "
                f"(from CHF {d['baseline']} to CHF {d['current']}) — {d['url']}"
            )
        env.add_reply("\n".join(lines))
    pass

def run(env: Environment):
    # register all of your tools (custom + built-ins)
    register_tools(env)

    raw = env.latest_message().strip()
    msg = raw.lower()

    if "galaxus" in msg:
        handle_galaxus(env)

    elif msg.startswith(("note:", "remember")):
        handle_notes(env, raw)

    elif msg.startswith(("search:", "research")):
        handle_research(env, raw)

    elif "list notes" in msg or "show notes" in msg:
        handle_notes(env, raw)

    else:
        # now that all tools are registered, let the LLM pick and call them
        result = env.completions_and_run_tools()
        env.add_reply(result)
