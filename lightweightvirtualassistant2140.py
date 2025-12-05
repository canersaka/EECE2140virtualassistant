import gradio as gr
import requests
import random


class VirtualAssistant:
    def __init__(self):
        #memory for current chat
        self.name = None
        self.mood = None
        self.lastTopic = None
        #details for summaries
        self.turns = 0
        self.topicsSeen = set()
        self.moodHistory = []
        #memory for LLM context
        self.chatHistory = []

        #LLM settings
        #set this to false to turn off llm ability
        self.useRealGGUF = True
        self.ggufEndpoint = "http://localhost:11434/api/chat"
        self.ggufModelName = "llama3.1:8b"


    def extractName(self, originalMessage, msgLower):
        """ 
        Try to pull a name out of sentences like:
        'my name is ____' or 'call me _____'
        """
        trigger = None
        if "my name is " in msgLower:
            trigger = "my name is "
        elif "call me " in msgLower:
            trigger = "call me "

        if trigger is None:
            return None

        startIndex = msgLower.find(trigger) + len(trigger)
        cleanName = originalMessage[startIndex:].strip()

        # stop at punctuation
        for punc in [",", ".", "!", "?"]:
            if punc in cleanName:
                parts = cleanName.split(punc, 1)
                cleanName = parts[0].strip()

        if cleanName == "":
            return None

        # make first letter uppercase so name looks normal by default
        return cleanName[0].upper() + cleanName[1:]

    def rememberTopic(self, intent):
        #rough topics for summary
        mapping = {
            "project_info": "the virtual assistant project",
            "project_tech": "how the project is implemented",
            "exam": "exams and studying",
            "study": "exams and studying",
            "mood": "how you were feeling",
        }
        if intent in mapping:
            self.topicsSeen.add(mapping[intent])

    def personalizeName(self, reply, intent):
        #sometimes add the user's name so it feels less robotic
        if self.name is None:
            return reply

        nameLower = self.name.lower()
        replyLower = reply.lower()

        #if we already said the name, don't say it again
        if nameLower in replyLower:
            return reply

        #always use name for greetings or goodbyes
        if intent in ("greeting", "goodbye"):
            return self.name + ", " + reply

        #otherwise, 30% chance to use it
        if random.random() < 0.3:
            return self.name + ", " + reply

        return reply

    def matchCasing(self, userMessage, reply):
        # roughly match the users typing style
        hasLetter = False
        allLower = True

        for char in userMessage:
            if char.isalpha():
                hasLetter = True
                if not char.islower():
                    allLower = False
                    break

        if not hasLetter:
            return reply

        if allLower:
            return reply.lower()

        return reply

    def detectIntent(self, msgLower):
        cleaned = msgLower
        for char in ["?", "!", ",", "."]:
            cleaned = cleaned.replace(char, " ")
        words = cleaned.split()
        #if elif tree for intents
        if ("hello" in words or "hi" in words or "hey" in words or "yo" in words):
            return "greeting"
        if ("bye" in words or "goodbye" in words):
            return "goodbye"
        if "see" in words and "you" in words:
            return "goodbye"
        if "my" in words and "name" in words and "is" in words:
            return "name"
        if "call" in words and "me" in words:
            return "name"
        if "my name is " in msgLower or "call me " in msgLower:
            return "name"
        if "feel" in words or "feeling" in words:
            return "mood"
        if (("i'm" in words or "im" in words or "i" in words) and ("sad" in words or "tired" in words or "stressed" in words or "anxious" in words or "okay" in words)):
            return "mood"
        if ("what" in words and "project" in words and "about" in words):
            return "project_info"
        if "virtual" in words and "assistant" in words and "project" in words:
            return "project_info"
        if "what is this project" in msgLower:
            return "project_info"
        if (("exam" in msgLower or "final" in msgLower or "test" in msgLower or "quiz" in msgLower) and ("what is" in msgLower or "tell me about" in msgLower or "explain" in msgLower)):
            return "unknown"
        if ("how does this work" in msgLower or "how do you work" in msgLower or "how are you implemented" in msgLower or "rule based" in msgLower or "gguf" in msgLower):
            return "project_tech"
        if ("exam" in msgLower or "final" in msgLower or "test" in msgLower or "quiz" in msgLower):
            return "exam"
        if ("study" in msgLower or "studying" in msgLower or "homework" in msgLower or "hw" in msgLower):
            return "study"
        if "thank" in msgLower or "thanks" in msgLower or "thx" in msgLower:
            return "thanks"
        if (msgLower.strip() == "help" or msgLower.strip() == "/help" or "what can you do" in msgLower):
            return "help"
        if (("how" in words and "are" in words and "you" in words) or ("sup" in words) or ("what's" in words and "up" in words) or ("whats" in words and "up" in words)):
            return "small_talk"
        if ("summarize" in msgLower or "summary" in msgLower or "recap" in msgLower or "what did we talk about" in msgLower):
            return "summary"
        return "unknown"

    def handleGreeting(self):
        self.lastTopic = "greeting"
        if self.name is not None:
            return "Nice to see you again."
        else:
            return "Hey, I'm your virtual assistant.\nYou can tell me your name by saying 'my name is ...'."

    def handleGoodbye(self):
        self.lastTopic = "goodbye"
        return "Okay, bye for now. Thanks for chatting!"

    def handleName(self, originalMessage, msgLower):
        self.lastTopic = "name"
        name = self.extractName(originalMessage, msgLower)
        if name is None:
            return "I tried to understand your name, but I'm not sure. Try 'my name is ...'."
        self.name = name
        return "Nice to meet you, " + name + ". How are you feeling today?"

    def handleMood(self, originalMessage, msgLower):
        self.lastTopic = "mood"
        self.mood = originalMessage
        self.moodHistory.append(originalMessage)
        feelingWords = {
            "anxious": "It sounds like you’re anxious. That’s really tough, but I’m glad you said it out loud.",
            "stressed": "You sound stressed. Maybe break things into smaller tasks so it feels less impossible.",
            "overwhelmed": "Feeling overwhelmed is common with school. One tiny step at a time still counts.",
            "tired": "You’re tired. Please don’t underestimate sleep. Even a short break can help.",
            "sad": "I’m sorry you’re feeling sad. You don’t have to fix everything at once.",
            "depressed": "I’m really sorry you feel that way. Talking to someone you trust in real life can help too.",
            "good": "Nice, I’m glad you’re feeling good.",
            "happy": "Happy is always nice to hear. Share a bit of that if you can.",
            "okay": "I'm glad you're feeling okay, anything you'd like to chat about?",
        }

        for word in feelingWords:
            if word in msgLower:
                return feelingWords[word] + " If you want, you can tell me what’s up."

        return "Thank you for telling me how you feel: \"" + originalMessage + "\".\nI might not fully understand it, but I’m here to listen."

    def handleProjectInfo(self):
        self.lastTopic = "project_info"
        return "This is my Virtual Assistant final project.\n- It uses simple if/elif rules to recognize patterns in what you type.\n- It keeps a bit of memory during the chat, which can be accessed by asking for a summary.\n- If a message does not match any rule, it can fall back to a GGUF model to handle more open-ended questions."

    def handleProjectTech(self):
        self.lastTopic = "project_tech"
        return "Technically, I work in a few steps:\n\n 1) Your message is cleaned/stripped and converted to lowercase so it is easier to analyze.\n 2) I run it through a rule based decision tree made of if/elif statements to detect your intent 3) Each intent has its own handler method that generates the appropriate reply.\n 4) I store conversation state inside my class for context and to summarize 5) If I cannot match your message to any known pattern, I use an optional local LLM fallback through Ollama. I send a small context window of the conversation to a GGUF model (like llama3.1:8b) and return its answer.\n\n"



    def handleExam(self):
        self.lastTopic = "exam"
        return "Exams are rough. Simple plan:\n1) Write down 3 topics you really need to review.\n2) Do about 25 minutes focused on the first one, then 5 minutes break.\n3) Repeat for the others.\nIf you tell me the topic, I can try a small pep talk."

    def handleStudy(self):
        self.lastTopic = "study"
        return "For studying, smaller chunks help a lot:\n- Turn 'study everything' into 'do 3 practice problems' or 'review 2 pages'.\n- Start with one small piece so your brain doesn’t immediately check out."

    def handleThanks(self):
        self.lastTopic = "thanks"
        return "You’re welcome!"

    def handleHelp(self):
        self.lastTopic = "help"
        return "Things you can try saying:\n- 'hi', 'hello' (greeting)\n- 'my name is...' (so I can remember your name)\n- 'I feel anxious / tired / sad / happy' (mood)\n- 'how are you?' or 'what's up' (small talk)\n- 'what is this project about?' (project info)\n- 'how do you work?' (technical explanation)\n- 'I have an exam' or 'I need to study' (study/exam help)\n- 'summarize our chat' (short recap)\nIf I don’t understand, I’ll use my GGUF fallback or just admit I don’t know."
    def handleSmallTalk(self):
        self.lastTopic = "small_talk"
        if self.mood is not None:
            return "I'm all good. Earlier you told me: \"" + self.mood + "\".\nSo I’d guess you’ve got a lot going on, but you’re still trying."
        else:
            return "I’m doing as good as any simple program could be. How are you doing?"
    def handleSummary(self):
        self.lastTopic = "summary"

        if self.turns == 0:
            return "We haven’t really talked yet, so there isn’t much to summarize."

        lines = []

        if self.name:
            lines.append("- You told me your name is " + self.name + ".")

        if self.moodHistory:
            if len(self.moodHistory) == 1:
                lines.append("- You shared how you feel: \"" + self.moodHistory[0] + "\".")
            else:
                lines.append("- You shared how you felt at different times:")
                for feeling in self.moodHistory:
                    lines.append("  - \"" + feeling + "\"")

        if len(self.topicsSeen) > 0:
            topicsText = ", ".join(sorted(self.topicsSeen))
            lines.append("- We talked about: " + topicsText + ".")

        lines.append("- Altogether, we exchanged about " + str(self.turns * 2) + " messages.")

        return "Here’s a quick summary of our chat so far:\n" + "\n".join(lines)

    #For messages that don't match the above, GGUF fallback
    def ggufFallback(self, userMessage):
        if not self.useRealGGUF:
            return "I don't have a specific rule for that.\nIn the full design this is where I would call a local large language model to generate a more flexible answer."

        context_info = ""
        if self.name:
            context_info += f" The user's name is {self.name}."
        if self.mood:
            context_info += f" The user feels {self.mood}."

        system_message = {"role": "system", "content": f"You are a helpful but simple assistant.{context_info}"}

        recent_history = self.chatHistory[-6:]
        messages = [system_message] + recent_history + [{"role": "user", "content": userMessage}]

        try:
            payload = {"model": self.ggufModelName, "messages": messages, "stream": False}

            response = requests.post(self.ggufEndpoint, json=payload, timeout=20)

            data = response.json()
            reply = data["message"]["content"]
            return reply.strip()

        except Exception:
            return "I tried to ask my local LLM for help, but something went wrong."


