# ShabdSetu– Dying Dialects Dilemma

## 📖 Project Overview

ShadbdSetu is a **gamified Indian language learning and dialect preservation platform** built by Team BisiGitBaath. The project addresses two major issues:

1. **Lack of interactive tools** for learning Indian languages with pronunciation and conversational practice.
2. **Dying dialects** – many Indian dialects are disappearing rapidly due to lack of documentation and oral-only traditions.

Our mission is to combine **learning with preservation**, enabling users to not only learn Indian languages but also actively participate in documenting and safeguarding their native dialects.

---

## ✨ Features

* **Language Learning Mode**

  * Daily lessons & tests across multiple Indian languages (Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Gujarati, Marathi, etc.).
  * Gamification: keys, streak points, badges, leaderboards, quests & challenges.
  * AI-powered pronunciation evaluator with real-time feedback using **AI4Bharat** models.

* **Dialect Preservation Mode**

  * Users can record words, phrases, idioms, and contextual expressions in local dialects.
  * AI4Bharat’s **ASR (Automatic Speech Recognition)** transcribes and identifies rare dialect contributions.
  * Contributions validated by community members and experts before being added to the **Crowdsourced Digital Dialect Dictionary**.
  * Gamified contributions – badges, recognition, and leaderboard rewards.

* **Voice-based Roleplay Lessons** for natural practice.

* **Pronunciation Scoring & Feedback** at phoneme-level accuracy.

* **Community-driven archive** of endangered dialects.

* **Multi-language learning paths** customized to the learner’s mother tongue.

---

## 🛠 Tech Stack

* **Frontend (Web):** React / Next.js
* **Frontend (Android):** Kotlin + Jetpack Compose
* **Backend:** FastAPI on Google Cloud Run
* **Database:** PostgreSQL on Supabase
* **AI Models:** [AI4Bharat](https://ai4bharat.iitm.ac.in/) (ASR, IndicTrans2, IndicTTS)
* **Deployment:** Docker + Google Cloud

---

## 🚀 Workflows

### Learning Mode Workflow

1. User logs in & selects target language & lessons.
2. User speaks displayed phrases.
3. AI4Bharat ASR processes input → converts to text.
4. Pronunciation Evaluator gives instant feedback.
5. Gamification (XP, badges, streaks) motivates progress.
6. IndicTTS plays back correct pronunciation.

### Documenting Mode Workflow

1. User records dialect word/phrase with metadata.
2. AI4Bharat ASR transcribes & detects new/rare dialects.
3. Audio + transcription stored in **Dialect Database**.
4. Experts & community validate contributions.
5. Verified entries added to **Dialect Dictionary**.
6. Contributors earn badges & recognition.

---

## 💡 Novelty & Impact

* India-first **gamified learning + dialect preservation** platform.
* End-to-end **Indic AI stack** integration.
* Sustainable **community-driven dialect preservation**.
* Future generations can access preserved dialects & cultural content.

---

BhashaBuddy API Endpoint ReferenceThis document provides the curl.exe commands to test all endpoints of the BhashaBuddy API.Prerequisite: Before running any of these commands, ensure your Python server is running in PyCharm.Part 1: Learning Mode CommandsA. Fetching Lesson ContentThese commands allow you to navigate the structured curriculum.1. Get All Learning CategoriesReturns a list of all main learning categories (e.g., "Greetings", "Basic Grammar").curl.exe "[http://127.0.0.1:8001/api/v1/learning/categories](http://127.0.0.1:8001/api/v1/learning/categories)"
2. Get Lessons for a Specific CategoryReturns a list of lessons within a given category. Use the id from the previous command (e.g., 1 for "Greetings").curl.exe "[http://127.0.0.1:8001/api/v1/learning/lessons/1](http://127.0.0.1:8001/api/v1/learning/lessons/1)"
3. Get Phrases for a Specific LessonReturns a list of practice phrases for a given lesson. Use the id from the previous command (e.g., 1 for "Formal Greetings").curl.exe "[http://127.0.0.1:8001/api/v1/learning/phrases/1](http://127.0.0.1:8001/api/v1/learning/phrases/1)"
B. Evaluating Pronunciation (Score & Feedback)This endpoint takes a user's audio and evaluates it against a specific phrase from the database.Prerequisite: A .wav file named test_hindi.wav (recording of "नमस्ते") must be in your project folder.Target: Evaluates against the phrase with ID HIN_GREET_01 ("नमस्ते").curl.exe -X POST "[http://127.0.0.1:8001/api/v1/learning/evaluate](http://127.0.0.1:8001/api/v1/learning/evaluate)" `
-H "accept: application/json" `
-F "lang=hi" `
-F "phrase_id=HIN_GREET_01" `
-F "audio_file=@test_hindi.wav"
Part 2: Documenting Mode CommandsA. Contributing a "Common" WordThis tests the contribution of a word that already exists in the dictionary. The API should respond with "is_rare_candidate": false.Prerequisite: A .wav file named test_namaste_contribution.wav (recording of "नमस्ते") must be in your project folder.curl.exe -X POST "[http://127.0.0.1:8001/api/v1/dialects/contribute](http://127.0.0.1:8001/api/v1/dialects/contribute)" `
-F "lang=hi" `
-F "user_spelling=नमस्ते" `
-F "meaning=A respectful greeting" `
-F "region=General" `
-F "audio_file=@test_namaste_contribution.wav"
B. Contributing a "Rare" WordThis tests the contribution of a new word. The API should flag it with "is_rare_candidate": true and set its status to pending_expert_validation.Prerequisite: A .wav file named test_shukriya_contribution.wav (recording of "शुक्रिया") must be in your project folder.curl.exe -X POST "[http://127.0.0.1:8001/api/v1/dialects/contribute](http://127.0.0.1:8001/api/v1/dialects/contribute)" `
-F "lang=hi" `
-F "user_spelling=शुक्रिया" `
-F "meaning=Thank you" `
-F "region=Urdu Influence" `
-F "audio_file=@test_shukriya_contribution.wav"




