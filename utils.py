
from chromadb import Documents, EmbeddingFunction, Embeddings

class VoyageEmbedFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        import voyageai
        # embed the documents somehow
        vo = voyageai.Client()
        result = vo.embed(documents, model="voyage-3").embeddings
        print(result)
        return embeddings

def get_client():
    import os
    from openai import OpenAI

    if not os.getenv('SAMBANOVA_API_KEY'):
        self.status_label.setText("Error: APIKEY not found in environment variables")
        raise Exception("APIKEY not found in environment variables")
    
    client = OpenAI(base_url="https://api.sambanova.ai/v1", api_key=os.getenv('SAMBANOVA_API_KEY'))
    return client

def get_first_google_result(search_term):
    from playwright.sync_api import sync_playwright, expect
    import time,re
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set headless=True for production
        
        # Create new context and page
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            java_script_enabled=True,
            bypass_csp=True,
            ignore_https_errors=True
        )
        
        page = context.new_page()
        page.goto('https://www.google.com', wait_until='domcontentloaded')
        page.fill('textarea[name="q"]', search_term, timeout=2000)
        page.press('textarea[name="q"]', 'Enter')
        page.wait_for_selector('div#search', state='visible', timeout=5000)
        first_result = page.locator('div#rcnt div.g [jscontroller] a').first
        first_result.click()
        page.wait_for_load_state('domcontentloaded')
        main_content = page.locator('main, article, #main-content, .main-content').first
        if main_content.count() > 0:
            text_content = main_content.text_content()
        else:
            # Fallback to body text if no main content area found
            text_content = page.locator('body').text_content()
        
        cleaned_text = re.sub(r'<[^>]+>', '', text_content)  # Remove HTML tags
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize whitespace
        cleaned_text = cleaned_text.strip()  # Remove leading/trailing whitespace
        
        # Clean up
        context.close()
        browser.close()
        
        return cleaned_text

def quick_chat(system,query, max_tokens=2048):
    
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]
    client = get_client()
    response = client.chat.completions.create(
        model="Meta-Llama-3.1-8B-Instruct",
        messages=messages,
        max_tokens=max_tokens,
    )
    # print(response)
    ai_response = response.choices[0].message.content
    return response

if __name__ == '__main__':
    result = get_first_google_result('new python framework launches')
    print(f"Page content:\n{result}")
    
    
