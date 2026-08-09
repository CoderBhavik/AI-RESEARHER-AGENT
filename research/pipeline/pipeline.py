from research.agents.agents import writer_chain, critic_chain
from research.tools.tools import web_scrape, web_search
from rich import print



def _noop(_stage: str) -> None:
    """Default no-op progress hook used when the caller doesn't pass one."""
    pass


def research_agent(topic: str, on_progress=None, max_results:int = 5, max_pages : int = 5) -> dict:
    if on_progress is None:
        on_progress = _noop

    state = {}

    # step 1 - search agent working
    on_progress("search")
    print("\n" + " =" * 50)
    print("step 1 - search agent is working ...")
    print(" =" * 50)

    search_result = web_search.invoke({
        "query": topic,
        "max_results" : max_results
    })
    state["search_result"] = search_result

    # step 2 - reader agent
    on_progress("scrape")
    print("\n" + " =" * 50)
    print("step 2 - Reader agent is scraping top resources ...")
    print(" =" * 50)

    scrape_result = []

    for result in search_result[:max_pages]:
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
