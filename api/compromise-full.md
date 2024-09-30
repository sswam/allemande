title: GitHub - spencermountain/compromise: modest natural-language processing
From: https://github.com/spencermountain/compromise

don\'t you find it strange,



 compromise *[tries its best]()* to turn text into data.
 it makes limited and sensible decisions.
 it\'s not as smart as you\'d think. 



 import nlp from 'compromise' 
 let doc = nlp ( 'she sells seashells by the seashore.' ) 
 doc . verbs ( ) . toPastTense ( ) 
 doc . text ( ) 
 // 'she sold seashells by the seashore.' 



*don\'t be fancy, at all:*

 if ( doc . has ( 'simon says #Verb' ) ) { 
 return true 
 } 



 *grab parts of the text:*

 let doc = nlp ( entireNovel ) 
 doc . match ( 'the #Adjective of times' ) . text ( ) 
 // "the blurst of times?" 

[match docs]() 



*and get data:*

 import plg from 'compromise-speech' 
 nlp . extend ( plg ) 
 let doc = nlp ( 'Milwaukee has certainly had its share of visitors..' ) 
 doc . compute ( 'syllables' ) 
 doc . places ( ) . json ( ) 
 /* 
 [{ 
 "text": "Milwaukee", 
 "terms": [{ 
 "normal": "milwaukee", 
 "syllables": ["mil", "wau", "kee"] 
 }] 
 }] 
 */ 

[json docs]() 



avoid the problems of brittle parsers:

 let doc = nlp ( "we're not gonna take it.." ) 
 doc . has ( 'gonna' ) // true 
 doc . has ( 'going to' ) // true (implicit) 
 // transform 
 doc . contractions ( ) . expand ( ) 
 doc . text ( ) 
 // 'we are not going to take it..' 

[contraction docs]() 



and whip stuff around like it\'s data:

 let doc = nlp ( 'ninety five thousand and fifty two' ) 
 doc . numbers ( ) . add ( 20 ) 
 doc . text ( ) 
 // 'ninety five thousand and seventy two' 

[number docs]() 



-because it actually is-

 let doc = nlp ( 'the purple dinosaur' ) 
 doc . nouns ( ) . toPlural ( ) 
 doc . text ( ) 
 // 'the purple dinosaurs' 

[noun docs]() 



Use it on the client-side:

 var doc = nlp ( 'two bottles of beer' ) 
 doc . numbers ( ) . minus ( 1 ) 
 document . body . innerHTML = doc . text ( ) 
 // 'one bottle of beer' 

or likewise:

 import nlp from 'compromise' 
 var doc = nlp ( 'London is calling' ) 
 doc . verbs ( ) . toNegative ( ) 
 // 'London is not calling' 





compromise is **\~250kb** (minified):



it\'s pretty fast. It can run on keypress:



it works mainly by [conjugating all forms]() of a basic word list.

The final lexicon is [\~14,000 words]() :



you can read more about how it works, [here]() . it\'s weird.



okay -

# compromise/one

