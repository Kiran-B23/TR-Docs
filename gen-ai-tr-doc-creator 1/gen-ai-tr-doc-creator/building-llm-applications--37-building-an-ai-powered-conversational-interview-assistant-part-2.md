# Building an AI-Powered Conversational Interview Assistant | Part 2

**Course:** Building LLM Applications  
**Topic:** Building AI-Powered Conversational Interview Assistant and RAG Agent Using LangChain  
**Unit ID:** `0bd49939ed704572947e07b95798cbbb` | **Unit Number:** 37

---

# Building an AI-Powered Conversational Interview Assistant | Part 2

## Introduction

In the previous session, we started building our AI-Powered Conversational Interview Assistant. We set up the basic structure and implemented the **Start Interview** functionality, where the AI greets the user and asks the first question based on the selected topic.

In this session, let's complete the application by implementing the remaining core features:

-   **Submit Answer**: We will enable the user to record their answer, convert the speech to text, have the AI agent process it, and generate a contextual follow-up question.
-   **End Interview**: We will implement the functionality to end the interview and have the AI provide structured, detailed feedback on the user's performance.

---

### Initial code

Download the Initial code: <a href="https://nkb-backend-ccbp-media-static.s3-ap-south-1.amazonaws.com/ccbp_prod/media/content_loading/uploads/6ee05b2c-be76-46ea-8a60-daa5c579eef8_INITIAL_CODE_INTERVIEW_ASSISTANT_PART%202.zip" target="_blank">Interview Assistant | Part 2</a>

 ---

## Implementing Submit Answer Functionality
When the user clicks "Submit Answer", the application needs to:
1.  Convert the user's voice recording to text.
2.  Pass the text answer to the AI agent.
3.  The agent should remember the answer and generate a relevant follow-up question.
4.  The new question is converted back to audio and streamed to the user.

### Initial Code Overview

The initial code provided already includes the frontend logic for record audio.

-   **`startRecording()`**: This function requests microphone access and starts capturing audio.

```js
function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
        const options = { mimeType: "audio/webm;codecs=opus" };
        
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            options.mimeType = "audio/webm";
        }
        
        mediaRecorder = new MediaRecorder(stream, options);
        recordingChunks = [];

        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                recordingChunks.push(e.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            recordedBlob = new Blob(recordingChunks, { type: "audio/webm" });
            stream.getTracks().forEach((track) => track.stop());
        };

        mediaRecorder.start();
        
        recordBtn.classList.remove("bg-zinc-800/80", "text-gray-400");
        recordBtn.classList.add("bg-red-500", "text-white", "recording-active");
        micIcon.classList.add("hidden");
        stopIcon.classList.remove("hidden");
        recordingStatus.textContent = "Recording...";
        submitBtn.classList.add("hidden");
        endInterviewBtn.disabled = true;
    });
}
```
-   **`stopRecording()`**: This function stops the recording and makes the "Submit Answer" button available.

```js
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        
        recordBtn.classList.remove("bg-red-500", "text-white", "recording-active");
        recordBtn.classList.add("bg-zinc-800/80", "text-gray-400");
        micIcon.classList.remove("hidden");
        stopIcon.classList.add("hidden");
        recordingStatus.textContent = "Recording complete";
        submitBtn.classList.remove("hidden");
        submitBtn.disabled = false;
    }
}
```

### Writing the Submit Answer Functionality

We'll create a new endpoint `/submit-answer` in our Flask application to handle this logic.

```python
@app.route("/submit-answer", methods=["POST"])
def submit_answer():

app.run(debug=True, port=5000)
```

The implementation will follow these steps:
1.  Receive the audio file from the frontend and convert it to text.
2.  Store the answer in agent's memory
3.  Generate the next follow-up question

---

### Step 1: Receive Audio and Convert to Text

#### Frontend: Sending Audio to the Backend

The frontend sends the recorded audio to the `/submit-answer` endpoint as a `POST` request. The audio data is sent as form data with the key `audio`.

