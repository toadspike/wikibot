'''
Nathan N
February 2021
This is my second Wikipedia bot. It corrects spelling; reliability is limited, due to the bizarre nature of spelling errors on Wikipedia. 
This is also has a simple find/replace program, so it could find any text and replace it with any other text. In that regard it is very reliable. 
The program gives a bias estimate using VaderSentiment. 
Setting up Pywikibot on your computer is required. This helped me a lot: https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py
Sources: 
https://stackoverflow.com/questions/15388831/what-are-all-possible-pos-tags-of-nltk
http://www.nltk.org/book/ch05.html
https://pypi.org/project/pyspellchecker/
'''

# imports five modules
import pywikibot # Wikipedia bot, used to log in and edit pages
import requests # used to follow redirects and get a random wiki page
from spellchecker import SpellChecker # used to check spelling
import nltk # used to check for proper nouns and various uncheckable parts of speech
import webbrowser # used to open the page in a web browser
import vaderSentiment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

site = pywikibot.Site('en', 'wikipedia')  # The Wikipedia site we want to run our bot on
# page = pywikibot.Page(site, 'User:Toadspike/sandbox') # Sandbox, my own personal testing spot
spell = SpellChecker() # setting up spellchecker
spell.word_frequency.load_words(['http', 'reflist', 'café', 'br', 's', 'infobox', 'imagesize', 'defaultsort', 'nbsp', 'https', 'km']) # ignore some common Markup words and other correct vocab

issues = {' .': '.',' ,': ','} # Keys we want to replace with values
spellingparts = ["NN", "JJR", "JJ", "CC", "DT", "IN", "PDT", "PRP", "RBR", "RP", "VB", "NNS"] # In order: nouns, comparative adjectives, ordinal adjectives, conjuctions, determiners, prepositions, predeterminer, pronoun, comparative adj, verb, plural noun
badparts = ["JJS", "RB", "RBS", "UH"] # superlative adj, adverb, superlat. adv, interjection
italics = 0
checks = [] # words which need to be checked for spelling
replacements = {} # words which will be replaced with a correct spelling
spell.distance = 2 # spellchecker nonsense (not worth explaining)

randomurl = "https://randomincategory.toolforge.org/All_articles_needing_copy_edit?site=en.wikipedia.org" # target URL; in this case it returns a random page that needs copyediting
page = requests.get(randomurl) # Pywikibot doesn't follow redirects, so I used Requests to use the random page URL
url = page.url
# print(url)
name = url[30:] # Removes the first 30 chars. of the URL, giving the name of the article, which can be given to Pywikibot
# print(name)
page = pywikibot.Page(site, name) # Pywikibot opens the page

# simple find and replace, for common issues such as spaces before punctuation
for n in issues: 
    if n in page.text: 
        page.text = page.text.replace(n,issues[n])

webbrowser.open(url) # open the page in a browser

# sentiment/bias (from vaderSentiment tutorial code; this section is (mostly) not my original work)
analyzer = SentimentIntensityAnalyzer()
sentence_list = nltk.tokenize.sent_tokenize(page.text)
paragraphSentiments = 0.0
for sentence in sentence_list:
    vs = analyzer.polarity_scores(sentence)
    # print("{:-<69} {}".format(sentence, str(vs["compound"])))
    paragraphSentiments += vs["compound"]
print("AVERAGE SENTIMENT FOR ARTICLE: \t" + str(round(paragraphSentiments / len(sentence_list), 4))) # Here, anything above 0.05 or below -0.05 is indicative of bias
print("----------------------------------------------------")
pause = input("Press any key to continue: ")

# nltk interprets the text and assigns grammar tags
text = nltk.word_tokenize(page.text)
text = nltk.pos_tag(text)
# print(text)

# I search the tagged text for words that should be checked for spelling
# I count for italics, because foreign-language words are often italicized
for word in text:
    if word[0].isalpha(): # this crucial line removes all words with special symbols, most of which are part of the Wikipedia Markup
        if italics == 0:
            if word[1] in spellingparts:
                checks.append(word)
                # print(word)
            elif word[1] in badparts:
                checks.append(word)
                print("Bad: " + word[0]) # these are parts of speech that may be superfluous on a Wikipedia page, so I print them for manual investigation
            elif word[1] == '``':
                print("italics")
                italics = 2
        if italics > 0: 
            italics -= 1
    else:
        pass

# run spellcheck on the selected words
misspelled = spell.unknown(word[0] for word in checks)

# give spelling suggestions for misspelled words
for word in misspelled:
    suggestion = spell.correction(word) # Get the one most likely spelling
    if suggestion != word: 
        print(word + " TO " + suggestion)
        choice = input("Do you like that suggestion? (yes/new/skip) ")
        if choice == "y" or choice == "yes": 
            replacements[word] = suggestion
        elif choice == "n" or choice == "new":
            candidates = spell.candidates(word) # Get a list of likely options
            for c in candidates: # cycles through likely options until I have chosen one
                print(c)
                choice = input("Do you like that suggestion? (yes/new/skip/i) ")
                if choice == 'y' or choice == 'yes':
                    replacements[word] = c # adds word to list of changes
                    break
                elif choice == "n" or choice == "new":
                    break
                elif choice == "i": 
                    replacements[word] = input("Input suggestion: ")
        else:
            pass # allows me to skip words that are not misspelled

# replaces all misspelled words
for word in replacements: 
    page.text = page.text.replace(word,replacements[word])

page.save('Checking spelling') # Saves the page