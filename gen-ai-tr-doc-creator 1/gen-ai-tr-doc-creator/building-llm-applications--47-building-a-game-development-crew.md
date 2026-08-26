# Building a Game Development Crew

**Course:** Building LLM Applications  
**Topic:** Building Multi Agent Systems and LLM Evaluation  
**Unit ID:** `4b9b9034008944af935a3fa395aa7536` | **Unit Number:** 47

---

# Introduction

In our previous session, we learned about Multi-Agent Systems, their key characteristics, and CrewAI's core components — Agents, Tasks, and Crew.

Now in this unit, we will build a Game Development Crew using CrewAI — creating specialized AI agents, defining tasks, assembling the crew, and executing it to turn a game idea into a playable prototype.

>**Quick Question**
> Have you ever played a video game and thought, "I want to make my own game!"?


##Building a Game Development Crew

Imagine You have a brilliant game idea. You can see the characters, you know how you want your game to be. But turning that vision into a playable prototype requires a team, specialized skills, and a lot of time.

<b>Brilliant Game Idea → Assemble Team → Develop Prototype → Deploy Prototype</b>

###High-Performance Game
For a Simple Game, You Typically Need

*   **Game Designer** — Creates game concepts and designs from the given idea
*   **Software Engineer** — Figures out logic and writes actual game code
*   **QA Engineer** — Tests and finds bugs

Instead of hiring 3 people, you can create 3 AI agents, each specialized in one role. They communicate, collaborate, and complete tasks just like a real team!

### What to Achieve?

**Our Goal:** Create a crew/team of AI agents that can design and plan a simple 2D platformer/jumper game.

**Our Team Structure:**

*   **Game Designer Agent** — Creative mind
*   **Software Engineer Agent** — Technical brain
*   **QA Engineer Agent** — Quality checker

### Initial Code

- <a href="https://colab.research.google.com/drive/1WQjLfKNpDZf6bVmQEnMnLXhb6bwNvjZ0#scrollTo=EpyaeIDlIr99" target="_blank">Building a Game Development Crew initial code</a>

##Steps to Build Game Development Crew

1.  Creating Agents
2.  Defining Tasks
3.  Assembling the Crew
4.  Executing the Crew

## Step 1: Creating Agents

### Creating Agents in CrewAI

There are two ways to create agents in CrewAI:

*   Using YAML Configuration File
*   Defining directly in code

Let's see how we can define agents in Python.

### Creating Agents - Syntax

```
sample_agent = Agent(
    role="Title of the agent",
    goal="The objective the agent must achieve",
    backstory="Context that shapes behavior, tone, and decisions",
    tools=[],
    llm=Model to be used (Current default is OpenAI's GPT-4),
    verbose=True/False (Shows agent's reasoning and steps)
)
```
###Creating Agent for Game Designer

```python
game_designer = Agent(
    role="Creative Game Designer",
    goal="Come up with fun, feasible game concepts and detailed mechanics based on user idea",
    backstory=
      "You are an experienced game designer."
      "You excel at turning vague ideas into clear, exciting game designs including:"
      "- core loop, rules, win/lose conditions"
      "- basic entities (player, enemies, items)"
      "- controls and feel"
      "Keep it simple enough to implement in pure Python + Pygame in one file.",
    verbose=True,
    llm=llm,
)
```

- Since no tools are required for designing a game, we haven’t provided any tools
- The model to be used currently defaults to GPT-4

Let’s see how we can integrate Gemini LLM

### Integrating Different LLMs

**<a href="https://www.crewai.com" target="_blank">CrewAI </a>**allows us to integrate with multiple LLM providers:

* **<a href="https://openai.com/" target="_blank">GPT (OpenAI)</a>**
* **<a href="https://gemini.google.com/app" target="_blank">Gemini (Google)</a>**
* **<a href="https://www.llama.com/models/llama-3/" target="_blank">LLaMA 3 (Meta)</a>**
* **<a href="https://claude.ai/" target="_blank">Claude (Anthropic)</a>**


### Integrating Google Gemini Models

CrewAI provides integration with Google Gemini through the Python package named Google GenAI.

```bash
!pip install "crewai[google-genai]"
```

### Defining LLM

