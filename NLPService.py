import spacy
from spacy.matcher import PhraseMatcher
import subprocess
import sys
from metaphone import doublemetaphone
from rapidfuzz import fuzz



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
        # self.wake_word_patterns_list = ["hello kiwi", "hey kiwi", "okay kiwi", "ok kiwi", "hey key", "key", "kiwi", "hi kiwi"]
        self.wake_word_patterns_list = [
                                    "hello kiwi", "hello key", "hello kwee", "hello kwee-wee", "hell oh kiwi",
                                    "hey kiwi", "hello ki", "hey kwee", "hey key", "hai kiwi", "he kiwi",
                                    "hay kiwi", "hey kwee-wee", "okay kiwi", "okay key", "ok kiwi", "okee kwee",
                                    "oh key kiwi", "o k kiwi", "oh-kay kwee", "okiwi", "o k kwee", "ok kwee",
                                    "oke kwee", "hey kye", "hi key", "hey kei", "hey kee", "hay key", "hei key",
                                    "key", "kye", "kee", "kae", "keh", "keye", "kyee", "kiwi", "tv", "kwee",
                                    "kee wee", "key wie", "kee vi", "kwee vi", "kye vi", "kewi", "kiwie",
                                    "kiywi", "beewee", "teewee", "hay we", "kee bee", "key bee", "heewee",
                                    "deewee", "zeewee", "brewee", "skeewee", "shewee", "leewie", "me key", "t.v",
                                    "atv"
        ]

        wake_word_patterns = [self.nlp(text) for text in self.wake_word_patterns_list]
        joke_patterns = [self.nlp(text) for text in ["tell me a joke"]]
        song_patterns = [self.nlp(text) for text in
                         [  "play the song",
                             "can I listen to the song",
                             "please can you play the song",
                             "play this song",
                             "could you play the song",
                             "please play the song",
                             "start the song",
                             "turn on the song",
                             "I want the song",
                             "let me hear the song",
                             "can you start the song",
                             "would you play the song",
                             "a song",
                             "play a song",
                             "sing a song",
                             "play some song",
                             "start a song",
                            "play"
                         ]]

        weather_patterns = [
            self.nlp(text) for text in [
                "what's the weather",
                "what is the weather",
                "what's the temperature",
                "tell me the weather",
                "weather in",
                "temperature in"
            ]
        ]
        time_patterns = [self.nlp(text) for text in [
            "what's the time",
            "what is the time",
            "tell me the time",
            "time please"
        ]]
        volume_up_patterns = [self.nlp(text) for text in [
            "turn the volume up",
            "volume up",
            "turn it up",
            "make it louder",
            "increase the volume",
            "put the volume louder"
        ]]
        volume_max_patterns = [self.nlp(text) for text in [
            "turn the volume max",
            "volume max",
            "turn it max volume",
            "make it loudest",
            "increase the volume to max",
            "set volume to 100"
        ]]

        volume_down_patterns = [self.nlp(text) for text in [
            "turn the volume down",
            "volume down",
            "turn it down",
            "make it quieter",
            "decrease the volume",
            "put the volume quieter"
        ]]

        mute_patterns = [self.nlp(text) for text in [
            "mute",
            "mute the volume",
            "turn the volume off",
            "silence"
        ]]

        # Add patterns to matcher
        self.matcher.add("WAKE_WORD", wake_word_patterns)
        self.matcher.add("JOKE", joke_patterns)
        self.matcher.add("SONG", song_patterns)
        self.matcher.add("WEATHER", weather_patterns)
        self.matcher.add("TIME", time_patterns)
        self.matcher.add("VOLUME_UP", volume_up_patterns)
        self.matcher.add("VOLUME_DOWN", volume_down_patterns)
        self.matcher.add("MUTE", mute_patterns)
        self.matcher.add("VOLUME_MAX", volume_max_patterns)



    def classify_instruction(self, text):
        # Clean input text
        cleaned_text = text.lower().strip()

        # Use spaCy to analyse text
        doc = self.nlp(cleaned_text)
        matches = self.matcher(doc)

        if not matches:
            return self.detect_best_match(cleaned_text, self.wake_word_patterns_list)
        # Get the first match (or loop over all)
        match_id, start, end = matches[0]

        # Convert match_id to string label
        label = self.nlp.vocab.strings[match_id]
        return label

    def detect_best_match(self, cleaned_text, wake_word_patterns_list, fuzzy_threshold=60):
        # Phonetic representation of input text
        cleaned_text = str(cleaned_text)
        phonetic_representation_input = doublemetaphone(cleaned_text)

        # Track the best matching wake word
        best_match = None
        highest_score = 0

        for wake_word in wake_word_patterns_list:
            # print(f"Checking wake word '{wake_word}'...")
            # Get phonetic representation of the current wake word
            phonetic_representation_wakeword = doublemetaphone(wake_word)

            # Check phonetic similarity (primary and alternate matches)
            phonetic_match = (
                    phonetic_representation_input[0] == phonetic_representation_wakeword[0] or
                    phonetic_representation_input[1] == phonetic_representation_wakeword[1]
            )
            # print(f"Phonetic match for '{wake_word}': {phonetic_match}")
            # If phonetic match, also calculate fuzzy text similarity
            if phonetic_match:
                fuzzy_score = fuzz.ratio(cleaned_text, wake_word)
                # print(f"Fuzzy score for '{wake_word}': {fuzzy_score}%")
                if fuzzy_score > highest_score and fuzzy_score >= fuzzy_threshold:
                    best_match = wake_word
                    highest_score = fuzzy_score

        # Return the best match if any, or None if no matches meet the threshold
        return "WAKE_WORD" if best_match else "UNKNOWN"


