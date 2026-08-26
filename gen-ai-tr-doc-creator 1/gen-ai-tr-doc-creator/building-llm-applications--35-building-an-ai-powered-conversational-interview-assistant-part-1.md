# Building an AI-Powered Conversational Interview Assistant | Part 1

**Course:** Building LLM Applications  
**Topic:** Building AI-Powered Conversational Interview Assistant and RAG Agent Using LangChain  
**Unit ID:** `7fc30fbce9a144cc836253d273878396` | **Unit Number:** 35

---

# Building an AI-Powered Conversational Interview Assistant

##Introduction

In this session, lets build an AI-powered Conversational Interview Assistant that conducts mock interviews in a realistic, interactive manner. The system asks questions, processes user responses, maintains conversational context, and generates relevant follow-up questions.

## The Problem: The Action Gap in Interviews

Have you ever gone blank during a viva, even though you studied? This is a common experience. There's a significant gap between knowing the answers and speaking them confidently under pressure.

-   **Knowing the Answers vs. Speaking Confidently**: Simply knowing information isn't enough. Articulating it clearly in a live interview is a separate skill.
 Watching Virat Kohli bat on TV won't make you a great cricketer. You need to get on the field and face the ball yourself. Similarly, passive learning doesn't prepare you for an active interview.

### Current Practice Methods and Their Limitations

-   **Practice with Friends**: They may not know the correct answers
-   **Watch YouTube Videos**: You’re not actually speaking or answering questions.
-   **Read Q&A Lists**: Memorizing answers is not the same as explaining concepts in your own words.
-   **Paid Mock Interviews**: These can be expensive and not always available.

---

## The Solution: An AI-Powered Conversational Interview Assistant

The solution is an AI-powered conversational assistant that can:

-   Ask relevant questions based on a chosen topic.
-   Listen to your answers.
-   Provide instant, constructive feedback.

### Real-World Interview Assistants

Several platforms already use this concept:

-   <a href="https://thita.ai/" target="_blank">thita.ai</a>
-   <a href="https://nxtmock-interview.ccbp.in/" target="_blank">Nxt Mock</a>

---

## What We Will Build

Let's build our own Conversational Interview Assistant with the following features:

### Key Features

-   **Multi-Subject Support**: Covers topics like Self Introduction, Generative AI, Python, English, HTML, and CSS.
-   **Conversational AI**: Asks natural, adaptive questions that reference your previous answers.
-   **Voice Interaction**: Allows you to listen to questions and record your responses verbally.
-   **Detailed Feedback**: Provides a comprehensive analysis with specific examples from your answers.
-   **Web-Based**: Works on any device with a web browser and microphone access.
-   **Fully Integrated**: A seamless flow from selecting a topic to getting feedback.

---

## Building the Conversational Interview Assistant

### Initial Code Structure and Prerequisites

Here, we are maintaining `frontend` and `backend` code in one environment: 

- `Backend`: This directory contains the code related to the backend application

- `Frontend`: This directory contains the code related to the frontend application

You will need the following prerequisites installed:


1.  VS Code
2.  Python
3.  Flask

### Functionalities to Implement

1.  **Start Interview**: When we click Start Interview, the interview should start based on selected subject
2.  **Submit Answer**: We answer the question verbally and get follow-up question
3.  **End Interview**: On clicking End Interview, we get feedback

---

### Implementing the Start Interview Functionality

After selecting a topic, when we click on the Start Interview button, the interview should start with a greeting and first question from the interviewer

### Writing the Start Interview Functionality

```python
from flask import Flask
app = Flask(__name__)

@app.route("/start-interview", methods=["POST"])
def start_interview():

app.run(debug=True, port=5000)
```

### Step 1: Send the Selected Topic to Backend

First, the frontend needs to send the chosen subject (e.g., "Python") to our backend API.

```js
const startInterviewApiUrl = "http://127.0.0.1:5000/start-interview";


async function startInterview() {
    startInterviewBtn.classList.add("hidden");
    recordBtn.classList.remove("hidden");
    recordingStatus.textContent = "Connecting...";
    
    try {
        const response = await fetch(startInterviewApiUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subject: currentSubject })
        });
        
        const contentType = response.headers.get("content-type");
        
        if (contentType && contentType.includes("text/plain")) {
            handleAudioStream(response, () => {
                endInterviewBtn.disabled = false;
            });
        } else {
            const data = await response.json();
            console.log("Question:", data.question);
            enableRecording();
            endInterviewBtn.disabled = false;
        }
    } catch (error) {
        recordingStatus.textContent = "Backend not connected";
        hideSpeakingBubble();
        recordBtn.classList.add("hidden");
        startInterviewBtn.classList.remove("hidden");
    }
}
```
Here, we are making call to `/start-interview` API with Subject and informing backend which topic to ask questions about we can access this value using the key name subject


