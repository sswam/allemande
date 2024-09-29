# Handwriting Recognition

I haven't done much with handwriting recognition. I know that GPT 4o can understand handwriting in English at least. It might get expensive if we have large documents to process. A quick google search suggests "transkribus" and Google Document AI.

I also asked Perplexity (which has models that search for live results), it said this:

For handwriting recognition, there are several advanced AI solutions and some notable open-source options:

## Commercial and Advanced AI Solutions

### MyScript

MyScript uses proprietary AI technology to interpret handwritten content in over 70 languages, analyze the structure of handwritten notes, and recognize mathematical equations and musical notation. Their approach involves preprocessing handwritten content and using neural networks, particularly feedforward neural networks and techniques like Connectionist Temporal Classification (CTC).

### Instabase

Instabase leverages machine learning and large language models to enhance OCR output for handwriting recognition. Their AI Hub provides turnkey access to handwriting recognition and other AI capabilities, making it easier to convert handwritten documents into machine-readable text.

### Google Document AI

Google's Document AI is highly effective for handwritten text recognition without extensive training. However, it has limitations in importing and exporting functions due to its specific JSON format.

### Transkribus

Transkribus uses AI-powered handwriting recognition to decipher both handwritten historical documents and printed texts. It allows users to train custom AI models, which can significantly improve accuracy after manual training.

## Open Source and Community-Driven Solutions

### Transkribus

While not entirely open-source, Transkribus offers a significant amount of functionality for free and allows users to train and customize their own models. It has a large community and provides extensive tools for handwriting recognition, especially for historical documents.

### Pen2Txt

Pen2Txt is a community-driven project that aims to provide accurate transcription of handwritten documents using the latest AI technologies. It includes features like a correction chat box to improve accuracy and is noted for its performance in handling diverse handwriting styles.

## General Deep Learning Frameworks

For those looking to develop their own solutions, frameworks like TensorFlow or PyTorch can be used to build and train deep learning models such as Convolutional Neural Networks (CNNs) and Recurrent Neural Networks (RNNs), which are commonly used in handwriting recognition tasks.

## MNIST Dataset and Other Public Datasets

The MNIST dataset, among others, is frequently used for training and testing handwriting recognition models. These datasets are publicly available and can be used to develop and train custom models using various machine learning and deep learning techniques.
