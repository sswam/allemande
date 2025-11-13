# More shell, less egg

https://leancrew.com/all-this/2011/12/more-shell-less-egg/

*December 4, 2011 at 10:50 PM by Dr. Drang*

My [TextExpander/shell script post](http://www.leancrew.com/all-this/2011/12/erm/) of last week reminded me of [Doug McIlroy](http://en.wikipedia.org/wiki/Douglas_McIlroy) and some unfinished business from back in October. So let’s talk about shell scripts and Unix again.

In the comments to [my October post](http://en.wikipedia.org/wiki/Douglas_McIlroy) about the early Unix developers and what good writers they were, [Bill Cheswick](http://www.cheswick.com/ches/) mentioned Doug McIlroy, and said it was a shame I’d omitted him from the post. Bill was right; I should have included McIlroy. The problem was I couldn’t find a link to any of his writings.

I had an example of his writing—a good one—but it was on paper only. I still haven’t found an online copy of it, but it’s worth talking about anyway.

The piece requires a bit of backstory. Jon Bentley had a regular column called “Programming Pearls” in the *Communications of the ACM* (you may have come across [this collection](#) of some of his columns). In 1986 he got interested in literate programming, so he asked Donald Knuth to write a program in that style as a guest column and Doug McIlroy to write a literary-style critique of it.

Literate programming is an interesting topic in its own right. The idea, which originated with Knuth, is to write a program and its documentation at the same time, interleaved with each other. It’s not just writing good comments or including docstrings or using systems like POD. In literate programming, the code is subservient to the documentation. For example, the various sections of the code are written not in the order the compiler (or interpreter) wants them, but in the order most appropriate for the explanation. Two utility programs transform the combination file: one to typeset the documentation and the code via TeX, and the other to extract and rearrange the source code and send it to the compiler.

I’m interested in literate programming, but **that’s not our topic today.**

Both Knuth’s article/program and McIlroy’s critique were published in Bentley’s column and then republished in Knuth’s *Literate Programming* collection, a copy of which I happen to have picked up for a few bucks in a used book store several years ago.

---

## Literate Programming

The program Bentley asked Knuth to write is one that’s become familiar to people who use languages with serious text-handling capabilities: **Read a file of text, determine the n most frequently used words, and print out a sorted list of those words along with their frequencies.**

Knuth wrote his program in WEB, a literate programming system of his own devising that used Pascal as its programming language. His program used a clever, purpose-built data structure for keeping track of the words and frequency counts; and the article interleaved with it presented the program lucidly. McIlroy’s review started with an appreciation of Knuth’s presentation and the literate programming technique in general. He discussed the cleverness of the data structure and Knuth’s implementation, pointed out a bug or two, and made suggestions as to how the article could be improved.

And then he calmly and clearly eviscerated the very foundation of Knuth’s program.

What people remember about his review is that McIlroy wrote a six-command shell pipeline that was a complete (and bug-free) replacement for Knuth’s 10+ pages of Pascal. Here’s the script, with each command given its own line:

```
tr -cs A-Za-z '\n' |
tr A-Z a-z |
sort |
uniq -c |
sort -rn |
sed ${1}q
```

#### Without line numbers

And here’s McIlroy’s short, impossible-to-misunderstand explanation:

> If you are not a UNIX adept, you may need a little explanation, but not much, to understand this pipeline of processes. The plan is easy:
>
> - Make one-word lines by transliterating the complement (`-c`) of the alphabet into newlines (note the quoted newline), and squeezing out (`-s`) multiple newlines.
> - Transliterate upper case to lower case.
> - Sort to bring identical words together.
> - Replace each run of duplicate words with a single representative and include a count (`-c`).
> - Sort in reverse (`-r`) numeric (`-n`) order.
> - Pass through a stream editor; quit (`q`) after printing the number of lines designated by the script’s first parameter (`${1}`).

I need to put that on a Post-it note as an example of how to explain a script. The best part? It would fit on a Post-it note.

*(I can’t help wondering, though, why he didn’t use `head -${1}` in the last line. It seems more natural than `sed`. Is it possible that `head` hadn’t been written yet?)*

---

**Update 12/8/11**
Thanks to Terry and Dan in the comments for pointing out the typos in the excerpt above. The mistakes were mine, not McIlroy’s, and are fixed now.

---

What’s often overlooked when this review is discussed is McIlroy’s explanation of why his solution is better—and it’s not just because it’s shorter. Here are some excerpts:

> A wise engineering solution would produce—or better, exploit—reusable parts.

> Very few people can obtain the virtuoso services of Knuth (or afford the equivalent person-weeks of lesser personnel) to attack nonce problems such as Bentley’s from the ground up. But old UNIX hands know instinctively how to solve this one in a jiffy.

> To return to Knuth’s paper: Everything there—even input conversion and sorting—is programmed monolithically and from scratch. In particular the isolation of words, the handling of punctuation, and the treatment of case distinctions are built in. Even if data-filtering programs for these exact purposes were not at hand, these operations would well be implemented separately: for separation of concerns, for easier development, for piecewise debugging, and for potential reuse.

> The simple pipeline given above will suffice to get answers right now, not next week or next month. It could well be enough to finish the job. But even for a production project, say for the Library of Congress, it would make a handsome down payment, useful for testing the value of the answers and for smoking out follow-on questions.

McIlroy’s review is both an explanation and an exemplar of the Unix Way: small programs that do elementary tasks, but which are written so they can be combined in complex ways.

I can’t help but include one more excerpt. It’s the last paragraph of the review:

> Knuth has shown us here how to program intelligibly, but not wisely. I buy the discipline. I do not buy the result. He has fashioned a sort of industrial-strength Fabergé egg—intricate, wonderfully worked, refined beyond all ordinary desires, a museum piece from the start.

Just remember, he’s saying this about *Donald Knuth*.

No Fabergé eggs for McIlroy.
Just brass balls.
