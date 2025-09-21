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
