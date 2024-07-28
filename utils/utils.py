from utils.minitube import *
import sys, fitz
import subprocess
import pandas as pd
import functools
from urllib.request import urlopen, Request, HTTPError
import asyncio
from bs4 import BeautifulSoup
import typing
import tiktoken
import openai
from dotenv import load_dotenv
import time
import logging

load_dotenv()
# get API key from top-right dropdown on OpenAI website
openai.api_key =  os.getenv('OPENAPI_API_KEY')


def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper




def extract_urls(text):
    # Regular expression pattern to match URLs
    url_pattern = re.compile(r'\bhttps?://\S+')

    # Find all matches in the text
    urls = re.findall(url_pattern, text)

    return urls


def remove_newlines(serie):
    serie = serie.replace('\n', ' ')
    serie = serie.replace('\\n', ' ')
    serie = serie.replace('  ', ' ')
    serie = serie.replace('  ', ' ')
    return serie


def process_long_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:  # iterate the document pages
        text += page.get_text()  # get plain text (is in UTF-8)
    return text

def download_file(url, local_folder):
    # Transform GitHub URL to raw URL if necessary
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

    filename = url.split('/')[-1]
    filepath = os.path.join(local_folder, filename)
    subprocess.run(["curl", "-L", "-o", filepath, url])  # '-L' to follow redirects
    return filepath


def download_pdf(url, folder='pdfs/'):
    # Check if the folder exists, if not, create it
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Get the file name from the URL
    file_name = url.split('/')[-1]

    # Check if the file is a PDF
    if not file_name.endswith('.pdf'):
        print(f"URL '{url}' does not point to a PDF file.")
        return

    file_path = download_file(url, folder)
    print(f"PDF file downloaded at {file_path}")


    doc = fitz.open(file_path)
    text = ""
    for page in doc:  # iterate the document pages
        text += page.get_text()  # get plain text (is in UTF-8)
    return text


def get_content_url(url,stored=False,debug=False):

    csv_file = 'blogs/scraped.csv' 
    
   
    if os.path.exists(csv_file) and stored:
        
        existing_data = pd.read_csv(csv_file)
        if url in existing_data['url'].values:
            print(f"URL '{url}' already exists in the CSV file.")
            return existing_data.loc[existing_data['url'] == url, 'text'].iloc[0]

    logging.info(f"Get data from  {url}")
    
    if url.endswith(".pdf"):
        text = download_pdf(url)
        logging.info("Processing pdf file")
    elif "youtube" in url or "youtu.be" in url:
        logging.info("Processing youtube video")
        text = get_content_from_youtube_url(url)
    else:
        logging.info("Processing normal url")
        result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)

        if debug:
            print(result.stdout)

        soup = BeautifulSoup(result.stdout, "html.parser")
        text = soup.get_text()


    if text:
        text = remove_newlines(text)

        # If the file exists, read the contents
        if stored:
                new_data = pd.DataFrame([(url, text)], columns=['url', 'text'])
                # Update the CSV with the new data
                new_data.to_csv(csv_file, mode='a', header=False, index=False)
    return text



async def send_long_message(channel, answer):
    chunk_size = 2000
    chunks = [answer[i:i + chunk_size] for i in range(0, len(answer), chunk_size)]
    for chunk in chunks:
        await channel.send(chunk)

def get_all_urls():
    csv_file = 'blogs/scraped.csv'
    
    # Check if the CSV file exists
    if not os.path.exists(csv_file):
        print("CSV file does not exist.")
        return []
    else:
        # If the file exists, read the contents
        existing_data = pd.read_csv(csv_file)
        
        # Return a list of all URLs in the 'fname' column
        return existing_data['url'].tolist()

def split_into_many(text, max_tokens = 800):
    tokenizer = tiktoken.get_encoding("cl100k_base")

    # Split the text into sentences
    sentences = text.split('. ')
    # Get the number of tokens for each sentence
    n_tokens = [len(tokenizer.encode(" " + sentence)) for sentence in sentences]
    chunks = []
    tokens_so_far = 0
    chunk = []
    print(sum(n_tokens))
    # Loop through the sentences and tokens joined together in a tuple
    for sentence, token in zip(sentences, n_tokens):

        # If the number of tokens so far plus the number of tokens in the current sentence is greater 
        # than the max number of tokens, then add the chunk to the list of chunks and reset
        # the chunk and tokens so far
        if tokens_so_far + token > max_tokens:
            chunks.append(". ".join(chunk) + ".")
            chunk = []
            tokens_so_far = 0

        # If the number of tokens in the current sentence is greater than the max number of 
        # tokens, go to the next sentence
        if token > max_tokens:
            continue

        # Otherwise, add the sentence to the chunk and add the number of tokens to the total
        chunk.append(sentence)
        tokens_so_far += token + 1
    if chunks == []:
        chunks = [text]
    print(chunks)

    return chunks



