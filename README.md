# LLM Application - Context based Subtitle Generation

Large language models (LLM) are good at transforming language sequence. Not only can it transform sequence, it can also take additional input (context) to fine tune the output.

Subtitle generation, from a high level, can be divided into 2 steps:
- Transcription: Converting audio to text in its original language
- Translation: Converting the text from one language to another

They are both sequence transformation (what LLM is good at). And with additional context, we might be able to improve quality of subtitle.

In the following, we will use 2 excerpts from "Attack on Titan" as an example to experiment LLM subtitle generation.

Clip 01: 
- Source: `[Skymoon-Raws] Shingeki no Kyojin S4 - 05 [ViuTV][WEB-DL][1080p][AVC AAC].mp4`
- Time code: 03:32 - 04:32

## Preparing Context

Imagine you are a secretary to a medical doctor. You are asked to prepare a transcript of a meeting with a pharmaceutical sales. Without any background in medicine, very likely you will find it difficult to keep up. You may not know spelling of drug names or meaning of medical terms. Same with transcribing videoes of fiction. Without any context, it is hard to get the names right. 

We need a way to get a list of character names and Wikipedia could be a good source. 

Here is the logic of the crawler:

Given the title of the fiction work.

1. Open the Wikipedia entry.
2. Look at `Template` tags that contain multiple texts in multiple languages side by side (e.g. `nihongo`). Extract the texts as they are very likely to be special names of the fiction.
3. List out links to other Wikipedia entries (e.g. `main`, `see`, `further` tags), ask LLM if there is any of them relevant to list of characters.
4. If there is such entry, go to the entry, perform #2.

## Transcription & Translation
Once we have prepared the context, we can try out the LLM and evaluate the performance. 

- Baseline model: Google Cloud Speech API & Translate API
- Open AI: Whisper (medium model) & ChatGpt API (gpt-3.5-turbo)

To evaluate model output, a score of 2 marks is assigned for each line:
1. whether the meaning is comparable to the original sentence (2 marks). If the meaning match exactly the original 2 marks. It the meaning is irrelavent to the original, 0 mark. Otherwise 1 mark.
2. whether the the sentence is grammatically correct (-1 mark if grammatically incorrect)
3. whether the names mentioned are accurate (-1 mark if inaccurate)


e.g. if the below sentence is mentioned:
`Hi <Name of character A>, please help <character B> carry the heavy goods`
and the model output:
`<character A, mispelled>, <character B> to move please assist`

This deserve 1 mark, as it carries similar meaning (not exactly, as missing "heavy"), but grammatically incorrect and the name is inaccurate. 

The average score is reported in [/result/clip_01/result.csv](/result/clip_01/result.csv).

A few observations here:
1. It seems additional contexts have no effect on Google Cloud Speech and Translation output.
2. Whisper + OpenAI seems to have higher quality transcription and translation even not considering context.
3. Whisper + OpenAI is able to enhance its output with context.

## How to improve translation performance?

1. Include examples in the prompt.

See: [Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165)

2. Create your own fine tuned model.

See: [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155)

This paper includes all the details of training InstructGPT, the predecessor of ChatGPT. Basically it is trained by:
1. Collect sample input and desired output to fine tune GPT-3 in a supervised manner.
2. In parallel, construct a reward model, by sampling prompts and several model outputs and have labelers rank the outputs.
3. Use the reward model to further optimise the fine turned GPT-3 model in an unsupervised manner.

This can be a potential way to construct a Chat Completion model in your own domain.

The reward model is also useful for combining output from different LLM models.

## Side Note: LLM Usage Tips
1. Divide and conquer. There is a token limit per request. So we need to properly batch the requests.
2. Index your individual request items in a batch.
3. Ask for a simple formatted response like JSON/direct answer without additional explanation. 