### Step 2: Retrieve the Topic in the Backend

Now, let's access this topic in our Flask backend. The `request` object in Flask contains all information about the incoming request. We use `request.json` to read the data sent from the frontend.

```python
from flask import Flask,request

app = Flask(__name__)

@app.route("/start-interview", methods=["POST"])
def start_interview():
    data = request.json
    current_subject = data.get("subject", "Python")	

app.run(debug=True, port=5000)
```

### Step 3: Set Up the AI Agent with Memory

We need the AI to not only generate questions but also remember the conversation to ask contextual follow-ups.

#### How Memory Helps
-   **Without Memory**: The AI loses context with each turn. If you say, "Tell me more about it," it won't know what "it" refers to.
-   **With Memory**: The AI maintains the conversation history and understands follow-up questions.

We will use LangChain with `InMemorySaver` to store the conversation history.

#### Installing Required Packages

```bash
pip install langchain langgraph langchain-google-genai python-dotenv flask-cors
```

#### Setting Up API Keys Securely

Create a `.env` file to store your secret API keys. This keeps sensitive data out of your code.

```env
GOOGLE_API_KEY="your_gemini_api_key_here"
```

Now, load these keys in your Python application.

```python
from flask import Flask,request
from dotenv import load_dotenv
import os
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)

@app.route("/start-interview", methods=["POST"])
def start_interview():
    data = request.json
    current_subject = data.get("subject", "Python")    

app.run(debug=True, port=5000)
```

`load_dotenv()` reads the .env file and makes the keys available through os.getenv()

#### Initialize AI Agent with Memory

We'll use LangChain to create an agent that is configured with a Gemini model and a memory checkpointer.

```python
from flask import Flask,request
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
checkpointer = InMemorySaver()

model = init_chat_model(
    "google_genai:gemini-2.5-flash",
    api_key=GOOGLE_API_KEY
)

agent = create_agent(
    model=model,
    tools=[],
    checkpointer=checkpointer
)

app = Flask(__name__)

@app.route("/start-interview", methods=["POST"])
def start_interview():
    data = request.json
    current_subject = data.get("subject", "Python")    

app.run(debug=True, port=5000)

```


#### Tracking Interview State

We'll use global variables to track the question count, the current subject, and a `thread_id`

- The thread\_id is like a conversation ID - all messages with the same thread\_id are stored together

```python
question_count = 0
current_subject = "
thread_id = "interview_session_1"
```

#### Defining the Interviewer's Behavior

A system prompt is used to instruct the AI on how to behave.

```python
INTERVIEW_PROMPT = ""You are Natalie, a friendly and conversational interviewer conducting a natural {subject} interview.

IMPORTANT GUIDELINES:
1. Ask exactly 5 questions total throughout the interview
2. Keep questions SHORT and CRISP (1-2 sentences maximum)
3. ALWAYS reference what the candidate ACTUALLY said in their previous answer - do NOT make up or assume their answers
4. Show genuine interest with brief acknowledgments based on their REAL responses
5. Adapt questions based on their ACTUAL responses - go deeper if they're strong, adjust if uncertain
6. Be warm and conversational but CONCISE
7. No lengthy explanations - just ask clear, direct questions

CRITICAL: Read the conversation history carefully. Only acknowledge what the candidate truly said, not what you think they might have said.

Keep it short, conversational, and adaptive!""


```

The subject placeholder gets replaced with the actual topic (Python, HTML, etc.) when we use this prompt

#### Implementing Start Interview