```js
const submitAnswerApiUrl = "http://127.0.0.1:5000/submit-answer";


async function submitAnswer() {
    if (!recordedBlob) return;

    disableRecording();
    recordingStatus.textContent = "Submitting...";

    const formData = new FormData();
    formData.append("audio", recordedBlob, "answer.webm");

    try {
        const response = await fetch(submitAnswerApiUrl, {
            method: "POST",
            body: formData
        });
        
        const contentType = response.headers.get("content-type");
        const isComplete = response.headers.get('X-Interview-Complete') === 'true';
        const questionNumber = response.headers.get('X-Question-Number');
        
        if (questionNumber) {
            updateQuestionNumber(questionNumber);
        }
        
        if (contentType && contentType.includes("text/plain")) {
            handleAudioStream(response, () => {
                recordedBlob = null;
                recordingChunks = [];
                
                if (isComplete) {
                    currentAudio.onended = () => {
                        isSpeaking = false;
                        hideSpeakingBubble();
                        showFeedbackSection();
                    };
                } else {
                    endInterviewBtn.disabled = false;
                }
            });
        } else {
            const data = await response.json();
            console.log("Response:", data);
            recordedBlob = null;
            recordingChunks = [];
            
            if (isComplete) {
                showFeedbackSection();
            } else {
                enableRecording();
                endInterviewBtn.disabled = false;
            }
        }
    } catch (error) {
        recordingStatus.textContent = "Connection error";
        hideSpeakingBubble();
        enableRecording();
    }
}
```

#### Backend: Accessing Uploaded File
In Flask, we can access the uploaded file from the `request.files` object.

```python
import tempfile
from flask import request

@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    audio_file = request.files["audio"]

app.run(debug=True, port=5000)
```


#### Backend: Converting Audio to Text

- The AI cannot process audio directly. Converting speech to text allows the AI to analyze our answer, remember it, and generate contextual follow-up questions
- The audio comes as file data in memory. However, (speech-to-text service) needs a file path to read from. We must save the audio to a temporary file first

```python
from flask import request
import tempfile

@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    audio_file = request.files["audio"]
    temp_path = (
    tempfile.NamedTemporaryFile(
      delete=False,
      suffix=".webm"
     ).name
    )
    audio_file.save(temp_path)
```

<MultiLineNote>
`tempfile.NamedTemporaryFile` creates a temporary file. We use `delete=False` to prevent it from being deleted immediately, so our speech-to-text service can access it. The `.name` property gives us the path to the file.
</MultiLineNote>

#### Backend: Converting Audio to Text with AssemblyAI

Let's use **AssemblyAI** to convert the audio file into text. It's a powerful AI service for speech-to-text transcription.

#### Features of AssemblyAI

- **Speech-to-Text (STT)** : Converts spoken words in an audio file into text
- **Multilingual Support** : Supports multiple languages
- **Sentiment Analysis** : Analyzes the emotional tone of spoken content, determining whether the sentiment is positive, negative, or neutral

#### Installing the AssemblyAI Python SDK:

- Python has a third party package called Assembly AI allowing us to transcribe audio files into text

```bash
pip install assemblyai
```

Next, get your API key from the <a href="https://www.assemblyai.com/" target="_blank">AssemblyAI website</a> and add it to your `.env` file.

```env
GOOGLE_API_KEY="your_gemini_api_key_here"
MURF_API_KEY="your_murf_api_key_here"
ASSEMBLYAI_API_KEY="your_assemblyai_api_key_here"
```

Now, let's set it up in our application and create a function to handle the transcription.

- AssemblyAI provides several methods & configuration options to interact

    - transcribe()
    - get_transcript()
    - sentiment_analysis
    - auto_highlights

```python
import assemblyai as aai
import os

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
aai.settings.api_key = ASSEMBLYAI_API_KEY

def speech_to_text(audio_path):
    ""Converts an audio file to text using AssemblyAI.""
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(
        speech_models=["universal-3-pro", "universal-2"],
        language_detection=True, speaker_labels=True,
    )
    transcript = transcriber.transcribe(audio_path, config=config)
    return transcript.text if transcript.text else "
```

#### Calling The Speech To Text Function

```python
from flask import Flask,request
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import assemblyai as aai
import os
import base64
import requests
import json
import tempfile


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
aai.settings.api_key = ASSEMBLYAI_API_KEY

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

def speech_to_text(audio_path):
    ""Converts an audio file to text using AssemblyAI.""
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(
        speech_models=["universal-3-pro", "universal-2"],
        language_detection=True, speaker_labels=True,
    )
    transcript = transcriber.transcribe(audio_path, config=config)
    return transcript.text if transcript.text else "


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


@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    global question_count
    audio_file = request.files["audio"]
    audio_file = request.files["audio"]
    temp_path = (
        tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".webm"
        ).name
    )
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = "Empty Text received"
    print(f"[Answer {question_count}] {answer}")

app.run(debug=True, port=5000)
```
- We call our function with the saved audio path to get the transcribed text
- After transcription, we delete the temporary file using os.unlink() to free up space. If transcription is empty, we provide a fallback message