#Main handlerm takes text, sends to intent detector, and then outputs set response or outputs from gguf
    def respond(self, message):
        text = message.strip()
        if text == "":
            reply = "Say something and I’ll try to respond."
            reply = self.matchCasing(message, reply)
            return reply

        self.turns += 1
        msgLower = text.lower()
        intent = self.detectIntent(msgLower)

        if intent == "greeting":
            reply = self.handleGreeting()
        elif intent == "goodbye":
            reply = self.handleGoodbye()
        elif intent == "name":
            reply = self.handleName(text, msgLower)
        elif intent == "mood":
            reply = self.handleMood(text, msgLower)
        elif intent == "project_info":
            reply = self.handleProjectInfo()
        elif intent == "project_tech":
            reply = self.handleProjectTech()
        elif intent == "exam":
            reply = self.handleExam()
        elif intent == "study":
            reply = self.handleStudy()
        elif intent == "thanks":
            reply = self.handleThanks()
        elif intent == "help":
            reply = self.handleHelp()
        elif intent == "small_talk":
            reply = self.handleSmallTalk()
        elif intent == "summary":
            reply = self.handleSummary()
        else:
            reply = self.ggufFallback(text)

        self.rememberTopic(intent)

        self.chatHistory.append({"role": "user", "content": text})
        self.chatHistory.append({"role": "assistant", "content": reply})

        reply = self.personalizeName(reply, intent)

        reply = self.matchCasing(message, reply)
        return reply


assistant = VirtualAssistant()

def chatFunction(message, history):
    return assistant.respond(message)

demo = gr.ChatInterface(
    fn=chatFunction,
    title="Virtual Assistant (Final Project)",
    description=("Rule-based chatbot using if/elif, and an optional GGUF fallback.")
)

demo.launch()
