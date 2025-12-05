# Lightweight Virtual Assistant – EECE 2140 Final Project
### Caner Saka 
## 1. Overview

This project is a small virtual assistant built in Python with a web
interface using Gradio.

The goal is to show how basic programming ideas from this class, such as
If/elif decision trees, classes, methods, simple data structures, can be
combined to make a realistic chatbot. This is accomplished by making:

- A **rule-based intent detector** (no ML needed for the core logic).
- A **class** that remembers information during the chat.
- A simple **summary** feature that reports what happened overall during the conversation
- An optional **local LLM fallback** (Ollama + a GGUF) for questions that don't match or are open ended.



## 2. What the assistant can do

- Respond to **greetings** and **goodbyes**.
- Learn and remember your **name**
- React to your **mood**:
  - stores your mood,
  - gives a short reassurance,
  - keeps a mood history.
- Answer questions about:
  - **what the project is** (`"what is this project about?"`)
  - **how it works technically** (`"how do you work?"`)
- Provide **study/exam support/reassurance**
- Handle **small talk** (`"how are you?"`, `"what's up"`) using your stored mood.
- Provide a **summary of the chat** when asked

The assistant also:

- Personalizes some replies with your name.
 -Not all, to make it less robotic it is randomized.
- Matches typing style
  - if you type everything in lowercase, it replies in lowercase too.

---

## 3. How it works (design)

### 3.1 The `VirtualAssistant` class and state

All logic is inside the `VirtualAssistant` class. It stores:

- `self.name` – your name
- `self.mood` – the last mood sentence you wrote.
- `self.lastTopic` – the last type of message handled.
- `self.turns` – how many nonempty messages you sent.
- `self.topicsSeen` – set of broad topics for the summary.
- `self.moodHistory` – list of every mood message you sent.
- `self.chatHistory` – recent messages (user & assistant combnined) for the LLM context
- `self.useRealGguf` – whether to actually call the local LLM or just show the placeholder.
- `self.ggufEndpoint`, `self.ggufModelName` – which Ollama endpoint and model to use.

### 3.2 Intent detection

The `detectIntent` method:

1. Converts the text to lowercase.
2. Replaces punctuation with spaces.
3. Splits into a list of words.
4. Runs through if/elif checks to classify the message as:
   - `"greeting"`, `"goodbye"`, `"name"`, `"mood"`, `"project_info"`,
     `"project_tech"`, `"exam"`, `"study"`, `"thanks"`, `"help"`,
     `"small_talk"`, or `"summary"`.
5. If nothing matches, returns `"unknown"` so the LLM fallback kicks in.

### 3.3 Handlers

Each intent has its own handler method, such as:

- `handleGreeting`, `handleGoodbye`
- `handleName`, `handleMood`
- `handleProjectInfo`, `handleProjectTech`
- `handleExam`, `handleStudy`
- `handleThanks`, `handleHelp`
- `handleSmallTalk`, `handleSummary`

This keeps the code readable

The **summary** handler uses `self.name`, `self.moodHistory`, `self.topicsSeen`
and `self.turns` to make a quickrecap of the conversation.

### 3.4 Personalization and style

Two helper methods to boost personalit

- `personalizeName(reply, intent)`:
  - sometimes prefixes the reply with your name,
  - always does it for greetings and goodbyes,

- `matchCasing(userMessage, reply)`:
  - checks if the user typed only lowercase letters, and converts accordingly

### 3.5 LLM fallback

The `ggufFallback` method is called when the intent is `unknown`

It works in two modes:

- **Simple mode** (`useRealGguf = False`):
  Returns a short placeholder message and does *not* call any external API.

- **LLM mode** (`useRealGguf = True` and ollama + GGUF ):  
  1. Builds context string
  2. Creates a **system message** telling the model it is a helpful assitant
  3. Takes a small rolling window to keep memory
  4. Sends `system_message + recent_history + whatever the current user message`is
     to the Ollama endpoint.
  5. Returns the LLM’s reply.

---

## 4. How to run the project

### 4.1 Requirements
- PC with decent specs
 -16 GB of RAM, modern CPU (Discrete GPU would speed performance immensely)
- **Python**
- Packages:
  - **`gradio`**
  - `requests`
 - `pip install gradio requests`
- **Olama** installed and running
 -Download from https://ollama.com
- A **GGUF** file pulled into Ollama
 -Example used for demonstration is 
   - `ollama pull llama3.1:8b`
 - Ensure code matches the end point of the Ollama localhost server and the name of the model

 -Run the command
  -python lightweightvirtualassistant2140.py
