from datetime import datetime

NOTES_FILE = "notes.md"

def save_note(text: str) -> str:
    """
    Append the given text (with timestamp) to the local notes file.
    """
    ts = datetime.utcnow().isoformat()
    with open(NOTES_FILE, "a") as f:
        f.write(f"- [{ts}] {text}\n")
    return f"Saved note: {text}"

def list_notes(limit: int = 5) -> str:
    """
    Return the last <limit> notes (default 5) from the notes file.
    """
    try:
        with open(NOTES_FILE) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return "No notes found."
    last = lines[-limit:]
    return "Your recent notes:\n" + "".join(last)