def count_token(text):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    sentences = text.split('. ')

    # Get the number of tokens for each sentence
    n_tokens = [len(tokenizer.encode(" " + sentence)) for sentence in sentences]
    # sum all item in array n_tokens
    return sum(n_tokens)

def get_answer_api(prompt, msgs = None,max_token=2000):
    if msgs == None:
        mssgs = [{"role": "system", "content": "You are expert in software security and vulnerability finding."},{"role": "user", "content": prompt}]
    else:
        mssgs = msgs 
        mssgs.append({"role": "user", "content": prompt})

    # Use OpenAI's ChatCompletion API to get the chatbot's response
    token_len = 0
    for msg in mssgs:
        cur_tokens = count_token(msg["content"])
        print(f"{cur_tokens} .   " + msg["content"][:50])
        token_len += cur_tokens
    print("API Prompt Token Len:", token_len)
    while True:
        try:
            response = openai.ChatCompletion.create(
                # model="gpt-3.5-turbo",  # The name of the OpenAI chatbot model to use
                model="gpt-4-1106-preview",  # The name of the OpenAI chatbot model to use
                messages=mssgs,  # The conversation history up to this point, as a list of dictionaries
                max_tokens=max_token,        # The maximum number of tokens (words or subwords) in the generated response
                stop=None,              # The stopping sequence for the generated response, if any (not used here)
                temperature=0,        # The "creativity" of the generated response (higher temperature = more creative)
            )
            break # Exit the loop if the API call succeeds
        except Exception as e:
            # If the API call fails, wait and retry after a delay
            print("API error:", e)
            if "You can find your API key at" in str(e):
                return str(e)
                break

            print("Retrying in 10 seconds...")
            time.sleep(30)
    
    # Find the first response from the chatbot that has text in it (some responses may not have text)
    print(response.choices)
    for choice in response.choices:
        if "text" in choice:
            return choice.text
    return response.choices[0].message.content



@to_thread
def blog_retrieve(query, content,isvr=True,bot=None):
    if count_token(content) < 40000:
        # chunks = [content]
        prompt=f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {content}\n\n---\n\nQuestion: {query}\nAnswer:"        
        answer = get_answer_api(prompt)
        open("prompt.txt", "a").write("\n\n====\n\n" + prompt + "\n\n====\n\n" + answer + "\n\n====\n\n")
        return answer,""

    else:
        chunks = split_into_many(content,40000)
    
    assistant = "You are a helpful assistant\n"
    if isvr:
        assistant = "You are expert in software security and vulnerability finding\n"
    template = """Please follow the template example below to answer the question:
    Example 1:
    Question:
    The original question is as follows: What is the capital of France?
    We have provided an existing answer: Paris
    We have the opportunity to refine the existing answer (only if needed) with some more context below. Refine the original answer to better answer the question. If the existing answer is already correct and the context doesn't require any refinement, simply restate the existing answer.
    The context is about the European Union's political capital.
    New Answer:
    Paris
    ----------------------------------------------------------
    Example 2:
    Question:
    The original question is as follows: What is the capital of France?
    We have provided an existing answer: Brussels
    We have the opportunity to refine the existing answer (only if needed) with some more context below. Refine the original answer to better answer the question. If the context provides the correct information to refine the answer, incorporate the context in the new answer.
    The context is about the capital of France is Paris.
    New Answer:
    Paris"""
    prompt_start = (
        
        "\n\n The original question is as follows: {query_str}\n"
        "We have provided an existing answer: {existing_answer}\n"
        "We have the opportunity to refine the existing answer (only if needed) with some more context below. Refine the original answer to better answer the question. If the context provides the correct information to refine the answer, incorporate the context in the new answer.\n"
        )
        
    prompt_end = (
        "Given the new context, refine the original answer to better answer the question. "
        "If the context isn't useful, just answer using the original answer."
        )
    existing_answer = "" 
    all_answer = []
    print(f"===========\nRetrieving: {count_token(content)}  Chunk: {len(chunks)}")
    i = 0
    total = len(chunks)
    for chunk in chunks:
        prompt = (
                template + prompt_start.format(query_str=query, existing_answer=existing_answer) + "\n\n====\n\n" + chunk + "\n\n====\n\nNew Answer:"   
            )
        print(f"===========\n {i}/{total} . No Tokens Prompt:{count_token(prompt)} Existing Answer: {count_token(existing_answer)} Chunk: {count_token(chunk)}")
        try:
            mssgs = None
            
            existing_answer = get_answer_api(prompt, mssgs)
        except Exception as e:
            print(e)
            break
        # print(existing_answer)
        open("prompt.txt", "a").write("\n\n====\n\n" + prompt + "\n\n====\n\n" + existing_answer + "\n\n====\n\n")
        all_answer.append(existing_answer)
        i+=1
    return existing_answer,all_answer