---

### Step 2: Store the answer in agent's memory

#### Storing the Answer in Memory

Now that we have the text `answer`, we need to store it in our LangChain agent's memory. This is crucial for the agent to have context about the conversation. We use the same `thread_id` to ensure the answer is added to the correct conversation history.

```python
@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    audio_file = request.files["audio"]
    temp_path = (
    tempfile.NamedTemporaryFile(
      delete=False,
      suffix=".webm"
     ).name
    )
    audio_file.save(temp_path)
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = "Empty Text received"
    print(f"[Answer {question_count}] {answer}")
    config = {"configurable": {"thread_id": thread_id}}
   
    agent.invoke({"messages": [{"role": "user", "content": answer}]}, config=config)
```
---

### Step 3: Generate the next follow-up question

#### Generating the Next Adaptive Question

With the answer stored in memory, we can now prompt the AI to generate a relevant follow-up question. We will also increment our `question_count`.

- This prompt instructs the AI to look at our actual answer (stored in memory) and ask a relevant follow-up question

    ```
    The candidate just answered question {question_count - 1}.
     
        Look at their ACTUAL answer above. Do NOT assume or make up what they said.
        
        Now ask question {question_count} of 5:
        1. Briefly acknowledge what they ACTUALLY said (1 sentence) - quote their exact words if needed
        2. Ask your next question that builds on their REAL response (1-2 sentences)
        3. If they said "I don't know" or gave a wrong answer, acknowledge that and ask something simpler
        4. Keep the TOTAL response under 3 sentences
        
        Be conversational but CONCISE. Only reference what they truly said.
    ```

```python
@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    global question_count
    audio_file = request.files["audio"]
    temp_path = (
    tempfile.NamedTemporaryFile(
      delete=False,
      suffix=".webm"
     ).name
    )
    audio_file.save(temp_path)
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = "Empty Text received"
    print(f"[Answer {question_count}] {answer}")
    config = {"configurable": {"thread_id": thread_id}}
   
    agent.invoke({"messages": [{"role": "user", "content": answer}]}, config=config)


    question_count += 1
    prompt = f""The candidate just answered question {question_count - 1}.
 
    Look at their ACTUAL answer above. Do NOT assume or make up what they said.
    
    Now ask question {question_count} of 5:
    1. Briefly acknowledge what they ACTUALLY said (1 sentence) - quote their exact words if needed
    2. Ask your next question that builds on their REAL response (1-2 sentences)
    3. If they said "I don't know" or gave a wrong answer, acknowledge that and ask something simpler
    4. Keep the TOTAL response under 3 sentences
    
    Be conversational but CONCISE. Only reference what they truly said.""
    response = agent.invoke({"messages": [{"role": "user", "content": prompt}]}, config=config)
    question = response["messages"][-1].content
    print(f"\n[Question {question_count}] {question}")
```

- We declare global question_count to increment it when generating the next question
- We increment the count so the AI knows which question number to ask next

Now we've generated the next question. We need to send it to the frontend with the question number so it can track which question we're on.

#### Understanding Custom Headers

HTTP headers are like labels on a package they provide extra information about the response. Custom headers let us send additional data alongside the main content

- Standard Headers (built-in):
    - Content-Type - What kind of data? (text, audio, JSON)
    - Content-Length - How big is the data?
- Custom Headers (we create):
    - Let’s us send extra information alongside the main content
    - The X - prefix indicates a custom header

#### Return Audio Response

The stream_audio() function converts text to speech by calling the Murf.AI API, generating audio chunks that stream immediately to the frontend