CrewAI provides an `LLM` class that allows us to integrate different models.

```python
from crewai import Agent, LLM

llm = LLM(
    model="gemini/gemini-2.5-flash",
)
```

### Storing API Keys

Store the Gemini API key in Colab Secrets:

```python
from crewai import Agent, LLM
from google.colab import userdata

gemini_api_key = userdata.get('GEMINI_API_KEY')

llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=gemini_api_key
)
```

### Providing LLM to Agent

```python
from crewai import Agent,LLM
from google.colab import userdata

gemini_api_key = userdata.get('GEMINI_API_KEY')


llm = LLM(
   model="gemini/gemini-2.5-flash",
   api_key=gemini_api_key
)

game_designer = Agent(
    role="Creative Game Designer",
    goal="Come up with fun, feasible game concepts and detailed mechanics based on user idea",
    backstory=
      "You are an experienced game designer."
      "You excel at turning vague ideas into clear, exciting game designs including:"
      "- core loop, rules, win/lose conditions"
      "- basic entities (player, enemies, items)"
      "- controls and feel"
      "Keep it simple enough to implement in pure Python + Pygame in one file.",
    verbose=True,
    llm=llm,
)
```

### Creating Agent for Software Engineer
```python
senior_engineer = Agent(
   role="Senior Python Game Developer",
   goal="Write clean, working Python code (using Pygame) for the described game",
    backstory=
        "You are a senior software engineer specialized in Python game development with Pygame."
        "You write structured, readable code with:"
        "- Proper game loop, event handling, drawing"
        "- Comments explaining key parts"
        "- Error handling where needed"
        "You always produce a complete, runnable .py file.",
   verbose=True,
   llm=llm,
)
```



Developers excel at problem-solving, not memorization. When stuck, they refer to official documentation. So let's provide a search tool to our software engineer agent.

### CrewAI Tools

Similar to LangChain, CrewAI also provides a suite of built-in tools which we can provide to Agents to enhance their capabilities.

CrewAI supports tools from:

*   CrewAI Toolkit
*   LangChain Tools

### Installing CrewAI Tools

```bash
!pip install 'crewai[tools]'
```

Some available tools:

* <a href="https://serper.dev/" target="_blank">SerperDev Tool</a> — Allows the agent to fetch up-to-date information from the internet  
* <a href="https://docs.crewai.com/en/tools/ai-ml/dalletool" target="_blank">DALL·E Tool</a> — Creates images based on text descriptions  
* <a href="https://docs.crewai.com/en/tools/file-document/filereadtool" target="_blank">File Search / FileRead Tool</a> — Retrieves information from uploaded files or external knowledge sources  

### Integrating SerperDev Tool

SerperDev tool allows AI agents to perform real-time Google search and access current information from the web.

```python
from crewai_tools import SerperDevTool

search_tool = SerperDevTool()
```

Store the Serper API key in Colab Secrets. Get the API key from - <a href="https://serper.dev/" target="_blank">Serper.dev</a>

### Providing Tools to the Software Engineer Agent

```python
from crewai_tools import SerperDevTool

serper_api_key = userdata.get('SERPER_API_KEY')

search_tool = SerperDevTool(api_key=serper_api_key)


senior_engineer = Agent(
   role="Senior Python Game Developer",
   goal="Write clean, working Python code (using Pygame) for the described game",
    backstory=
        "You are a senior software engineer specialized in Python game development with Pygame."
        "You write structured, readable code with:"
        "- Proper game loop, event handling, drawing"
        "- Comments explaining key parts"
        "- Error handling where needed"
        "You always produce a complete, runnable .py file.",
   verbose=True,
   llm=llm,
)
```


### Creating QA Agent

```python
qa_engineer = Agent(
    role="QA Engineer & Code Reviewer",
    goal="Test, review, and improve the code for bugs, playability, and completeness",
    backstory=
        "You are a meticulous QA engineer and code reviewer."
        "You carefully check:"
        "- Does the code run without errors?"
        "- Does it implement ALL the designed features?"
        "- Is it fun/playable? Any obvious balance issues?"
        "- Code style, variable names, comments"
        "Suggest fixes or small improvements and output the FINAL improved code.",
    verbose=True,
    llm=llm,
)

```

