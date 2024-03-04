# slackbot.py
import os
import logging
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain import  LLMChain, PromptTemplate
from langchain.llms import Ollama
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
import subprocess
import ollama
import query_rag1
import splunklib.client as client
import splunklib.results as results
from flask import Flask, jsonify,Response

# Load environment variables from .env file
load_dotenv('.env')

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
# Initializes your app with your bot token and socket mode handler
slack_app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Langchain implementation
template = """Azeerah is a large language model trained by Ollama.

    Azeerah is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Azeerah is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

    Azeerah is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Azeerah is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

    Overall, Azeerah is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Azeerah is here to assist.

    {history}
    Human: {human_input}
    Azeerah:"""

prompt = PromptTemplate(
    input_variables=["history", "human_input"],
    template=template
)


chatgpt_chain = LLMChain(
    llm=Ollama(model="phi"), 
    prompt=prompt,
    verbose=True,
    memory=ConversationBufferWindowMemory(k=2),
)
    
retriever = None
github_process_active = False
splunk_process_active = False

@slack_app.message("github")
def handle_git_message(message, say, logger):
    global retriever, github_process_active  
    
    # Extract the text from the message
    input_text = message.get("text", "").strip().lower()
    
    # Check if the input message is "github exit"
    if input_text == "github exit":
        # Acknowledge the exit message
        say("Exiting GitHub process...")
    
        github_process_active = False
        return
     # Log the incoming message
    logger.info(message)
    # Acknowledge the message
    say("Received /git message. Initiating git process...")
    
    try:
       subprocess.run(["python", "gitloader.py"], check=True)
       subprocess.run(["python", "query_rag1.py"], check=True)
         # Check if the retriever is None
       if retriever is None:
          retriever = query_rag1.main()
       say("Please ask a question related to GitHub.")
       # Set the global variable to indicate that the GitHub process is active
       github_process_active = True
  
    except subprocess.CalledProcessError as e:
       logging.error(f"Error executing script: {e}")

def rag_chain(input_text, retriever):
    retrieved_docs = retriever.invoke(input_text)
    formatted_context = format_docs(retrieved_docs)
    return ollama_llm(input_text, formatted_context)

def format_docs(chunks):
    if isinstance(chunks[0], str):
        return "\n\n".join(chunks)
    else:
        return "\n\n".join(doc.page_content for doc in chunks)

def ollama_llm(input_text, context):
    formatted_prompt = {"role": "user", "content": f"Question: {input_text}\n\nContext: {context}"}
    response = ollama.chat(model='phi', messages=[formatted_prompt])
    print("Response received:", response)  
    
    # Check if response is a dictionary
    if isinstance(response, dict):
        print("Response is a dictionary")
        if 'message' in response and isinstance(response['message'], dict) and 'content' in response['message']:
            print("Message content found")
            message_content = response['message']['content']
            return message_content
    
    return "Unexpected response format"

# Define a handler function for app_mention events
@slack_app.event("app_mention")
def handle_app_mention_events(body, logger,say, client):
    global github_process_active,splunk_process_active 
    logger.info(body)  
    
    # Extract relevant data from the event
    event = body.get("event", {})
    channel_id = event.get("channel")

    input_text = event.get("text", "")
    if github_process_active:
        output=rag_chain(input_text,retriever)
        if input_text.strip().lower() == "github exit":
            say("Exiting GitHub process...")
            github_process_active = False
    elif splunk_process_active:
        output = read_splunk_logs(input_text)  
        if input_text.strip().lower() == "splunk exit":
            say("Exiting Splunk process...")
            splunk_process_active = False       
    else:    
        output = chatgpt_chain.predict(human_input=input_text)

    client.chat_postMessage(channel=channel_id, text=output)
    
    
 # Define a listener for message events
@slack_app.message("splunk")
def handle_splunk_message( say,message, logger):
    global  splunk_process_active 
    
    input_text = message.get("text", "").strip().lower()
    
    if input_text == "splunk exit":
           say("Exiting Splunk process...")
           splunk_process_active = False
           return
    logger.info(message)
    try:
          say(f"You said: {message['text']}.Please ask a question related to Splunk.")
          splunk_process_active = True
  
    except:
          say("Error executing script: no run")
    
# Message handler for Slack
@slack_app.message(".*")
def message_handler(message, say, logger):
    global github_process_active,splunk_process_active 
    logger.info(message)  
    input_text = message['text']
   
    if message.get("user") == os.environ.get("SLACK_BOT_USER_ID"):
        return
   
    if github_process_active:
        output=rag_chain(input_text,retriever)
        if input_text.strip().lower() == "github exit":
            say("Exiting GitHub process...")
            github_process_active = False
    elif splunk_process_active:
        output = read_splunk_logs(input_text) 
        if input_text.strip().lower() == "splunk exit":
            say("Exiting Splunk process...")
            splunk_process_active = False       
    else:    
        output = chatgpt_chain.predict(human_input=input_text)
  
    if isinstance(output, Response):
        response_data = output.response
        
        for log_entry in response_data:
            raw_log = log_entry.get("_raw")
            if raw_log:
                say(raw_log)
    else:
       say(output)
       print(output)

# Add a listener function to handle message_deleted events
@slack_app.event("message")
def handle_message_events(body, logger):
    logger.info(body)
  
# Endpoint to read Splunk logs
@app.route('/read-splunk-logs', methods=['GET'])
def read_splunk_logs(input_text):
    # Connection settings
    HOST = "localhost"
    PORT = 8089
    USERNAME = "haja"
    PASSWORD = "Haja@321"
    # Connect to Splunk
    try:
        service = client.connect(host=HOST, port=PORT, username=USERNAME, password=PASSWORD)
        print("Connection to Splunk established.")
    except Exception as e:
        return jsonify({"error": f"Failed to connect to Splunk: {str(e)}"}), 500
    
    searchquery_normal = input_text   #"search index=_internal error"
    kwargs_normalsearch = {"exec_mode": "normal"}
    job = service.jobs.create(searchquery_normal, **kwargs_normalsearch)
    while True:
        while not job.is_ready():
            pass
        if job["isDone"] == "1":
            break
 
    # Fetch results
    results_list = []
    for result in results.ResultsReader(job.results()):
        results_list.append(result)
        print(result)
        return format_splunk_results(results_list)
    
# Function to format Splunk results for Slack
def format_splunk_results(results_list):
     formatted_result = "\n".join([str(result) for result in results_list])
     return formatted_result
    
def message_handler(payload):
    try:
        message = payload["event"]
        if "text" in message:
            input_text = message["text"]
            response_data = read_splunk_logs(input_text)
            for result in response_data:
                text = result.get("_raw")  
                if text:
                    client.chat_postMessage(channel=message["channel"], text=text)
                    return text
    except Exception as e:
        print("Error:", e)
# Start the app
if __name__ == "__main__":
    # Start the Socket Mode handler
    SocketModeHandler(slack_app, os.environ["SLACK_APP_TOKEN"]).start()
    app.run(port=8081,debug=True)