```python
from flask import Response

@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    global question_count
    audio_file = request.files["audio"]
    temp_path = (
    tempfile.NamedTemporaryFile(
      delete=False,
      suffix=".webm"
     ).name
    )
    audio_file.save(temp_path)
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = "Empty Text received"
    print(f"[Answer {question_count}] {answer}")
    config = {"configurable": {"thread_id": thread_id}}
   
    agent.invoke({"messages": [{"role": "user", "content": answer}]}, config=config)


    question_count += 1
    prompt = f""The candidate just answered question {question_count - 1}.
 
    Look at their ACTUAL answer above. Do NOT assume or make up what they said.
    
    Now ask question {question_count} of 5:
    1. Briefly acknowledge what they ACTUALLY said (1 sentence) - quote their exact words if needed
    2. Ask your next question that builds on their REAL response (1-2 sentences)
    3. If they said "I don't know" or gave a wrong answer, acknowledge that and ask something simpler
    4. Keep the TOTAL response under 3 sentences
    
    Be conversational but CONCISE. Only reference what they truly said.""
    response = agent.invoke({"messages": [{"role": "user", "content": prompt}]}, config=config)
    question = response["messages"][-1].content
    print(f"\n[Question {question_count}] {question}")
    return (stream_audio(question),
        {
        'Content-Type': 'text/plain',
        'X-Question-Number': str(question_count)
        }
    )
```

<MultiLineQuickTip>
**Why use Headers?** Headers are sent and read by the browser *before* the response body. This allows the frontend to immediately update the UI (e.g., "Question 2 of 5") while the audio is still loading and streaming.
</MultiLineQuickTip>

#### CORS Configuration

By default, browsers restrict access to custom headers for security reasons. We need to explicitly allow our frontend to read the `X-Question-Number` header by updating our CORS configuration.

```python
from flask import Flask,request,jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import assemblyai as aai
import os
import base64
import requests
import tempfile

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
aai.settings.api_key = ASSEMBLYAI_API_KEY
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

FEEDBACK_PROMPT = ""Based on our complete interview conversation, provide detailed feedback as JSON only:
    {{
    "subject": "<topic>",
    "candidate_score": <1-5>,
    "feedback": "<detailed strengths with specific examples 
    from their ACTUAL answers>",
    "areas_of_improvement": "<constructive suggestions based 
    on gaps you noticed>"
    }}
    Be specific - reference ACTUAL things they said during the interview.""


app = Flask(__name__)
CORS(app, expose_headers=['X-Question-Number'])

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

def speech_to_text(audio_path):
  ""Convert audio file to text using AssemblyAI""
  transcriber = aai.Transcriber()
  config = aai.TranscriptionConfig(
        speech_models=["universal-3-pro", "universal-2"],
        language_detection=True, speaker_labels=True,
    )
  transcript = transcriber.transcribe(audio_path, config=config)
  return transcript.text if transcript.text else "



@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    global question_count
    audio_file = request.files["audio"]
    temp_path = (
    tempfile.NamedTemporaryFile(
      delete=False,
      suffix=".webm"
     ).name
    )
    audio_file.save(temp_path)
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = "Empty Text received"
    print(f"[Answer {question_count}] {answer}")
    config = {"configurable": {"thread_id": thread_id}}
   
    agent.invoke({"messages": [{"role": "user", "content": answer}]}, config=config)


    question_count += 1
    prompt = f""The candidate just answered question {question_count - 1}.
 
    Look at their ACTUAL answer above. Do NOT assume or make up what they said.
    
    Now ask question {question_count} of 5:
    1. Briefly acknowledge what they ACTUALLY said (1 sentence) - quote their exact words if needed
    2. Ask your next question that builds on their REAL response (1-2 sentences)
    3. If they said "I don't know" or gave a wrong answer, acknowledge that and ask something simpler
    4. Keep the TOTAL response under 3 sentences
    
    Be conversational but CONCISE. Only reference what they truly said.""
    response = agent.invoke({"messages": [{"role": "user", "content": prompt}]}, config=config)
    question = response["messages"][-1].content
    print(f"\n[Question {question_count}] {question}")
    return (stream_audio(question),
        {
        'Content-Type': 'text/plain',
        'X-Question-Number': str(question_count)
        }
    )


app.run(debug=True, port=5000)
```

#### Frontend: Reading the Custom Header

The frontend JavaScript can easily read this header from the `fetch` response.

