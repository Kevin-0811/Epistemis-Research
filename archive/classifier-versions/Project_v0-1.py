biased_words = {"always" : "", "never"  : "rarely", "everyone" : "many people", "no one" : "few people", 
                        "must" : "should", "only" : "primarily", "obviously" : "", "undoubtedly" : "", 
                        "definitely" : "likely", "completely" : "majorly", "have ever" : "have"}
sentence = input("Enter the sentence: ")
words = sentence.split()
for word in words:
    if word.lower() in biased_words:
        print(f"Biased word found: {word}")
        print(f"neutral version of word: {biased_words[word.lower()]}\n")
neutral_words = []
for word in words: 
                if word.lower() in biased_words:
                    neutral_words.append(biased_words[word.lower()])
                else:
                    neutral_words.append(word)
neutral_sentence = " ".join(neutral_words)
print(f"Neutral version of the sentence is {neutral_sentence}")  