## Step 2: Defining Tasks

In the CrewAI framework, a Task is a specific assignment completed by an Agent. Each task should have:

*   **Description** — What needs to be done
*   **Agent** — Who will do this task
*   **Expected Output** — What the final result should look like

### Creating Tasks in CrewAI

There are two ways to define tasks:

*   Defining through YAML file
*   Defining directly in code

### Creating Tasks - Syntax

```python
research_task = Task(
    description=",
    expected_output=",
    agent=researcher
)
```

### Creating Task for Game Designer

```python
from crewai import Task

task_design = Task(
    description=
        "Take the user's game idea: {game_idea}"
        "1. Clarify and expand it into a fun, simple 2D game"
        "2. Describe: objective, controls, entities, win/lose"
        "3. Keep scope small (one level, basic mechanics)"
        "Output format:"
        "## Game Design Document"
        "- Title: ..."
        "- Genre: ..."
        "- Objective: ..."
        "- Controls: ..."
        "- Entities: ..."
        "- Mechanics: ...",
    expected_output="A clear markdown Game Design Document",
    agent=game_designer
)
```

**Note:** Description here is not a formatted string. `{game_idea}` will be given later and managed by CrewAI.

### Creating Task for Software Engineer

How does the Engineer know what the Designer has created?

```python
task_code = Task(
    description=
        "Using the game design from the previous task"
        "Write a COMPLETE, standalone Python script using Pygame that implements the game."
        "- Include import pygame, sys, random (if needed)"
        "- Full game loop, init, events, update, draw"
        "- Make it runnable with python game.py"
        "- Add simple comments"
        "- The main game loop must be exposed in the python code, it should not be inside any function like main"
        "- Final answer MUST be ONLY the Python code and Instructions on how to play the game",
    expected_output="A complete runnable Pygame Python script",
    agent=senior_engineer,
    context=[task_design]
)
```

### The Context Parameter

Tasks accept a parameter called `context` which allows us to pass the output from previous tasks as input to the current one. It's how the team shares information and builds on each other's work.

### Creating Task for QA Engineer

For final review, the QA engineer receives both the design document and the code via the context list.

```python
task_review = Task(
    description=
        "Review the Python code from the previous task."
        "1. Check for syntax/runtime errors"
        "2. Verify it matches the design document"
        "3. Test mentally: does it have init, loop, quit handling, drawing?"
        "4. Suggest fixes/improvements if needed"
        "5. Output the FINAL, improved, ready-to-run code"
        "Your final answer MUST be ONLY the complete Python code along with the instructions on how to play the game",
    expected_output="Final polished, runnable Pygame Python script and instructions on how to play the game",
    agent=qa_engineer,
    context=[task_design, task_code]
)
```

## Step 3: Assembling the Crew

- Game Designer -Design Game
- Software Engineer - Write Code
- QA Engineer - Review & Refine

###Crew
The crew is your complete team — all agents working together with a defined process:

*   **Sequential** — Agents work one after another
*   **Hierarchical** — One agent manages others
*   **Parallel** — Agents work simultaneously

```python
from crewai import Crew, Process

game_crew = Crew(
    agents=[game_designer, senior_engineer, qa_engineer],
    tasks=[task_design, task_code, task_review],
    process=Process.sequential,
    verbose=True
)
```

- Tasks will be executed in the order they are defined.

## Step 4: Executing the Crew

` crew.kickoff()` CrewAI provides a method called `kickoff()` that allows us to start the execution process according to the defined process flow.

```python
game_idea = "A fun endless runner where a character jumps over obstacles"
result = game_crew.kickoff(inputs={"game_idea": game_idea})
print(result)
```

### Running the Output

Copy the code generated by the crew, paste it into a cell, and run the code.

### From Idea to Playable Experience

**Input:** `game_idea = "A fun endless runner where a character jumps over obstacles"`

**Output:** A complete, runnable Pygame game!

##Final code
- <a href="https://colab.research.google.com/drive/1BiuwD86iXpjE_137TMTzmoh9BrLH-NAe#scrollTo=dQ4n37Q8Sl3K" target="_blank">Building a Game Development Crew Final Code Colab</a>