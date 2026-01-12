import spacy
from spacy.matcher import PhraseMatcher
import sys
import subprocess

# -------------------------------
# NLP SERVICE
# -------------------------------
class NLPService:

    def __init__(self):

        # Load spaCy English model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model is not found, download it automatically
            print("Downloading spaCy model 'en_core_web_sm'...")
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

        # Create a phrase matcher
        self.matcher = PhraseMatcher(self.nlp.vocab)

        # Convert patterns to spaCy documents
        wake_word_patterns = [self.nlp(text) for text in [
            "hello kiwi", "hey kiwi", "okay kiwi", "ok kiwi",
            "kiwi", "key we", "kee wee", "he kiwi", "hay kiwi", "halo kiwi"
        ]]
        joke_patterns = [self.nlp(text) for text in [
            "tell me a joke", "make me laugh", "do you know a joke", 
            "tell another joke", "say something funny", "crack a joke",
            "tell a joke", "another joke"
        ]]
        song_patterns = [self.nlp(text) for text in ["play the song", "Can I listen to", "Please can you play", "music"]]

        # Add patterns to matcher
        self.matcher.add("WAKE_WORD", wake_word_patterns)
        self.matcher.add("JOKE", joke_patterns)
        self.matcher.add("SONG", song_patterns)



    def classify_instruction(self, text):
        # Clean input text
        cleaned_text = text.lower().strip()
        print(cleaned_text)

        # Use spaCy to analyse text
        doc = self.nlp(cleaned_text)
        matches = self.matcher(doc)

        if not matches:
            return "UNKNOWN"

        # Get the first match (or loop over all)
        match_id, start, end = matches[0]

        # Convert match_id to string label
        label = self.nlp.vocab.strings[match_id]
        return label

    def extract_song_name(self, text):
        cleaned_text = text.lower().strip()
        doc = self.nlp(cleaned_text)
        matches = self.matcher(doc)

        if not matches:
            return None

        match_id, start, end = matches[0]
        label = self.nlp.vocab.strings[match_id]

        if label != "SONG":
            return None

        song_name = doc[end:].text.strip()

        if song_name == "":
            return None

        # Remove common filler words at the END
        fillers = {"please", "now"}
        parts = song_name.split()

        while parts and parts[-1] in fillers:
            parts.pop()

        song_name = " ".join(parts).strip()

        if song_name == "":
            return None

        return song_name

