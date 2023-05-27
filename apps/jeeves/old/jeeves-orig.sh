#!/bin/bash -eu
# jeeves-orig.sh: generate legal documents, these shell commands were the original version of the general purpose jeeves tool

1s "GPT-4 AI LLM onselling, legal document thorough and well written as if by a top queens counsel" | tee service-agreement-1.txt

query "Please write a service agreement for GPT-4 AI LLM onselling, legal document thorough and well written as if by a top queens counsel" | tee service-agreement-1.txt
< service-agreement.txt gpt process "Please finish writing this service agreement for GPT-4 AI LLM onselling, legal document thorough and well written as if by a top queens counsel" | tee service-agreement-2.txt

cat-sections service-agreement-1.txt service-agreement-2.txt > service-agreement.txt

query "I am starting an AI consulting and SaaS services business in Melbourne, Australia, with international clients (in the USA, EU, Australia, NZ, China and elsewhere). We also want to provide chat and social media services. Please write my a step by step nested plan or tasks list, in markdown, for all my legal obligations; such as service agreement, privacy policy, terms of service, etc. Please write it as if planned by a top queens counsel. Just write the list of documents and requirements, do not write the actual documents yet." | tee legal-plan-1.txt
