# gensim_shim.py
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from functools import wraps

# Create a function that wraps Sumy with the Gensim API
def convert_params(summarize_func):
    @wraps(summarize_func)
    def wrapper(text, ratio=None, word_count=None, split=False):
        language = "english"
        # Sumy requires a parser and tokenizer
        parser = PlaintextParser.from_string(text, Tokenizer(language))
        stemmer = Stemmer(language)
        summarizer = TextRankSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(language)

        # Determine the number of sentences based on gensim's ratio or word_count
        sentence_count = None
        if ratio is not None:
            num_sentences_total = len(parser.document.sentences)
            if num_sentences_total > 0:
                sentence_count = int(num_sentences_total * ratio)
            else:
                sentence_count = 1 # Fallback to 1 sentence if no sentences found
        elif word_count is not None:
            # Approximate sentence count based on word count. 
            # This is not a perfect 1:1 mapping but follows the original gensim logic.
            average_words_per_sentence = 10 # Heuristic value
            sentence_count = max(1, int(word_count / average_words_per_sentence))
        
        # If no ratio or word_count, Sumy uses its default behavior
        if sentence_count is None:
            summary = summarizer(parser.document)
        else:
            summary = summarizer(parser.document, sentence_count=sentence_count)

        sentences = [str(s) for s in summary]

        if split:
            return sentences
        return " ".join(sentences)
    return wrapper

# Expose the new summarize function under the old name
@convert_params
def summarize(*args, **kwargs):
    """Placeholder to mimic gensim.summarization.summarizer.summarize"""
    pass

# Create a dummy class to mimic the gensim.summarization namespace
class summarization:
    summarize = summarize