(#---compromiseone--)

A tokenizer of words, sentences, and punctuation.



 import nlp from 'compromise/one' 
 let doc = nlp ( "Wayne's World, party time" ) 
 let data = doc . json ( ) 
 /* [{ 
 normal:"wayne's world party time", 
 terms:[, 
 ... 
 ] 
 }] 
 */ 

[tokenizer docs]()

**compromise/one** splits your text up, wraps it in a handy API,



**/one** is quick - most sentences take a 10th of a millisecond.

It can do **\~1mb** of text a second - or 10 wikipedia pages.

*Infinite jest* takes 3s.

You can also parallelize, or stream text to it with [compromise-speed]() .



# compromise/two

(#---compromisetwo--)

A part-of-speech tagger, and grammar-interpreter.



 import nlp from 'compromise/two' 
 let doc = nlp ( "Wayne's World, party time" ) 
 let str = doc . match ( '#Possessive #Noun' ) . text ( ) 
 // "Wayne's World" 

[tagger docs]()



**compromise/two** automatically calculates the very basic grammar of each word.

this is more useful than people sometimes realize.

Light grammar helps you write cleaner templates, and get closer to the information.



compromise has **83 tags** , arranged in [a handsome graph]() .

**#FirstName** → **#Person** → **#ProperNoun** → **#Noun**

you can see the grammar of each word by running doc.debug()

you can see the reasoning for each tag with nlp.verbose(\'tagger\') .

if you prefer [*Penn tags*]() , you can derive them with:

 let doc = nlp ( 'welcome thrillho' ) 
 doc . compute ( 'penn' ) 
 doc . json ( ) 



# compromise/three

(#---compromisethree--)

Phrase and sentence tooling.



 import nlp from 'compromise/three' 
 let doc = nlp ( "Wayne's World, party time" ) 
 let str = doc . people ( ) . normalize ( ) . text ( ) 
 // "wayne" 

[selection docs]()

**compromise/three** is a set of tooling to *zoom into* and operate on parts of a text.

.numbers() grabs all the numbers in a document, for example - and extends it with new methods, like .subtract() .

When you have a phrase, or group of words, you can see additional metadata about it with .json()

 let doc = nlp ( 'four out of five dentists' ) 
 console . log ( doc . fractions ( ) . json ( ) ) 
 /*[{ 
 text: 'four out of five', 
 terms: [ [Object], [Object], [Object], [Object] ], 
 fraction: 
 } 
 ]*/ 

 let doc = nlp ( '$4.09CAD' ) 
 doc . money ( ) . json ( ) 
 /*[{ 
 text: '$4.09CAD', 
 terms: [ [Object] ], 
 number: 
 } 
 ]*/ 



## API

(#api)

### Compromise/one

(#compromiseone)

##### Output

(#output)

- **[.text()]()** - return the document as text
- **[.json()]()** - return the document as data
- **[.debug()]()** - pretty-print the interpreted document
- **[.out()]()** - a named or custom output
- **[.html()]()** - output custom html tags for matches
- **[.wrap()]()** - produce custom output for document matches

##### Utils

(#utils)

- **[.found]()** *\[getter\]* - is this document empty?
- **[.docs]()** *\[getter\]* get term objects as json
- **[.length]()** *\[getter\]* - count the \# of characters in the document (string length)
- **[.isView]()** *\[getter\]* - identify a compromise object
- **[.compute()]()** - run a named analysis on the document
- **[.clone()]()** - deep-copy the document, so that no references remain
- **[.termList()]()** - return a flat list of all Term objects in match
- **[.cache()]()** - freeze the current state of the document, for speed-purposes
- **[.uncache()]()** - un-freezes the current state of the document, so it may be transformed
- **[.freeze()]()** - prevent any tags from being removed, in these terms
- **[.unfreeze()]()** - allow tags to change again, as default

##### Accessors

(#accessors)

- **[.all()]()** - return the whole original document (\'zoom out\')
- **[.terms()]()** - split-up results by each individual term
- **[.first(n)]()** - use only the first result(s)
- **[.last(n)]()** - use only the last result(s)
- **[.slice(n,n)]()** - grab a subset of the results
- **[.eq(n)]()** - use only the nth result
- **[.firstTerms()]()** - get the first word in each match
- **[.lastTerms()]()** - get the end word in each match
- **[.fullSentences()]()** - get the whole sentence for each match
- **[.groups()]()** - grab any named capture-groups from a match
- **[.wordCount()]()** - count the \# of terms in the document
- **[.confidence()]()** - an average score for pos tag interpretations

##### Match

(#match)

*(match methods use the [match-syntax]() .)*

- **[.match(\'\')]()** - return a new Doc, with this one as a parent
- **[.not(\'\')]()** - return all results except for this
- **[.matchOne(\'\')]()** - return only the first match
- **[.if(\'\')]()** - return each current phrase, only if it contains this match (\'only\')
- **[.ifNo(\'\')]()** - Filter-out any current phrases that have this match (\'notIf\')
- **[.has(\'\')]()** - Return a boolean if this match exists
- **[.before(\'\')]()** - return all terms before a match, in each phrase
- **[.after(\'\')]()** - return all terms after a match, in each phrase
- **[.union()]()** - return combined matches without duplicates
- **[.intersection()]()** - return only duplicate matches
- **[.complement()]()** - get everything not in another match
- **[.settle()]()** - remove overlaps from matches
- **[.growRight(\'\')]()** - add any matching terms immediately after each match
- **[.growLeft(\'\')]()** - add any matching terms immediately before each match
- **[.grow(\'\')]()** - add any matching terms before or after each match
- **[.sweep(net)]()** - apply a series of match objects to the document
- **[.splitOn(\'\')]()** - return a Document with three parts for every match (\'splitOn\')
- **[.splitBefore(\'\')]()** - partition a phrase before each matching segment
- **[.splitAfter(\'\')]()** - partition a phrase after each matching segment
- **[.join()]()** - merge any neighbouring terms in each match
- **[.joinIf(leftMatch, rightMatch)]()** - merge any neighbouring terms under given conditions
- **[.lookup(\[\])]()** - quick find for an array of string matches
- **[.autoFill()]()** - create type-ahead assumptions on the document

##### Tag

(#tag)

- **[.tag(\'\')]()** - Give all terms the given tag
- **[.tagSafe(\'\')]()** - Only apply tag to terms if it is consistent with current tags
- **[.unTag(\'\')]()** - Remove this term from the given terms
- **[.canBe(\'\')]()** - return only the terms that can be this tag

##### Case

(#case)

- **[.toLowerCase()]()** - turn every letter of every term to lower-cse
- **[.toUpperCase()]()** - turn every letter of every term to upper case
- **[.toTitleCase()]()** - upper-case the first letter of each term
- **[.toCamelCase()]()** - remove whitespace and title-case each term

##### Whitespace

(#whitespace)

- **[.pre(\'\')]()** - add this punctuation or whitespace before each match
- **[.post(\'\')]()** - add this punctuation or whitespace after each match
- **[.trim()]()** - remove start and end whitespace
- **[.hyphenate()]()** - connect words with hyphen, and remove whitespace
- **[.dehyphenate()]()** - remove hyphens between words, and set whitespace
- **[.toQuotations()]()** - add quotation marks around these matches
- **[.toParentheses()]()** - add brackets around these matches

##### Loops

(#loops)

- **[.map(fn)]()** - run each phrase through a function, and create a new document
- **[.forEach(fn)]()** - run a function on each phrase, as an individual document
- **[.filter(fn)]()** - return only the phrases that return true
- **[.find(fn)]()** - return a document with only the first phrase that matches
- **[.some(fn)]()** - return true or false if there is one matching phrase
- **[.random(fn)]()** - sample a subset of the results

##### Insert

(#insert)

- **[.replace(match, replace)]()** - search and replace match with new content
- **[.replaceWith(replace)]()** - substitute-in new text
- **[.remove()]()** - fully remove these terms from the document
- **[.insertBefore(str)]()** - add these new terms to the front of each match (prepend)
- **[.insertAfter(str)]()** - add these new terms to the end of each match (append)
- **[.concat()]()** - add these new things to the end
- **[.swap(fromLemma, toLemma)]()** - smart replace of root-words,using proper conjugation

##### Transform

(#transform)

- **[.sort(\'method\')]()** - re-arrange the order of the matches (in place)
- **[.reverse()]()** - reverse the order of the matches, but not the words
- **[.normalize()]()** - clean-up the text in various ways
- **[.unique()]()** - remove any duplicate matches

##### Lib

(#lib)

*(these methods are on the main nlp object)*

- **[nlp.tokenize(str)]()** - parse text without running POS-tagging

- **[nlp.lazy(str, match)]()** - scan through a text with minimal analysis

- **[nlp.plugin()]()** - mix in a compromise-plugin

- **[nlp.parseMatch(str)]()** - pre-parse any match statements into json

- **[nlp.world()]()** - grab or change library internals

- **[nlp.model()]()** - grab all current linguistic data

- **[nlp.methods()]()** - grab or change internal methods

- **[nlp.hooks()]()** - see which compute methods run automatically

- **[nlp.verbose(mode)]()** - log our decision-making for debugging

- **[nlp.version]()** - current semver version of the library

- **[nlp.addWords(obj, isFrozen?)]()** - add new words to the lexicon

- **[nlp.addTags(obj)]()** - add new tags to the tagSet

- **[nlp.typeahead(arr)]()** - add words to the auto-fill dictionary

- **[nlp.buildTrie(arr)]()** - compile a list of words into a fast lookup form

- **[nlp.buildNet(arr)]()** - compile a list of matches into a fast match form



### compromise/two:

(#compromisetwo)

##### Contractions

(#contractions)

- **[.contractions()]()** - things like \"didn\'t\"
- **[.contractions().expand()]()** - things like \"didn\'t\"
- **[.contract()]()** - things like \"didn\'t\"



### compromise/three:

(#compromisethree)

##### Nouns

(#nouns)

- **[.nouns()]()** - return any subsequent terms tagged as a Noun
 - **[.nouns().json()]()** - overloaded output with noun metadata
 - **[.nouns().parse()]()** - get tokenized noun-phrase
 - **[.nouns().isPlural()]()** - return only plural nouns
 - **[.nouns().isSingular()]()** - return only singular nouns
 - **[.nouns().toPlural()]()** - \'football captain\' → \'football captains\'
 - **[.nouns().toSingular()]()** - \'turnovers\' → \'turnover\'
 - **[.nouns().adjectives()]()** - get any adjectives describing this noun

##### Verbs

(#verbs)

- **[.verbs()]()** - return any subsequent terms tagged as a Verb
 - **[.verbs().json()]()** - overloaded output with verb metadata
 - **[.verbs().parse()]()** - get tokenized verb-phrase
 - **[.verbs().subjects()]()** - what is doing the verb action
 - **[.verbs().adverbs()]()** - return the adverbs describing this verb.
 - **[.verbs().isSingular()]()** - return singular verbs like \'spencer walks\'
 - **[.verbs().isPlural()]()** - return plural verbs like \'we walk\'
 - **[.verbs().isImperative()]()** - only instruction verbs like \'eat it!\'
 - **[.verbs().toPastTense()]()** - \'will go\' → \'went\'
 - **[.verbs().toPresentTense()]()** - \'walked\' → \'walks\'
 - **[.verbs().toFutureTense()]()** - \'walked\' → \'will walk\'
 - **[.verbs().toInfinitive()]()** - \'walks\' → \'walk\'
 - **[.verbs().toGerund()]()** - \'walks\' → \'walking\'
 - **[.verbs().toPastParticiple()]()** - \'drive\' → \'had driven\'
 - **[.verbs().conjugate()]()** - return all conjugations of these verbs
 - **[.verbs().isNegative()]()** - return verbs with \'not\', \'never\' or \'no\'
 - **[.verbs().isPositive()]()** - only verbs without \'not\', \'never\' or \'no\'
 - **[.verbs().toNegative()]()** - \'went\' → \'did not go\'
 - **[.verbs().toPositive()]()** - \"didn\'t study\" → \'studied\'

##### Numbers

(#numbers)

- **[.numbers()]()** - grab all written and numeric values
 - **[.numbers().parse()]()** - get tokenized number phrase
 - **[.numbers().get()]()** - get a simple javascript number
 - **[.numbers().json()]()** - overloaded output with number metadata
 - **[.numbers().toNumber()]()** - convert \'five\' to 5
 - **[.numbers().toLocaleString()]()** - add commas, or nicer formatting for numbers
 - **[.numbers().toText()]()** - convert \'5\' to five
 - **[.numbers().toOrdinal()]()** - convert \'five\' to fifth or 5th
 - **[.numbers().toCardinal()]()** - convert \'fifth\' to five or 5
 - **[.numbers().isOrdinal()]()** - return only ordinal numbers
 - **[.numbers().isCardinal()]()** - return only cardinal numbers
 - **[.numbers().isEqual(n)]()** - return numbers with this value
 - **[.numbers().greaterThan(min)]()** - return numbers bigger than n
 - **[.numbers().lessThan(max)]()** - return numbers smaller than n
 - **[.numbers().between(min, max)]()** - return numbers between min and max
 - **[.numbers().isUnit(unit)]()** - return only numbers in the given unit, like \'km\'
 - **[.numbers().set(n)]()** - set number to n
 - **[.numbers().add(n)]()** - increase number by n
 - **[.numbers().subtract(n)]()** - decrease number by n
 - **[.numbers().increment()]()** - increase number by 1
 - **[.numbers().decrement()]()** - decrease number by 1
- **[.money()]()** - things like \'\$2.50\'
 - **[.money().get()]()** - retrieve the parsed amount(s) of money
 - **[.money().json()]()** - currency + number info
 - **[.money().currency()]()** - which currency the money is in
- **[.fractions()]()** - like \'2/3rds\' or \'one out of five\'
 - **[.fractions().parse()]()** - get tokenized fraction
 - **[.fractions().get()]()** - simple numerator, denomenator data
 - **[.fractions().json()]()** - json method overloaded with fractions data
 - **[.fractions().toDecimal()]()** - \'2/3\' -\> \'0.66\'
 - **[.fractions().normalize()]()** - \'four out of 10\' -\> \'4/10\'
 - **[.fractions().toText()]()** - \'4/10\' -\> \'four tenths\'
 - **[.fractions().toPercentage()]()** - \'4/10\' -\> \'40%\'
- **[.percentages()]()** - like \'2.5%\'
 - **[.percentages().get()]()** - return the percentage number / 100
 - **[.percentages().json()]()** - json overloaded with percentage information
 - **[.percentages().toFraction()]()** - \'80%\' -\> \'8/10\'

##### Sentences

(#sentences)

- **[.sentences()]()** - return a sentence class with additional methods
 - **[.sentences().json()]()** - overloaded output with sentence metadata

 ```

 ```
 - **[.sentences().toPastTense()]()** - he walks -\> he walked
 - **[.sentences().toPresentTense()]()** - he walked -\> he walks
 - **[.sentences().toFutureTense()]()** \-- he walks -\> he will walk
 - **[.sentences().toInfinitive()]()** \-- verb root-form he walks -\> he walk
 - **[.sentences().toNegative()]()** - - he walks -\> he didn\'t walk
 - **[.sentences().isQuestion()]()** - return questions with a ?
 - **[.sentences().isExclamation()]()** - return sentences with a !
 - **[.sentences().isStatement()]()** - return sentences without ? or !

##### Adjectives

(#adjectives)

- **[.adjectives()]()** - things like \'quick\'
 - **[.adjectives().json()]()** - get adjective metadata
 - **[.adjectives().conjugate()]()** - return all inflections of these adjectives
 - **[.adjectives().adverbs()]()** - get adverbs describing this adjective
 - **[.adjectives().toComparative()]()** - \'quick\' -\> \'quicker\'
 - **[.adjectives().toSuperlative()]()** - \'quick\' -\> \'quickest\'
 - **[.adjectives().toAdverb()]()** - \'quick\' -\> \'quickly\'
 - **[.adjectives().toNoun()]()** - \'quick\' -\> \'quickness\'

##### Misc selections

(#misc-selections)

- **[.clauses()]()** - split-up sentences into multi-term phrases
- **[.chunks()]()** - split-up sentences noun-phrases and verb-phrases
- **[.hyphenated()]()** - all terms connected with a hyphen or dash like \'wash-out\'
- **[.phoneNumbers()]()** - things like \'(939) 555-0113\'
- **[.hashTags()]()** - things like \'#nlp\'
- **[.emails()]()** - things like \'hi@compromise.cool\'
- **[.emoticons()]()** - things like :)
- **[.emojis()]()** - things like 💋
- **[.atMentions()]()** - things like \'@nlp_compromise\'
- **[.urls()]()** - things like \'compromise.cool\'
- **[.pronouns()]()** - things like \'he\'
- **[.conjunctions()]()** - things like \'but\'
- **[.prepositions()]()** - things like \'of\'
- **[.abbreviations()]()** - things like \'Mrs.\'
- **[.people()]()** - names like \'John F. Kennedy\'
 - **[.people().json()]()** - get person-name metadata
 - **[.people().parse()]()** - get person-name interpretation
- **[.places()]()** - like \'Paris, France\'
- **[.organizations()]()** - like \'Google, Inc\'
- **[.topics()]()** - people() + places() + organizations()
- **[.adverbs()]()** - things like \'quickly\'
 - **[.adverbs().json()]()** - get adverb metadata
- **[.acronyms()]()** - things like \'FBI\'
 - **[.acronyms().strip()]()** - remove periods from acronyms
 - **[.acronyms().addPeriods()]()** - add periods to acronyms
- **[.parentheses()]()** - return anything inside (parentheses)
 - **[.parentheses().strip()]()** - remove brackets
- **[.possessives()]()** - things like \"Spencer\'s\"
 - **[.possessives().strip()]()** - \"Spencer\'s\" -\> \"Spencer\"
- **[.quotations()]()** - return any terms inside paired quotation marks
 - **[.quotations().strip()]()** - remove quotation marks
- **[.slashes()]()** - return any terms grouped by slashes
 - **[.slashes().split()]()** - turn \'love/hate\' into \'love hate\'





### .extend():

(#extend)

This library comes with a considerate, common-sense baseline for english grammar.

You\'re free to change, or lay-waste to any settings - which is the fun part actually.

the easiest part is just to suggest tags for any given words:

 let myWords = { 
 kermit : 'FirstName' , 
 fozzie : 'FirstName' , 
 } 
 let doc = nlp ( muppetText , myWords ) 

or make heavier changes with a [compromise-plugin]() .

 import nlp from 'compromise' 
 nlp . extend ( { 
 // add new tags 
 tags : { 
 Character : { 
 isA : 'Person' , 
 notA : 'Adjective' , 
 } , 
 } , 
 // add or change words in the lexicon 
 words : { 
 kermit : 'Character' , 
 gonzo : 'Character' , 
 } , 
 // change inflections 
 irregulars : { 
 get : { 
 pastTense : 'gotten' , 
 gerund : 'gettin' , 
 } , 
 } , 
 // add new methods to compromise 
 api : View => { 
 View . prototype . kermitVoice = function ( ) { 
 this . sentences ( ) . prepend ( 'well,' ) 
 this . match ( 'i [(am|was)]' ) . prepend ( 'um,' ) 
 return this 
 } 
 } , 
 } ) 

[.plugin() docs]()  

### Docs:

(#docs)

##### gentle introduction:

(#gentle-introduction)

- **[#1) Input → output]()**
- **[#2) Match & transform]()**
- **[#3) Making a chat-bot]()**



##### Documentation:

(#documentation)

 Concepts API Plugins

 [Accuracy]() [Accessors]() [Adjectives]()
 [Caching]() [Constructor-methods]() [Dates]()
 [Case]() [Contractions]() [Export]()
 [Filesize]() [Insert]() [Hash]()
 [Internals]() [Json]() [Html]()
 [Justification]() [Character Offsets]() [Keypress]()
 [Lexicon]() [Loops]() [Ngrams]()
 [Match-syntax]() [Match]() [Numbers]()
 [Performance]() [Nouns]() [Paragraphs]()
 [Plugins]() [Output]() [Scan]()
 [Projects]() [Selections]() [Sentences]()
 [Tagger]() [Sorting]() [Syllables]()
 [Tags]() [Split]() [Pronounce]()
 [Tokenization]() [Text]() [Strict]()
 [Named-Entities]() [Utils]() [Penn-tags]()
 [Whitespace]() [Verbs]() [Typeahead]()
 [World data]() [Normalization]() [Sweep]()
 [Fuzzy-matching]() [Typescript]() [Mutation]()
 [Root-forms]() 



##### Talks:

(#talks)

- **[Language as an Interface]()** - by Spencer Kelly
- **[Coding Chat Bots]()** - by KahWee Teng
- **[On Typing and data]()** - by Spencer Kelly

##### Articles:

(#articles)

- **[Geocoding Social Conversations with NLP and JavaScript](http://compromise.cool)** - by Microsoft
- **[Microservice Recipe]()** - by Eventn
- **[Adventure Game Sentence Parsing with Compromise]()**
- **[Building Text-Based Games]()** - by Matt Eland
- **[Fun with javascript in BigQuery]()** - by Felipe Hoffa
- **[Natural Language Processing\... in the Browser?]()** - by Charles Landau

##### Some fun Applications:

(#some-fun-applications)

- **[Automated Bechdel Test]()** - by The Guardian
- **[Story generation framework]()** - by Jose Phrocca
- **[Tumbler blog of lists]()** - horse-ebooks-like lists - by Michael Paulukonis
- **[Video Editing from Transcription]()** - by New Theory
- **[Browser extension Fact-checking]()** - by Alexander Kidd
- **[Siri shortcut]()** - by Michael Byrns
- **[Amazon skill]()** - by Tajddin Maghni
- **[Tasking Slack-bot]()** - by Kevin Suh [\[see more\]]()

##### Comparisons

(#comparisons)

- [Compromise and Spacy]()
- [Compromise and NLTK]()





### Plugins:

(#plugins)

These are some helpful extensions:

##### Dates

(#dates)

npm install compromise-dates

- **[.dates()]()** - find dates like June 8th or 03/03/18
 - **[.dates().get()]()** - simple start/end json result
 - **[.dates().json()]()** - overloaded output with date metadata
 - **[.dates().format(\'\')]()** - convert the dates to specific formats
 - **[.dates().toShortForm()]()** - convert \'Wednesday\' to \'Wed\', etc
 - **[.dates().toLongForm()]()** - convert \'Feb\' to \'February\', etc
- **[.durations()]()** - 2 weeks or 5mins
 - **[.durations().get()]()** - return simple json for duration
 - **[.durations().json()]()** - overloaded output with duration metadata
- **[.times()]()** - 4:30pm or half past five
 - **[.times().get()]()** - return simple json for times
 - **[.times().json()]()** - overloaded output with time metadata

##### Stats

(#stats)

npm install compromise-stats

- **[.tfidf()]()** - rank words by frequency and uniqueness

- **[.ngrams()]()** - list all repeating sub-phrases, by word-count

- **[.unigrams()]()** - n-grams with one word

- **[.bigrams()]()** - n-grams with two words

- **[.trigrams()]()** - n-grams with three words

- **[.startgrams()]()** - n-grams including the first term of a phrase

- **[.endgrams()]()** - n-grams including the last term of a phrase

- **[.edgegrams()]()** - n-grams including the first or last term of a phrase

##### Speech

(#speech)

npm install compromise-syllables

- **[.syllables()]()** - split each term by its typical pronunciation
- **[.soundsLike()]()** - produce a estimated pronunciation

##### Wikipedia

(#wikipedia)

npm install compromise-wikipedia

- **[.wikipedia()]()** - compressed article reconciliation



### Typescript

(#typescript)

we\'re committed to typescript/deno support, both in main and in the official-plugins:

 import nlp from 'compromise' 
 import stats from 'compromise-stats' 
 const nlpEx = nlp . extend ( stats ) 
 nlpEx ( 'This is type safe!' ) . ngrams ( ) 

[typescript docs]() 

#### Limitations:

(#limitations)

- **slash-support:** We currently split slashes up as different words, like we do for hyphens. so things like this don\'t work: nlp(\'the koala eats/shoots/leaves\').has(\'koala leaves\') //false

- **inter-sentence match:** By default, sentences are the top-level abstraction. Inter-sentence, or multi-sentence matches aren\'t supported without [a plugin]() : nlp(\"that\'s it. Back to Winnipeg!\").has(\'it back\')//false

- **nested match syntax:** the danger beauty of regex is that you can recurse indefinitely. Our match syntax is much weaker. Things like this are not *(yet)* possible: doc.match(\'(modern (major\|minor))? general\') complex matches must be achieved with successive **.match()** statements.

- **dependency parsing:** Proper sentence transformation requires understanding the [syntax tree]() of a sentence, which we don\'t currently do. We should! Help wanted with this.
