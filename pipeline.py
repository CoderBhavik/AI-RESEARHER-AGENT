from agents import writer_chain, critic_chain
from tools import web_scrape, web_search
from rich import print

def research_agent(topic : str) -> str:
    state = {}
    #search agent working 
    print("\n"+" ="*50)
    print("step 1 - search agent is working ...")
    print(" ="*50)

    search_result = web_search.invoke({
        "query" : topic
    })
    state["search_result"] = search_result


    
    # state["search_result"] = search_result["messages"][-1].content
    # print("\n search result ",state["search_result"])

    #step 2 - reader agent 
    print("\n"+" ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print(" ="*50)

    scrape_result = []

    for result in search_result:
        scrape_result.append(
            web_scrape.invoke({
                "url" : result["url"]
                }
            )
        )

    state["scrape_result"] = scrape_result
    # print("\nscraped content: \n", state['scrape_result'])

    #step 3 - writer chain 

    print("\n"+" ="*50)
    print("step 3 - Writer is drafting the report ...")
    print(" ="*50)
    
    combined_result = (
        f"Search result = {state["search_result"]} \n\n"
        f"Scraped result = {state["scrape_result"]}\n\n"
    )

    report = writer_chain.invoke({
    "topic": topic,
    "research": combined_result
    })

    state["Report"] = report

    print("\n Final Report\n",state['Report'])

    #critic report 

    print("\n"+" ="*50)
    print("step 4 - critic is reviewing the report ")
    print(" ="*50)

    feedback = critic_chain.invoke({
        "report": report
        }
    )
    state["Feedback"] = feedback
    print("\n critic report \n", state['Feedback'])


    return state

if __name__ == "__main__":
    # topic = input("Enter what you want to research : ")
    research_agent("What is Quantum computer?")