```python
from flask import Flask,request
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

checkpointer = InMemorySaver()

model = init_chat_model(
    "google_genai:gemini-2.5-flash",
    api_key=GOOGLE_API_KEY
)

agent = create_agent(
    model=model,
    tools=[],
    checkpointer=checkpointer
)

question_count = 0
current_subject = "
thread_id = "interview_session"

INTERVIEW_PROMPT = ""You are Natalie, a friendly and conversational interviewer conducting a natural {subject} interview.

IMPORTANT GUIDELINES:
1. Ask exactly 5 questions total throughout the interview
2. Keep questions SHORT and CRISP (1-2 sentences maximum)
3. ALWAYS reference what the candidate ACTUALLY said in their previous answer - do NOT make up or assume their answers
4. Show genuine interest with brief acknowledgments based on their REAL responses
5. Adapt questions based on their ACTUAL responses - go deeper if they're strong, adjust if uncertain
6. Be warm and conversational but CONCISE
7. No lengthy explanations - just ask clear, direct questions

CRITICAL: Read the conversation history carefully. Only acknowledge what the candidate truly said, not what you think they might have said.

Keep it short, conversational, and adaptive!""


app = Flask(__name__)

CORS(app)

@app.route("/start-interview", methods=["POST"])
def start_interview():
    global question_count, current_subject, checkpointer, agent
    data = request.json
    current_subject = data.get("subject", "Python")
    question_count = 1
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer
    )
    config = {"configurable": {"thread_id": thread_id}}
    formatted_prompt = INTERVIEW_PROMPT.format(subject=current_subject)
    response = agent.invoke({
        "messages": [
            {"role": "system", "content": formatted_prompt},
            {"role": "user", "content": f"Start the interview with a warm greeting and ask the first question about {current_subject}. Keep it SHORT (1-2 sentences)."}
        ]
    }, config=config)
    question = response["messages"][-1].content
    print(f"\n[Question {question_count}] {question}")
    
app.run(debug=True, port=5000)
```

- We declare global variables to modify them in other functions, retrieve the subject from the frontend, and set question count to 1 to start the first question of a fresh interview
- We create a new agent with fresh memory, ensuring no previous conversation data carries over to the new interview
- Configure the `thread_id` to link messages, formats the prompt with our subject
- Invokes the agent to generate a greeting and first question
- Extracting the AI Responses
- Configure CORS to allow the frontend application to access backend APIs across different browsers

---

### Step 4: Send Audio Response

To make the experience conversational, we'll convert the AI's text response into spoken audio using Murf.AI's Falcon API, which is optimized for speed and real-time voice generation.

#### Why Murf.AI Falcon
Speed

- Less than **130 ms latency**, verified across **10+ geographic regions**
- Optimized for real-time voice applications

Cost

- **$0.01 per minute**
- Flat pricing at any scale — **no confusing tiers**

Language Support

- Supports **35+ languages**
- Best-in-class fluency and natural speech output

Deployment

- Edge-based deployment across **10+ global locations**
- Keeps data geographically closer for faster response times

Scalability

- Handles up to **10,000 concurrent requests**
- No performance degradation under heavy load

<MultiLineQuickTip>
The <a href="https://murf.ai/api/products/text-to-speech/Falcon" target="_blank">Falcon Text to Speech - Playground</a> allows you to experiment with:

- Different voices
- Voice types
- Language settings
- Pitch and speech variations

</MultiLineQuickTip>

<MultiLineNote>
Sign up to <a href="https://murf.ai/api/signup?utm_source=NXTWAVE26" target="_blank">Murf.AI</a> Using a new email ID not previously used on Murf AI to get $11 in free credits
</MultiLineNote>

<MultiLineNote>
In order to use Murf.AI Falcon you need to have an API key. Let's get one from <a href="https://murf.ai/api/api-keys" target="_blank">Murf.AI</a>
</MultiLineNote>

#### Understanding Streaming Audio

Instead of generating the entire audio file and then sending it, streaming sends small chunks of audio as they are generated. This significantly reduces waiting time for the user.

-   **Normal Audio**: Download the whole file, then play.
-   **Streaming Audio**: Play the first part while the next part is still downloading (like Netflix).

#### Add the Murf API Key to the `.env` file.

```env
GOOGLE_API_KEY="your_gemini_api_key_here"
MURF_API_KEY="your_murf_api_key_here"
```

#### Creating the Audio Streaming Function

We will create a `stream_audio` function that takes text, sends it to the Murf API, and yields the audio response in chunks.


```python
import requests
import json
import base64

def stream_audio(text):
    BASE_URL = "https://global.api.murf.ai/v1/speech/stream"
    payload = {
        "text": text,
        "voiceId": "en-US-natalie",
        "model": "FALCON",
        "multiNativeLocale": "en-US",
        "sampleRate": 24000,
        "format": "MP3",
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": MURF_API_KEY
    }
    response = requests.post(
        BASE_URL,
        headers=headers,
        data=json.dumps(payload),
        stream=True
    )
    for chunk in response.iter_content(chunk_size=4096):
        if chunk:
            yield base64.b64encode(chunk).decode("utf-8") + "\n"
```

