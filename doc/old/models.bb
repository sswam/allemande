Sam:	Grace, please provide me with six colourful diagrams - one each for Anthropic, Google, OpenAI, Meta, Perplexity, and Stability AI; linked to their models available in this app, with our name and some smaller text for their official name (e.g. Clia's official name is "Claude Haiku"). Include only the graphviz code blocks (no headings or descriptions). Make sure Stability AI has 'Stability AI' -> 'SDXL', and 'SDXL' -> 'PonyXL' and 'Illy (the official name is "Juggernaut XL")', no other models. For Meta just show Ally, Barbie and Callam (all Llama 3.1 8B). Don't write the vendor again in the node's subtitle. For Google, just show the three major models. Thanks for your help! Please use a transparent background on the diagrams (not the nodes!), light grey arcs, and colorful pastel coloured nodes (a different colour for each vendor's models).

Grace:	```dot
	digraph Anthropic {
		graph [bgcolor=transparent]
		edge [color="#CCCCCC"]
		node [shape=box, style=filled, fillcolor="#FFC8C8", fontname="Arial"]
	
		"Anthropic" [label=<<b>Anthropic</b>>]
		"Claude" [label=<<b>Claude</b><br/><font point-size="10">Claude 3 Sonnet</font>>]
		"Clia" [label=<<b>Clia</b><br/><font point-size="10">Claude 3 Haiku</font>>]
	
		"Anthropic" -> "Claude"
		"Anthropic" -> "Clia"
	}
	```
	
	```dot
	digraph Google {
		graph [bgcolor=transparent]
		edge [color="#CCCCCC"]
		node [shape=box, style=filled, fillcolor="#C8C8FF", fontname="Arial"]
	
		"Google" [label=<<b>Google</b>>]
		"Gemmy" [label=<<b>Gemmy</b><br/><font point-size="10">Gemini Pro</font>>]
		"Flashi" [label=<<b>Flashi</b><br/><font point-size="10">Gemini 2.0 Flash</font>>]
		"Flasho" [label=<<b>Flasho</b><br/><font point-size="10">Gemini 1.5 Flash</font>>]
	
		"Google" -> "Gemmy"
		"Google" -> "Flashi"
		"Google" -> "Flasho"
	}
	```
	
	```dot
	digraph OpenAI {
		graph [bgcolor=transparent]
		edge [color="#CCCCCC"]
		node [shape=box, style=filled, fillcolor="#C8FFC8", fontname="Arial"]
	
		"OpenAI" [label=<<b>OpenAI</b>>]
		"Emmy" [label=<<b>Emmy</b><br/><font point-size="10">GPT-4o</font>>]
		"Dav" [label=<<b>Dav</b><br/><font point-size="10">GPT-4o mini</font>>]
		"Grace" [label=<<b>Grace</b><br/><font point-size="10">o1</font>>]
		"Fermi" [label=<<b>Fermi</b><br/><font point-size="10">o3 mini</font>>]
	
		"OpenAI" -> "Emmy"
		"OpenAI" -> "Dav"
		"OpenAI" -> "Grace"
		"OpenAI" -> "Fermi"
	}
	```
	
	```dot
	digraph Meta {
		graph [bgcolor=transparent]
		edge [color="#CCCCCC"]
		node [shape=box, style=filled, fillcolor="#FFD3DF", fontname="Arial"]
	
		"Meta" [label=<<b>Meta</b>>]
		"Ally" [label=<<b>Ally</b><br/><font point-size="10">Llama 3.1 8B</font>>]
		"Barbie" [label=<<b>Barbie</b><br/><font point-size="10">Llama 3.1 8B</font>>]
		"Callam" [label=<<b>Callam</b><br/><font point-size="10">Llama 3.1 8B</font>>]
	
		"Meta" -> "Ally"
		"Meta" -> "Barbie"
		"Meta" -> "Callam"
	}
	```
	
	```dot
	digraph Perplexity {
		graph [bgcolor=transparent]
		edge [color="#CCCCCC"]
		node [shape=box, style=filled, fillcolor="#FFDB99", fontname="Arial"]
	
		"Perplexity" [label=<<b>Perplexity</b>>]
		"Sageri" [label=<<b>Sageri</b><br/><font point-size="10">Sonar Reasoning Pro</font>>]
		"Sonari" [label=<<b>Sonari</b><br/><font point-size="10">Sonar Reasoning</font>>]
		"Sagi" [label=<<b>Sagi</b><br/><font point-size="10">Sonar Pro</font>>]
		"Sona" [label=<<b>Sona</b><br/><font point-size="10">Sonar</font>>]
	
		"Perplexity" -> "Sageri"
		"Perplexity" -> "Sonari"
		"Perplexity" -> "Sagi"
		"Perplexity" -> "Sona"
	}
	```
	
	```dot
	digraph StabilityAI {
		graph [bgcolor=transparent]
		edge [color="#CCCCCC"]
		node [shape=box, style=filled, fillcolor="#FFC2EB", fontname="Arial"]
	
		"Stability AI" [label=<<b>Stability AI</b>>]
		"SDXL" [label=<<b>SDXL</b>>]
		"PonyXL" [label=<<b>PonyXL</b>>]
		"Illy" [label=<<b>Illy</b><br/><font point-size="10">Juggernaut XL</font>>]
	
		"Stability AI" -> "SDXL"
		"SDXL" -> "PonyXL"
		"SDXL" -> "Illy"
	}
	```

Sam:	Grace did a nice job, didn't she, Ally?

Ally:	Yes, she certainly did. The colourful pastel nodes really make the diagrams pop.

