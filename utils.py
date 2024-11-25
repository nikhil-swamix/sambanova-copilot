from contextlib import suppress

# Tailwind Like Programmatic Aliasing for sizes
modelmap = {
    "xxs": "Meta-Llama-3.2-1B-Instruct",
    "xs": "Meta-Llama-3.2-3B-Instruct",
    "s": "Meta-Llama-3.1-8B-Instruct",
    "m": "Meta-Llama-3.1-70B-Instruct",  # medium basis point
    "l": "Meta-Llama-3.1-405B-Instruct",
    "v:m": "Llama-3.2-11B-Vision-Instruct",  # vision
    "v:l": "Llama-3.2-11B-Vision-Instruct",
}


def get_resource_path(relative_path):
    import sys, os

    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_client():
    import os
    from openai import OpenAI

    if not os.getenv('SAMBANOVA_API_KEY'):
        self.status_label.setText("Error: APIKEY not found in environment variables")
        raise Exception("APIKEY not found in environment variables")

    client = OpenAI(base_url="https://api.sambanova.ai/v1", api_key=os.getenv('SAMBANOVA_API_KEY'))
    return client


def smart_chat(query, system="", model="s", max_tokens=2048, temperature=0.1, randomize=False):
    """
    Smart chat function that uses the OpenAI API to generate a response.
    :param query: The user's query.
    :param system: The system message to guide the model.
    :param model: The model to use. Can be a string or a model alias.
    :param max_tokens: The maximum number of tokens to generate.
    :param randomize: Whether to randomize the system message. useful for retry functions if not satisfactory
    """
    import random

    if model in modelmap.values():
        model = model

    elif model in modelmap.keys():
        model = modelmap[model]

    if randomize:
        max_tokens = max_tokens + random.randint(128, 4000)
        _limiter = random.choice(["With Atleast", "in Utmost", "Approximately", "In Between"])
        _subinstr = random.choice(["concise", "verbose", "creative", "technical", "obedient", "analylitical", "research"])
        system = f"you are a Very {_subinstr} Assistant. Complete your responses {_limiter} Words. {system}"
        temperature = round(random.uniform(0.1, 1), 2)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]
    client = get_client()
    response = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
    # print(response)
    ai_response = response.choices[0].message.content
    return ai_response


def web_search(query):
    from playwright.sync_api import sync_playwright, expect
    import time, re

    if not query:
        return "could not perform web query, as empty query was passed in tool call"

    with sync_playwright() as p:

        browser = None
        for c in ['chrome', 'chrome-dev', 'msedge']:
            with suppress(Exception):
                browser = p.chromium.launch(headless=False, channel=c)
                break

        # Create new context and page
        context = browser.new_context(viewport={'width': 1280, 'height': 720}, java_script_enabled=True, bypass_csp=True, ignore_https_errors=True)

        page = context.new_page()
        page.goto('https://www.google.com', wait_until='domcontentloaded')
        page.fill('textarea[name="q"]', query, timeout=2000)
        page.press('textarea[name="q"]', 'Enter')
        page.wait_for_selector('div#search', state='visible', timeout=5000)

        # Open first three results in new pages
        links = []
        pages = []
        for i in range(3):
            with suppress(Exception):
                link = page.locator(f'div#rcnt div.g [jscontroller] a').nth(i)
                new_page = context.new_page()
                new_page.goto(link.get_attribute('href'), wait_until='domcontentloaded')
                pages.append(new_page)
                links.append(link.get_attribute('href'))

        # Gather text content from each page
        text_contents = []
        for link, new_page in zip(links, pages):

            text_content = new_page.query_selector_all('h1,h2,h3,h4,h5,h6,a,p,code')
            text_content = '\n'.join(set([el.inner_text() for el in text_content]))
            if text_content:
                cleaned_text = re.sub(r'<[^>]+>', '', text_content)  # Remove HTML tags
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize whitespace
                cleaned_text = cleaned_text.strip()  # Remove leading/trailing whitespace
                pruned_page = smart_chat(cleaned_text, "summarize this article/search result, keeping all points. add your analysis + observations in end")
                print("pruned", pruned_page)
                text_contents.append(f"# Source {link}\n{cleaned_text}")
            else:
                text_contents.append(f"# Source {link}\n Failed to get this source")  # element matcher failed

        # Clean up
        for new_page in pages:
            new_page.close()
        context.close()
        browser.close()

        return '\n\n'.join(text_contents)