```js
const submitAnswerApiUrl = "http://127.0.0.1:5000/submit-answer";


async function submitAnswer() {
    if (!recordedBlob) return;

    disableRecording();
    recordingStatus.textContent = "Submitting...";

    const formData = new FormData();
    formData.append("audio", recordedBlob, "answer.webm");

    try {
        const response = await fetch(submitAnswerApiUrl, {
            method: "POST",
            body: formData
        });
        
        const contentType = response.headers.get("content-type");
        const isComplete = response.headers.get('X-Interview-Complete') === 'true';
        const questionNumber = response.headers.get('X-Question-Number');
        
        if (questionNumber) {
            updateQuestionNumber(questionNumber);
        }
        
        if (contentType && contentType.includes("text/plain")) {
            handleAudioStream(response, () => {
                recordedBlob = null;
                recordingChunks = [];
                
                if (isComplete) {
                    currentAudio.onended = () => {
                        isSpeaking = false;
                        hideSpeakingBubble();
                        showFeedbackSection();
                    };
                } else {
                    endInterviewBtn.disabled = false;
                }
            });
        } else {
            const data = await response.json();
            console.log("Response:", data);
            recordedBlob = null;
            recordingChunks = [];
            
            if (isComplete) {
                showFeedbackSection();
            } else {
                enableRecording();
                endInterviewBtn.disabled = false;
            }
        }
    } catch (error) {
        recordingStatus.textContent = "Connection error";
        hideSpeakingBubble();
        enableRecording();
    }
}
```

---

## Implementing End Interview Functionality

When the user clicks "End Interview," the agent should review the entire conversation history and provide comprehensive feedback.

### Updating the GetFeedback API URL

```js
const getFeedbackApiUrl = "http://127.0.0.1:5000/get-feedback";

async function getFeedback() {
    showFeedbackSection();
    getFeedbackBtn.textContent = "Generating...";
    getFeedbackBtn.disabled = true;

    try {
        const response = await fetch(getFeedbackApiUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayFeedback(data.feedback);
        }
    } catch (error) {
        getFeedbackBtn.textContent = "Error - Retry";
        getFeedbackBtn.disabled = false;
    }
}
```

### Writing the Get Feedback Backend

We'll create a `/get-feedback` endpoint to handle this.

```python
@app.route("/get-feedback", methods=["POST"])
def get_feedback():

```

### Step 1: Define feedback format

To ensure the frontend can easily display the feedback, we'll instruct the AI to provide it in a structured JSON format.

Here is the prompt we will use for feedback:

```python
FEEDBACK_PROMPT = ""Based on our complete interview conversation, provide detailed feedback.
IMPORTANT: You MUST respond with ONLY a valid JSON object. No other text before or after.
Address the candidate directly using "you" and "your" (e.g., "You explained..." not "The candidate explained...").
Respond with ONLY this JSON structure (no markdown, no code blocks, no extra text):
{{
    "subject": "{subject}",
    "candidate_score": <1-5>,
    "feedback": "<detailed strengths with specific examples from their ACTUAL answers>",
    "areas_of_improvement": "<constructive suggestions based on gaps you noticed>"
}}
Be specific - reference ACTUAL things they said during the interview.""
```

<MultiLineNote>
The double braces `{{` and `}}` are used in the Python f-string so that they become single braces in the final prompt.
</MultiLineNote>

The frontend requires specific fields (score, feedback, suggestions) for proper UI display: score in the circle, feedback in strengths, suggestions in improvements—inconsistent formats break the display

### Step 2: Generate feedback using conversation memory

We invoke the agent one last time, using the same `thread_id` so it can access the entire conversation.

```python

@app.route("/get-feedback", methods=["POST"])
def get_feedback():
    ""Generate detailed interview feedback""
    config = {"configurable": {"thread_id": thread_id}}
    response = agent.invoke({
        "messages": [
        {
            "role": "user", 
            "content": f"{FEEDBACK_PROMPT}\n\nReview our complete {current_subject} interview conversation and provide detailed feedback."
        }
        ]
    }, config=config)
    text = response["messages"][-1].content
    print(f"\n[Feedback Generated]\n{text}\n")

```

### Step 3: Parse and return response

The AI's response is a string that should contain JSON. We need to clean it up (in case it's wrapped in markdown code blocks) and return it as a proper JSON response to the frontend.

```python

import json
from flask import jsonify

@app.route("/get-feedback", methods=["POST"])
def get_feedback():
    cleaned_text = feedback_text.strip()
    if " in cleaned_text:
        cleaned_text = cleaned_text.split(")[1].replace("json", ").strip()

    feedback_json = json.loads(cleaned_text)
    

    return jsonify({"success": True, "feedback": feedback_json})
```

- strip() removes extra whitespace. If code blocks exist, we extract just the JSON content
- Sometimes the AI wraps JSON in markdown code blocks like \``` json ... \```. We must remove.
- jsonify() converts our dictionary to a JS