- The payload configures voice settings - female US English voice, FALCON model for fast generation, and MP3 format
- We import json to format data. Headers tell Murf API we're sending JSON data and include our API key for authentication
- `stream=True` Tells the server to send data in pieces instead of waiting for the complete audio file
- The response object from Murf API contains the `iter_content()` method which reads the audio response in small 4096-byte chunks 
- `yield` enables sending audio pieces one-by-one, without waiting for all pieces
<MultiLineNote>
 Base64 converts binary data into text characters that can be safely sent over HTTP. `decode("utf-8")` converts the encoded bytes into a string
</MultiLineNote>

- We import `base64`, encode each audio chunk to text format, convert to string, and yield it. The `\n` separates chunks so frontend knows where each piece ends


#### Returning the Audio Stream from the API

Finally, we update the `start_interview` function to return a streaming `Response`. We set the `mimetype` to `text/plain` because we are sending Base64-encoded text.

```python
from flask import Flask,request
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import os
import base64
import requests
import json

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")

checkpointer = InMemorySaver()

model = init_chat_model(
    "google_genai:gemini-2.5-flash",
    api_key=GOOGLE_API_KEY
)

agent = create_agent(
    model=model,
    tools=[],
    checkpointer=checkpointer
)

question_count = 0
current_subject = "
thread_id = "interview_session"

INTERVIEW_PROMPT = ""You are Natalie, a friendly and conversational interviewer conducting a natural {subject} interview.

IMPORTANT GUIDELINES:
1. Ask exactly 5 questions total throughout the interview
2. Keep questions SHORT and CRISP (1-2 sentences maximum)
3. ALWAYS reference what the candidate ACTUALLY said in their previous answer - do NOT make up or assume their answers
4. Show genuine interest with brief acknowledgments based on their REAL responses
5. Adapt questions based on their ACTUAL responses - go deeper if they're strong, adjust if uncertain
6. Be warm and conversational but CONCISE
7. No lengthy explanations - just ask clear, direct questions

CRITICAL: Read the conversation history carefully. Only acknowledge what the candidate truly said, not what you think they might have said.

Keep it short, conversational, and adaptive!""


app = Flask(__name__)
CORS(app)


def stream_audio(text):
    BASE_URL = "https://global.api.murf.ai/v1/speech/stream"
    payload = {
        "text": text,
        "voiceId": "en-US-natalie",
        "model": "FALCON",
        "multiNativeLocale": "en-US",
        "sampleRate": 24000,
        "format": "MP3",
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": MURF_API_KEY
    }
    response = requests.post(
        BASE_URL,
        headers=headers,
        data=json.dumps(payload),
        stream=True
    )
    for chunk in response.iter_content(chunk_size=4096):
        if chunk:
            yield base64.b64encode(chunk).decode("utf-8") + "\n"



@app.route("/start-interview", methods=["POST"])
def start_interview():
    global question_count, current_subject, checkpointer, agent
    data = request.json
    current_subject = data.get("subject", "Python")
    question_count = 1
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer
    )
    config = {"configurable": {"thread_id": thread_id}}
    formatted_prompt = INTERVIEW_PROMPT.format(subject=current_subject)
    response = agent.invoke({
        "messages": [
            {"role": "system", "content": formatted_prompt},
            {"role": "user", "content": f"Start the interview with a warm greeting and ask the first question about {current_subject}. Keep it SHORT (1-2 sentences)."}
        ]
    }, config=config)
    question = response["messages"][-1].content
    print(f"\n[Question {question_count}] {question}")
    return stream_audio(question), {"Content-Type": "text/plain"}


app.run(debug=True, port=5000)

```

The frontend will receive these text chunks, decode them from Base64 back into audio, and play them, creating a seamless conversational experience.


### Final code

Download the Final code: <a href="https://nkb-backend-ccbp-media-static.s3-ap-south-1.amazonaws.com/ccbp_beta/media/content_loading/uploads/f9faf1b1-8952-4f65-b57e-33750c0f6f47_FINAL_CODE_INTERVIEW_ASSISTANT_PART%201.zip" target="_blank">Interview Assistant | Part 1</a>

---

### Murf.AI Community Support

-   **Join Murf.AI Discord Community**: <a href="https://discord.gg/CF8E9T5b6W" target="_blank">Click Here</a>
-   **Follow Murf.AI on GitHub**: <a href="https://github.com/murf-ai" target="_blank">Click Here</a>