def workspace_search(query):
    """
    Searches the workspace for relevant files and returns their content.
    """
    return "DOC 1\nLorem Ipsum"


def suggest_filename(text):
    r = smart_chat(
        text,
        "give a creative descriptive self explaining filename for the text which i provided like a blog title, journal record, just the optimal name  use emojis if required at beginning, should span 10-20 words grasping full context, always add #tags in end. do not exceed word limit",
        model="s",
        temperature=0.33,
    )
    print(r)


def save_artifact(markdown, filename=None, css=None, engine='weasyprint'):
    import requests

    if filename:
        raise NotImplementedError(
            "filename not implemented, it suggest automatically, seems more effecient than humans, sort by date to check latest generations in artifacts folder"
        )

    url = 'https://md-to-pdf.fly.dev/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://md-to-pdf.fly.dev/',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Origin': 'https://md-to-pdf.fly.dev',
    }
    if not css:
        css = 'h1, h2 {\n    color: MidnightBlue;\n}\n\ntable {\n   border-collapse: collapse;\n}\n\ntable, th, td {\n   border: 1px solid DimGray;\n}\n\nth, td {\n   text-align: left;\n   padding: 1em;\n}'
    data = {
        'markdown': markdown,
        'css': css,
        'engine': engine,
    }
    response = requests.post(url, headers=headers, data=data)
    # print(response.headers)
    return response.content


toolkit = [
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "web_search",
    #         "description": """
    #             # this function drafts an intelligent query for google search ,
    #             Use this tool to search the web for relevant, up-to-date information.
    #             It is particularly useful in the following scenarios:
    #             When the user explicitly requests information by using phrases like 'search', 'find', 'lookup', 'news', 'tell me about'.
    #             """,
    #         "parameters": {
    #             "type": "object",
    #             "properties": {"query": {"type": "string", "description": "A natural language query to search the web, SEO optimized 1 liner."}},
    #             "required": ["query"],
    #         },
    #     },
    # },
    {
        "type": "function",
        "function": {
            "name": "router",
            "description": """Main routing function for processing user queries and directing to appropriate systems. Capabilities: | Documentation Search: Processes internal doc queries using personal pronouns & doc terms | Web Search: Handles general knowledge queries based on search intent 4. System Instructions: Generates contextual prompts and guidelines Be optimistic on querying local data""",
            "parameters": {
                "type": "object",
                "properties": {
                    "system": {
                        "type": "string",
                        "description": "fine tuned system instructions 3 lines. mentions tone and specific relevant to task. inject common user preferences and obvious requirements, creative writing",
                    },
                    "web_query": {
                        "type": "string",
                        "description": "The user's query or message, redirect to online references always rewrite to make better return empty string if not applicable, be optimistic and provide a value when probability greater than 50% ",
                    },
                    "docs_query": {
                        "type": "string",
                        "description": """Query generator for internal documentation search. Processes natural language queries by identifying documentation-specific triggers (e.g. 'my', 'our', 'docs', 'guide') and technical terms. always inject few keywords to align the search """,
                    },
                },
                "required": ["system"],
            },
        },
    },
]

for tool in toolkit:
    tool['function']['description'] = tool['function']['description'].replace('\t', '').replace('    ', '')


def router(query):
    messages = [
        {
            "role": "system",
            "content": "You are a decision engine, and creates arguments based on user query. adjust to each task accordingly and maintain creativity like personal assistant",
        },
        {"role": "user", "content": query},
    ]
    with suppress(Exception):
        r0 = get_client().chat.completions.create(model=modelmap['m'], messages=messages, tools=toolkit, tool_choice="auto", temperature=0.2)
        if r0.error:
            r0 = get_client().chat.completions.create(model=modelmap['s'], messages=messages, tools=toolkit, tool_choice="auto", temperature=0.2)
            print("using mini router model")
    response = {"web_query": "", "docs_query": ""}
    if r0.choices[0].finish_reason == "tool_calls":

        response: dict[str, str] = r0.choices[0].message.tool_calls[0].function.arguments
        # r = web_search(**tool_calls[0].function.arguments)
        # print(r)
    else:
        ...
    return response


if __name__ == '__main__':
    # result = web_search('how to write a quant algo')
    # print(f"Page content:\n{result}")
    print(router("Summarize and give highlights of the last meeting with ceo "))
    print(router("Was my last support ticket for ai chip installation for the customer from acme corp resolved?"))
    # print(router("Summarize and give highlights of the last meeting with ceo "))
    # print(router("give latest trends in web development, google search"))
    print(router("Searchfor recent election news"))
