from agents import writer_chain, critic_chain
from tools import web_scrape, web_search
from rich import print

# --------------------------------------------------------------------------
# NOTE ON CHANGES (for the web UI integration):
#
# 1. Fixed a pre-existing syntax issue: the original f-strings used the same
#    quote character (") both to open the f-string and to index into the
#    `state` dict (state["search_result"]). That only parses on Python 3.12+
#    (PEP 701). Switched the inner quotes to single quotes so this runs on
#    any modern Python version.
#
# 2. Added an OPTIONAL `on_progress` callback parameter. It defaults to
#    `None`, so every existing caller (e.g. `python pipeline.py` from the
#    terminal) behaves exactly as before. When provided, it is called with a
#    short stage key ("search", "scrape", "write", "critic", "done") right
#    before that stage starts, so a UI (like the Streamlit app) can render a
#    live progress timeline without needing to know anything about the
#    research logic itself.
#
# No agent/tool/prompt logic was touched.
# --------------------------------------------------------------------------


def _noop(_stage: str) -> None:
    """Default no-op progress hook used when the caller doesn't pass one."""
    pass


def research_agent(topic: str, on_progress=None) -> dict:
    if on_progress is None:
        on_progress = _noop

    state = {}

    # step 1 - search agent working
    on_progress("search")
    print("\n" + " =" * 50)
    print("step 1 - search agent is working ...")
    print(" =" * 50)

    search_result = web_search.invoke({
        "query": topic
    })
    state["search_result"] = search_result

    # step 2 - reader agent
    on_progress("scrape")
    print("\n" + " =" * 50)
    print("step 2 - Reader agent is scraping top resources ...")
    print(" =" * 50)

    scrape_result = []

    for result in search_result:
        scrape_result.append(
            web_scrape.invoke({
                "url": result["url"]
            })
        )

    state["scrape_result"] = scrape_result

    # step 3 - writer chain
    on_progress("write")
    print("\n" + " =" * 50)
    print("step 3 - Writer is drafting the report ...")
    print(" =" * 50)

    combined_result = (
        f"Search result = {state['search_result']} \n\n"
        f"Scraped result = {state['scrape_result']}\n\n"
    )

    report = writer_chain.invoke({
        "topic": topic,
        "research": combined_result
    })

    state["Report"] = report

    print("\n Final Report\n", state['Report'])

    # step 4 - critic report
    on_progress("critic")
    print("\n" + " =" * 50)
    print("step 4 - critic is reviewing the report ")
    print(" =" * 50)

    feedback = critic_chain.invoke({
        "report": report
    })
    state["Feedback"] = feedback
    print("\n critic report \n", state['Feedback'])

    on_progress("done")

    return state


if __name__ == "__main__":
    # topic = input("Enter what you want to research : ")
    research_agent("What is Quantum computer?")
