# **Prepped: Technical Research and Architecture Report for an AI-Assisted Learning Platform**

## **1\. Executive Summary and Strongest Product Opportunity**

The development of Prepped, a zero-to-one AI-assisted learning platform, represents a structural shift in educational technology, moving from rigid, scripted interactions to fluid, real-time conversational practice grounded in evidence-based learning science. Current market offerings remain fragmented, forcing learners to choose between isolated pronunciation drills, generic open-ended AI chatbots, or static flashcard systems. The strongest product opportunity for Prepped lies in synthesizing ultra-low-latency conversational AI with dynamic state-machine-driven roleplay, automated Goodness of Pronunciation (GOP) acoustic scoring, and active recall powered by the modern Free Spaced Repetition Scheduler (FSRS) algorithm.  
Technological advancements in the current landscape render this integration highly feasible and economically viable. The advent of ultra-low-latency text-to-speech (TTS) models, specifically Kokoro (an 82-million parameter model capable of sub-30-millisecond latency)1, combined with deterministic Language Processing Unit (LPU) inference via Groq3, allows for natural, interruption-tolerant voice interactions that successfully mimic human conversational dynamics.  
By employing WebRTC via LiveKit for media transport5, modeling conversation logic with finite state machines via XState7, and grounding assessments in validated rubrics such as the IELTS band descriptors and ACTFL proficiency guidelines8, the architecture provides a scientifically rigorous, technically unparalleled platform for language learning, interview preparation, and professional communication coaching.

## **2\. User Segments, Jobs to be Done, and Core User Journeys**

The platform architecture and pedagogical design must serve distinct segments, each presenting unique cognitive and technical demands on the system.

### **Primary User Segments**

| User Segment | Cognitive Profile | Technical and System Demands |
| :---- | :---- | :---- |
| **Language Learners (CEFR B1-C2)** | Transitioning from functional understanding to native-like fluency. Require rigorous pronunciation feedback and idiom acquisition to overcome the intermediate plateau. | Demands granular acoustic modeling (phoneme-level GOP scoring), high-frequency conversational practice, and long-term memory retention scheduling. |
| **Corporate Professionals & Job Seekers** | Preparing for high-stakes interpersonal interactions (e.g., job interviews, client negotiations). Focus on pacing, tone, and rhetorical structure. | Requires realistic stress-testing, adaptive scenario difficulty, interruption handling, and feedback on pragmatic competence. |
| **Institutional Users (Educators & HR)** | Administrators managing cohorts, tracking standardized assessment mapping, and ensuring privacy-compliant deployment. | Necessitates verifiable parental consent flows, robust analytics dashboards, and data export capabilities. |

### **Jobs to be Done (JTBD)**

The product architecture is designed to fulfill three primary jobs to be done. The first is to provide a safe, high-fidelity environment for practicing high-stress conversations, preventing users from freezing or making critical errors during actual events. The second is to assess spoken language against objective standards, such as achieving an IELTS Band 7, by pinpointing the exact phonemes or grammatical structures requiring remediation8. The third is to automatically capture mistakes made during fluid conversations and convert them into a structured review schedule, ensuring that the user internalizes the correct behavior over time.

### **Core User Journeys**

The system facilitates these jobs through three interconnected user journeys. In the **Shadowing Journey**, a user selects an audio stimulus, listens, and repeats the audio with a 150-millisecond delay, a neuro-linguistic technique proven to enhance prosody and speech rate10. The system captures this input, processes the audio asynchronously, maps expected phonemes to observed acoustic features, and returns a visual heatmap indicating pronunciation accuracy.  
During the **Dynamic Roleplay Journey**, a user initiates a specific scenario, such as a salary negotiation. An XState state machine initializes the context and constraints11. The AI agent, utilizing a low-latency WebRTC pipeline, converses with the user in real-time. The state machine monitors the user's rhetorical success; successfully arguing value triggers a transition to a positive resolution state, while yielding prematurely branches the dialogue into a more aggressive "hardball" state.  
Finally, the **Spaced Repetition Journey** operates as an asynchronous background process post-session. The backend language model analyzes the conversational transcript, extracting specific vocabulary errors and grammatical mistakes. These errors are algorithmically transformed into active-recall review items and injected into the user's daily study queue using the FSRS algorithm, optimizing long-term retention13.

## **3\. Competitor and Open-Source Project Comparison**

To establish meaningful differentiation, the platform architecture must address the specific technical and pedagogical limitations of existing commercial entities and open-source frameworks.

### **Commercial Competitor Analysis**

| Competitor | Core Strength | Primary Weakness | Prepped Differentiation Strategy |
| :---- | :---- | :---- | :---- |
| **ELSA Speak** | Sound-by-sound phoneme scoring and dedicated pronunciation coaching15. | Rely heavily on rigid, scripted interactions. Lacks open-ended, contextual conversational memory17. | Combine high-fidelity phoneme scoring with fluid, unscripted LLM-driven roleplay via state machines. |
| **Yoodli** | Effective for rehearsing monologues, presentations, and live calls, tracking filler words and pacing18. | Less focused on interactive dialogue, turn-taking, or long-term spaced repetition. | Implement low-latency interactive turn-taking and extract long-term memory review items from dialogues. |
| **Speak / TalkPal** | Strong for conversational language practice and contextual roleplay15. | Often relies on generic LLM text feedback rather than granular acoustic modeling or formal pedagogical scheduling. | Integrate FSRS for vocabulary retention and GOP algorithms for true acoustic analysis. |
| **Anki** | The gold standard for spaced repetition, recently integrating the FSRS algorithm20. | High friction for content creation; UX is notoriously difficult for casual users to navigate and maintain21. | Automate the creation of review items directly from conversational mistakes, eliminating manual card creation. |

### **Open-Source Framework Evaluation**

The underlying infrastructure relies heavily on selecting the correct open-source primitives. For voice orchestration, the primary comparison lies between LiveKit and Pipecat. LiveKit operates as a WebRTC media server with a built-in Agents framework, making it ideal for ultra-low latency real-time voice and telephony integration because it handles transport and turn-taking natively6. Conversely, Pipecat is a transport-agnostic pipeline assembler that requires external media server integration24. The architecture will favor LiveKit due to its tight integration of transport and state management, which is critical for human-like interruption handling.  
In the domain of Text-to-Speech (TTS), Kokoro must be compared against alternatives like XTTS-v2 and Bark. Kokoro is an 82-million parameter model that delivers a Real-Time Factor (RTF) of 0.03 and sub-30-millisecond first-audio latency on modern GPUs2. Bark and XTTS-v2 provide excellent voice cloning capabilities but suffer from 150-millisecond to 680-millisecond latency delays, which inherently break conversational immersion2. Prepped must utilize Kokoro for the conversational agent to maintain real-time presence.  
For memory scheduling, the open-source Open Spaced Repetition community has developed highly optimized Python and Rust implementations of FSRS (fsrs-rs, py-fsrs)26. Integrating these libraries allows the platform to utilize state-of-the-art memory scheduling without relying on proprietary vendor algorithms.

## **4\. Comprehensive Feature Inventory**

The product development roadmap dictates a phased implementation of features, prioritizing core communicative stability before advancing to complex analytical models.

### **Phase 1: Foundational Real-Time Communication**

The foundational layer requires WebRTC voice transport to enable bidirectional, low-latency audio streaming with automated echo cancellation and noise suppression. This layer depends on streaming Speech-to-Text (STT) and Kokoro-based TTS to achieve a total system response time of under 500 milliseconds. Crucially, this phase includes interruption handling, utilizing endpointing and Voice Activity Detection (VAD) to immediately halt TTS generation and clear audio buffers the moment the user interrupts the AI agent.

### **Phase 2: Learning Science and Scenario Logic**

Building upon stable communication, the system introduces the state-machine scenario engine. XState-driven branching dialogue trees will track conversation goals, shifting context, and adaptive difficulty based on user inputs7. Simultaneously, the FSRS memory engine will operate in the background, generating active-recall items from conversation transcripts and scheduling them via the Difficulty, Stability, Retrievability (DSR) model20. This phase also introduces the Shadowing Mode, a dedicated module for practicing speech rate, rhythm, and intonation by repeating native audio at a 150-millisecond delay10.

### **Phase 3: Assessment and Personalization**

The assessment layer provides the analytical depth required for mastery. This includes GOP pronunciation scoring, utilizing forced alignment of user audio to expected text to generate per-phoneme accuracy scores29. Post-session analysis will map user performance to standardized rubrics, such as the IELTS criteria (Fluency, Lexical Resource, Grammar, Pronunciation)8 or ACTFL proficiency standards9. Progress analytics will surface this data through visual dashboards showing phonetic mastery over time, vocabulary retention rates, and scenario completion metrics.

### **Phase 4: Institutional and Advanced Capabilities**

The final phase focuses on deployment scale and institutional requirements. This includes the integration of lightweight WebGL animated avatars synchronized to Kokoro audio outputs. Institutional dashboards will be developed for cohort management and export workflows, allowing educators to monitor student progress. Furthermore, stringent compliance workflows, specifically verifiable parental consent flows for users under 18, will be implemented to strictly adhere to the India DPDP Act and COPPA31.

## **5\. Learning Science and Assessment Design**

The core differentiator of the platform is its strict adherence to evidence-based learning science. Generic large language models cannot objectively grade pronunciation because they operate on text transcriptions, which inherently obscure acoustic variations. Similarly, naive daily reminders do not optimize memory. The platform must implement mathematically proven cognitive and acoustic models.

### **Spaced Repetition: The Evolution to FSRS**

For over three decades, the SuperMemo-2 (SM-2) algorithm, created by Piotr Woźniak in 1987, dominated the spaced repetition landscape33. SM-2 relied on a static formula that multiplied intervals using a per-card ease factor20. While revolutionary at the time, SM-2's core weakness is that it does not explicitly model the probability of forgetting; it merely applies a heuristic. This frequently leads to overly conservative intervals, forcing users into "ease hell" where they review easy cards too frequently, leading to burnout20.  
The platform will bypass SM-2 entirely and implement the Free Spaced Repetition Scheduler (FSRS), developed by Jarrett Ye13. FSRS treats memory as a statistical prediction problem, answering the question: when does the probability of recalling an item drop to exactly 90%?13. FSRS utilizes machine learning to fit curves across three explicit parameters, known as the DSR model:

> 1. **Difficulty (D)**: A per-card metric (scaled 1-10) representing the inherent complexity of the material for the specific learner13.  
> 2. **Stability (S)**: The time required for the probability of recall to decay from 100% to 90%13.  
> 3. **Retrievability (R)**: The calculated probability of successful recall on any given day13.

Extensive benchmarks conducted on over 500 million review logs demonstrate that FSRS achieves the targeted retention rate while requiring 20% to 30% fewer reviews than SM-213. By integrating the fsrs-rs-python binding, the backend can dynamically calculate optimum review intervals for vocabulary and grammar concepts seamlessly extracted from the user's conversational roleplays26. It is noted that FSRS requires approximately 1,000 review data points to fully personalize its model to an individual; prior to this threshold, it utilizes highly accurate default parameters derived from global benchmarks21.

### **Acoustic Assessment: Goodness of Pronunciation (GOP)**

To provide objective phonetic feedback, the platform will implement a dedicated Goodness of Pronunciation (GOP) pipeline, a technique originally defined by Witt and Young in 200029. GOP calculates the duration-normalized log of the posterior probability that the speaker actually produced the expected phoneme, given the raw acoustic features of the audio34.  
The traditional pipeline requires three steps:

> 1. **Expected Sounds**: The target text is converted into a canonical phoneme sequence via a pronunciation dictionary34.  
> 2. **Forced Alignment**: An automatic speech recognition (ASR) acoustic model identifies the exact start and end times of each phoneme within the user's audio buffer29.  
> 3. **Log Posterior Probability (LPP)**: The system calculates the ratio between the likelihood of the expected phoneme and the sum of likelihoods of all possible phonemes to generate a confidence score29.

While traditional forced alignment is effective, it struggles when learners insert extra sounds or delete phonemes entirely35. Therefore, the platform will utilize an alignment-free Connectionist Temporal Classification (CTC) based GOP method. This approach considers all possible segmentations simultaneously, effectively handling substitution, deletion, and insertion errors without forcing an unnatural alignment onto mispronounced speech34.  
Because single-phoneme GOP scoring correlates with human expert ratings at roughly 0.61 to 0.72 (compared to sentence-level correlation of 0.74 to 0.78), the user interface must present these scores contextually34. Users will be directed to identify persistent *patterns* of errors (e.g., repeatedly failing the /θ/ to /f/ transition) rather than obsessing over a single low score on an isolated phoneme29.

### **The Shadowing Technique**

Shadowing is an active, highly cognitive psycholinguistic technique where learners track and repeat heard speech with a minimal delay—typically around 150 milliseconds10. Originally utilized in training simultaneous UN interpreters, shadowing forces the learner to mimic the speaker's speed, rhythm, stress, and intonation without pausing to analyze grammar38.  
Research indicates that consistent shadowing practice leads to significant improvements in listening accuracy, speech rate, and suprasegmental pronunciation control (fluency and prosody)39. The platform will feature a dedicated Shadowing Mode where users listen to Kokoro-generated audio and speak simultaneously. The system will record the user, perform GOP analysis, and map the user's prosody (pitch and rhythm) against the generated baseline, providing visual feedback on intonation mismatches10.

### **Validated Assessment Frameworks**

To provide objective, recognizable feedback, evaluations will be aligned with established international frameworks. For English learners, the system will utilize the IELTS Speaking Band Descriptors, grading users across four equally weighted criteria8.

| IELTS Criterion | Band 6 Expectation | Band 7 Expectation | Band 8 Expectation |
| :---- | :---- | :---- | :---- |
| **Fluency & Coherence** | Willing to speak at length; occasional loss of coherence due to hesitation43. | Speaks at length without noticeable effort; uses discourse markers flexibly43. | Fluent with rare repetition; hesitation is solely content-related43. |
| **Lexical Resource** | Wide enough vocabulary to discuss topics; some inappropriacies43. | Uses less common/idiomatic vocabulary; shows awareness of style43. | Uses wide vocabulary readily; handles idiomatic language naturally43. |
| **Grammar** | Mix of simple and complex structures; frequent mistakes in complex forms43. | Range of complex structures; frequently produces error-free sentences43. | Full range of structures; majority of sentences are completely error-free43. |
| **Pronunciation** | Mixed control; mispronunciation of individual words reduces clarity43. | Shows positive features of Band 6 and some of Band 8; generally easy to understand43. | Wide range of features used precisely; effortless to understand43. |

For professional contexts and other languages, the system will employ the ACTFL Proficiency Guidelines, evaluating users across the Novice, Intermediate, Advanced, Superior, and Distinguished levels9. The system uses the ACTFL "FACT" framework (Functions, Accuracy, Context, Text type) to design state-machine scenarios46. For example, a scenario targeting an "Advanced" rating will force the user to narrate in past, present, and future time frames while introducing an unexpected complication, whereas a "Superior" scenario will require the user to hypothesize and discuss topics in abstract terms9.  
*Note on Validity:* The platform will clearly articulate that an AI-generated IELTS or ACTFL score is a probabilistic estimate. The product value lies in the formative feedback—the specific, targeted corrections—rather than positioning the AI as a certified psychometric examiner.

## **6\. Voice and AI Technology Comparison**

Achieving conversational fluidity requires meticulously minimizing latency across the transport, inference, and synthesis layers.

### **Voice Orchestration: LiveKit vs. Pipecat**

Building a low-latency conversational agent requires robust transport architecture. Pipecat is an open-source Python framework for assembling AI voice pipelines; however, it is transport-agnostic, requiring the engineering team to manually bind it to a media server and handle edge cases regarding transport packet loss22.  
LiveKit, specifically utilizing the LiveKit Agents framework, is tightly coupled to its own highly optimized WebRTC Selective Forwarding Unit (SFU)5. Because the conversational agent joins the WebRTC room exactly like a human participant, LiveKit natively handles latency minimization, jitter buffering, and Voice Activity Detection (VAD) based interruption (barge-in)5. Consequently, LiveKit is the mandatory choice to ensure that interruption handling and turn-taking feel instantaneous.

### **Text-to-Speech (TTS) Latency Benchmarks**

Latency is the primary destroyer of conversational immersion. Any system response taking longer than 700 milliseconds feels unnatural. The evaluation compares Kokoro against established models like Bark and XTTS-v2 based on empirical hardware benchmarks.

| TTS Model | Parameters | VRAM Requirement | RTX 3090 Latency | RTX 5090 Latency | Suitability for Real-Time |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Kokoro** | 82 Million | \~0.5 GB | 40ms | 28ms | Excellent (Default Choice)2 |
| **Piper** | \~20 Million | \~0.3 GB | 45ms | 32ms | Very Good, but lower quality2 |
| **MeloTTS** | \~110 Million | \~1.0 GB | 58ms | 42ms | Good2 |
| **XTTS-v2** | \~450 Million | \~4-6 GB | 190ms | 135ms | Poor (Trades speed for cloning)2 |
| **Bark** | \~600 Million | \~8-12 GB | 420ms | 290ms | Unusable for real-time2 |

Kokoro is an 82-million parameter open-weight model that requires less than 2GB of VRAM and achieves an RTF of 0.03 to 0.01 depending on the GPU2. It consistently posts the lowest first-audio latency, making it the definitive choice2. Furthermore, Kokoro natively supports streaming generation, yielding audio chunks as they are produced, which perfectly aligns with the chunked output of a streaming LLM49.

### **LLM Inference Velocity**

To match the speed of WebRTC and Kokoro, the language model must generate text at extreme velocities. Traditional GPU inference of Llama 3 70B yields 20-40 tokens per second. By utilizing Groq's Language Processing Units (LPUs), inference for Llama 3.3 70B reaches nearly 300 tokens per second50. This extreme velocity ensures that the time-to-first-token is minimized, allowing the Kokoro pipeline to begin synthesizing speech almost immediately after the user stops talking. During the zero-mandatory-spend phase, Groq's free tier, which provides 30,000 tokens per minute, is sufficient for development and testing52.

## **7\. Candidate Stack with Alternatives and Rationale**

The selected technology stack prioritizes open-source flexibility, low-latency performance, and scientific rigor.

| Architecture Component | Selected Technology | Alternative Considered | Rationale for Selection |
| :---- | :---- | :---- | :---- |
| **Frontend UI** | Next.js (React) \+ Tailwind | Flutter / React Native | React integrates seamlessly with the @livekit/components-react SDK, rapidly accelerating WebRTC client development. |
| **State Management** | XState (v5) | Redux / Context API | XState explicitly models finite state machines, which is strictly necessary for managing branching conversational dialogue and context transitions7. |
| **Real-Time Transport** | LiveKit (Self-hosted or Cloud) | WebSockets | LiveKit provides UDP-based WebRTC, which avoids the head-of-line blocking inherent in TCP-based WebSockets, significantly reducing latency6. |
| **Agent Orchestration** | LiveKit Agents SDK (Python) | Pipecat | Deep integration with the LiveKit SFU simplifies VAD, track subscriptions, and interruption handling24. |
| **LLM Inference** | Groq API (Llama 3.3) | OpenAI / Anthropic | Groq LPUs provide the \~300 t/s required for real-time voice streaming without introducing awkward conversational pauses50. |
| **Speech-to-Text (STT)** | Deepgram (API) or Whisper | Google Cloud STT | Deepgram offers ultra-low latency streaming STT. Local Whisper deployments can be used to maintain a zero-spend development environment. |
| **Text-to-Speech (TTS)** | Kokoro TTS (Self-hosted) | ElevenLabs | Kokoro offers sub-50ms latency on mid-range GPUs2, operates locally to reduce network round-trips, and is free under the Apache 2.0 license49. |
| **Spaced Repetition** | fsrs-rs-python | Custom SM-2 script | FSRS is fundamentally rooted in modern memory statistical modeling and requires significantly fewer reviews to achieve target retention21. |
| **Pronunciation Scoring** | Torchaudio (CTC GOP) | Proprietary APIs | Self-hosting alignment-free CTC GOP allows for granular phoneme control, eliminates API costs, and ensures data privacy compliance35. |
| **Database** | PostgreSQL (Supabase) | MongoDB | Relational data integrity is vital for tracking user histories, complex FSRS review logs, and scenario state progression. |

## **8\. System Architecture and Component Responsibilities**

The architecture is explicitly segregated into a synchronous, ultra-low-latency path for real-time conversation, and an asynchronous, high-compute path for learning analysis and scheduling.

### **Component Responsibilities**

> 1. **Client Application (Next.js)**: Captures user microphone input, manages the XState scenario UI, and renders visual elements. It connects directly to the LiveKit server via WebRTC.  
> 2. **LiveKit Server (SFU)**: Acts as the media router, forwarding audio tracks between the client and the backend Python Agent without processing the media payloads.  
> 3. **Voice Agent (Python)**: Subscribes to the user's audio track via the LiveKit SDK. It utilizes VAD to detect speech start and stop events. It pipes the audio to the STT engine, sends the transcribed text and the current XState context to the Groq LLM, and streams the resulting output tokens directly into the Kokoro TTS engine. The synthesized Kokoro audio chunks are pushed back to the LiveKit Server.  
> 4. **Learning Engine (Async Backend)**: Operates independently of the real-time loop. The Evaluation Worker takes completed transcripts and audio files, queries a heavier LLM for IELTS/ACTFL grading, and runs the Torchaudio GOP pipeline for phoneme scoring. The Review Generation Worker extracts vocabulary and grammatical errors, creates flashcards, and instantiates FSRS records in the database.

### **System Architecture Diagram (Mermaid)**

Code snippet  
sequenceDiagram  
    participant Client as Next.js Client (XState)  
    participant SFU as LiveKit Server  
    participant Agent as LiveKit Python Agent  
    participant STT as Streaming STT  
    participant LLM as Groq API (Llama 3.3)  
    participant TTS as Kokoro TTS (GPU)  
    participant LearnEng as Async Learning Engine (FSRS/GOP)  
    participant DB as PostgreSQL

    Client-\>\>SFU: WebRTC Audio Track (User speaking)  
    SFU-\>\>Agent: Route Audio Track  
    Agent-\>\>STT: Stream Audio Bytes  
    STT--\>\>Agent: Transcript Stream  
    Agent-\>\>Agent: VAD Detects End of Speech  
    Agent-\>\>LLM: Append to Chat History \+ XState Context  
    LLM--\>\>Agent: Stream Tokens (High t/s)  
    Agent-\>\>TTS: Stream Tokens to Pipeline  
    TTS--\>\>Agent: Synthesized Audio Chunks (\<50ms latency)  
    Agent-\>\>SFU: WebRTC Audio Track (AI speaking)  
    SFU-\>\>Client: Play Audio to User  
      
    Note over Client, Agent: User Interrupts AI  
    Client-\>\>SFU: New Audio Track  
    SFU-\>\>Agent: VAD Detects Speech  
    Agent-\>\>Agent: Halt TTS Generation & Clear Buffers  
      
    Note over Agent, DB: Post-Session Asynchronous Processing  
    Agent-\>\>LearnEng: Send full audio \+ transcript  
    LearnEng-\>\>LearnEng: Run GOP (CTC Alignment-Free)  
    LearnEng-\>\>LLM: Request IELTS/ACTFL Rubric Grading  
    LearnEng-\>\>LLM: Extract Mistakes & Generate Q\&A  
    LearnEng-\>\>LearnEng: Initialize fsrs-rs-python items  
    LearnEng-\>\>DB: Store Session Data, GOP Scores, FSRS Logs

## **9\. Core Data Model, Key API Contracts, and End-to-End Flows**

Relational data integrity is critical for mapping long-term learning outcomes. The PostgreSQL schema is designed to separate identity, session telemetry, and spaced repetition analytics.

### **Core Database Entities**

| Entity | Primary Attributes | Description |
| :---- | :---- | :---- |
| **Users** | id, role, parental\_consent\_verified, target\_language, current\_proficiency | Core identity and compliance tracking. |
| **Scenarios** | id, title, system\_prompt, xstate\_machine\_definition, actfl\_level | Defines the parameters and branching logic of a given practice module. |
| **Sessions** | id, user\_id, scenario\_id, transcript, audio\_url, rubric\_scores, created\_at | Immutable log of a completed conversational interaction. |
| **ReviewItems** | id, user\_id, source\_session\_id, front\_text, back\_text, concept\_type | Flashcards generated from conversation errors (Vocabulary/Grammar). |
| **FSRSRecords** | id, item\_id, difficulty, stability, retrievability, next\_due\_date, reps | The statistical memory state parameters managed by the DSR model13. |

### **Key API Contracts**

The communication between the frontend and the asynchronous learning engine relies on strict JSON contracts.  
**1\. FSRS Review Submission API (POST /api/v1/fsrs/review)** This endpoint handles the user's grading of a flashcard (1=Again, 2=Hard, 3=Good, 4=Easy)33. It invokes the fsrs-rs-python library to calculate the new DSR values and update the next due date.

JSON  
{  
  "request": {  
    "item\_id": "uuid-1234",  
    "rating": 3,  
    "review\_timestamp": "2026-10-18T10:12:32Z"  
  },  
  "response": {  
    "success": true,  
    "next\_due\_date": "2026-10-25T00:00:00Z",  
    "updated\_stability": 4.5,  
    "updated\_difficulty": 5.2,  
    "updated\_retrievability": 0.91  
  }  
}

**2\. GOP Phoneme Analysis API (GET /api/v1/assessment/gop/{session\_id})** This endpoint returns the results of the alignment-free CTC metrics processed by the asynchronous worker, allowing the frontend to render phonetic heatmaps35.

JSON  
{  
  "response": {  
    "words": \[  
      {  
        "word": "environment",  
        "score": 0.82,  
        "phonemes": \[  
          {"phoneme": "ih", "score": 0.91, "expected": true},  
          {"phoneme": "n", "score": 0.88, "expected": true},  
          {"phoneme": "v", "score": 0.45, "expected": true, "error\_type": "substitution"}  
        \]  
      }  
    \],  
    "overall\_sentence\_score": 0.76  
  }  
}

## **10\. Security, Privacy, Reliability, Accessibility, and Evaluation Design**

Deploying AI systems in an educational context requires rigorous adherence to privacy laws and safety protocols, particularly concerning data retention and model hallucination.

### **Privacy and the India DPDP Act 2023 Compliance**

Because the platform targets learners, it will inevitably interact with minors. The Indian Digital Personal Data Protection (DPDP) Act of 2023 strictly defines anyone below the age of 18 as a child31.  
Under Section 9 and Rule 10 of the DPDP Act, the platform must obtain verifiable parental consent before processing any personal data of a user under 1832. The architecture will implement a mandatory age-gating flow; if the stated age is under 18, account activation will require a parental verification step, such as a micro-transaction or institutional authorization. Furthermore, the DPDP Act explicitly prohibits tracking, behavioral profiling, and targeted advertising directed at children31. The platform's architecture inherently separates telemetry data from identity, and third-party tracking pixels (e.g., Meta or Google Analytics) will be strictly disabled for child accounts. Users and parents will also have a one-click mechanism to purge all audio recordings, transcripts, and FSRS histories from the PostgreSQL database and object storage.

### **Security and Prompt Injection Defenses**

Conversational LLMs are highly vulnerable to prompt injection attacks, where a user attempts to break the persona constraints (e.g., instructing the interviewer to execute arbitrary code or discuss inappropriate topics). To mitigate this, the Agent architecture utilizes a routing layer. The user's transcribed input is passed through a lightweight, local classifier (e.g., an ONNX-quantized BERT model) to detect intent anomalies before it reaches the primary Groq Llama 3.3 instance. Furthermore, the XState machine enforces strict contextual boundaries; if the user's topic deviates heavily from the scenario\_id parameters, the state machine triggers a predefined fallback response, preventing the LLM from wandering off-topic.

### **Assessment Validity and Observability**

Pedagogical trust is paramount. AI outputs must not be presented as infallible objective truth. To validate the platform's GOP and IELTS scoring, the system will be continuously benchmarked against standard datasets like speechocean76234. The objective is to monitor GOP correlation with human experts, targeting a Pearson correlation greater than 0.70 at the sentence level34. From a UX perspective, UI elements will explicitly label scores as "AI Estimates" and provide tooltips explaining the margin of error, ensuring users focus on the actionable corrections rather than treating the score as an official certification.

## **11\. Licensing, Infrastructure, Performance, and Cost Analysis**

The deployment strategy is bifurcated to accommodate a zero-mandatory-spend development phase, seamlessly transitioning into a scalable production architecture.

### **Zero-Mandatory-Spend Development Strategy**

To build from absolute zero without initial capital, the architecture heavily favors free-tier and open-source solutions. LLM inference relies on the Groq Free Tier, which provides access to Llama models at 30 requests per minute and 30,000 tokens per minute, sufficient for single-developer testing52. Voice orchestration utilizes the LiveKit Cloud free tier, offering 50GB of bandwidth per month22. The TTS component, Kokoro, is run locally on the developer's machine; requiring only \~2GB of VRAM, it runs comfortably on consumer hardware (e.g., RTX 3060\)2. The database relies on the Supabase free tier for a managed PostgreSQL instance.

### **Large-Scale Production Infrastructure**

As concurrent users scale, free tiers will bottleneck the application, specifically regarding Groq's rate limits and local GPU compute constraints. Transitioning to a dedicated TTS compute cluster is highly cost-effective compared to proprietary APIs. On a dedicated bare-metal server equipped with an NVIDIA RTX 3090 (24GB VRAM, costing approximately £110 per month), Kokoro achieves 52-millisecond latency and can synthesize speech at a fraction of a second2. Because Kokoro's RTF on an RTX 3090 is 0.02, a single GPU can handle dozens of concurrent TTS streams simultaneously2.  
For LLM inference, transitioning to Groq's Developer or Production tier (approximately \$0.05 per 1 million input tokens for Llama 3.1 8B) represents one of the lowest-cost inference options available while maintaining essential LPU speed3. Audio files required for GOP analysis and shadowing playback will be stored in AWS S3 or Cloudflare R2, utilizing automated lifecycle policies to delete raw audio after 30 days. This minimizes storage costs and strictly complies with data minimization principles.

## **12\. Key Technical and Product Risks with Mitigations**

| Risk Domain | Specific Risk Profile | Mitigation Strategy |
| :---- | :---- | :---- |
| **Latency Budgeting** | End-to-end latency exceeding 700 milliseconds destroys the illusion of real-time conversation, causing users to speak over the AI agent. | Strictly utilize LiveKit WebRTC for transport23, Groq for LLM50, and Kokoro for TTS2. Stream TTS audio chunks into LiveKit *as they are generated* rather than waiting for the full sentence to complete synthesis49. |
| **Assessment Hallucination** | The LLM invents grammar rules or incorrectly grades a user's speech, irrevocably damaging pedagogical trust. | Do not rely on the LLM for acoustic grading; use deterministic GOP algorithms for pronunciation35. For grammar/lexical grading, use few-shot prompting with established IELTS/ACTFL examples43 and implement a low-temperature sampling parameter. |
| **FSRS Cold Start** | FSRS requires \~1,000 review data points to effectively personalize the DSR model to an individual user; until then, it relies on defaults21. | Utilize the highly optimized open-source default weights derived from the 500-million review benchmark for all new users21. The algorithm will automatically shift to personalized weights as the user accrues review history. |
| **Interruption Handling** | VAD triggers falsely on background noise (e.g., keyboard typing, traffic), causing the AI to abruptly stop speaking mid-sentence. | Implement multi-band noise suppression prior to the VAD layer. Configure VAD with a high activation threshold for barge-in, requiring distinct vocal energy to trigger a cancellation event in the LiveKit agent. |

## **13\. Implementation Roadmap**

The implementation roadmap is structured into four distinct phases, ordered by technical dependency, ensuring that real-time communication is stable before analytical layers are introduced.

### **Phase 1: Transport and Telemetry (Weeks 1-4)**

The objective is to establish the sub-500-millisecond voice loop. Tasks include deploying the LiveKit server, building the baseline Next.js client, and implementing the Python Agent using the LiveKit SDK. The Groq API and local Kokoro TTS pipeline must be integrated. Acceptance criteria dictate that a user can speak into the browser, and the AI replies coherently within 600 milliseconds of the user stopping speech. Interruption (barge-in) must instantly halt the AI's audio output.

### **Phase 2: Conversational State and Logic (Weeks 5-8)**

The objective is to move from stateless chatbots to goal-oriented scenarios. Tasks involve integrating XState into the frontend and backend. Three core scenarios (e.g., Coffee Shop, Salary Negotiation, IELTS Part 1 Interview) will be defined with branching logic7. Acceptance criteria require the AI to correctly advance the XState machine when a user achieves a specific rhetorical goal, with the UI accurately reflecting the current state and context visually.

### **Phase 3: The Learning Engine \- FSRS and Shadowing (Weeks 9-12)**

The objective is to implement spaced repetition and passive listening practice. Tasks include building the Shadowing Mode UI, featuring the 150-millisecond delay loop10. The fsrs-rs-python library will be integrated into the PostgreSQL backend26. The asynchronous background job to extract LLM vocabulary errors into FSRS flashcards will be written. Acceptance criteria dictate that post-session, the database populates with accurately extracted review items, and the FSRS algorithm accurately schedules these items for future review.

### **Phase 4: Assessment, Privacy, and Polish (Weeks 13-16)**

The objective is to deploy objective grading and ensure strict legal compliance. Tasks include deploying the Torchaudio CTC GOP pipeline for pronunciation scoring and implementing the IELTS and ACTFL mapping logic. The DPDP Act verifiable parental consent flow must be implemented32. Acceptance criteria require that users receive a granular phoneme heatmap post-session, and accounts created with an age under 18 are hard-blocked pending successful parental authorization.

## **14\. Unresolved Questions and Recommended Experiments**

To finalize the production architecture and ensure scalability, several hypotheses require empirical testing prior to full-scale launch.

> 1. **GOP Alignment-Free Efficacy in Production**: While academic literature strongly supports the superiority of alignment-free CTC models for GOP in handling insertion and deletion errors35, its computational overhead in a highly concurrent web environment remains untested. An experiment must be conducted to load-test the PyTorch Torchaudio pipeline on an RTX 3090 against 100 concurrent 3-minute audio files to determine precise server scaling requirements.  
> 2. **Context Window vs. Latency Trade-offs**: As an XState scenario progresses, the chat history sent to the Groq Llama 3.3 model continuously expands. An experiment must measure the time-to-first-token degradation on Groq as the context window approaches 8,000 tokens. This will determine the optimal point to summarize previous conversational turns to save context space without losing conversational coherence.  
> 3. **FSRS Flashcard Generation Quality**: It remains an open question whether the LLM can reliably extract high-quality, atomized active-recall questions from conversational mistakes without human moderation. An experiment will generate 500 review items from mock transcripts using Llama 3.3. A human linguistic expert will blindly grade them for pedagogical accuracy and atomicity, allowing the engineering team to adjust the extraction prompt based on findings.

#### **Works cited**

> 1. Kokoro v1 Benchmark (PyTorch/ONNX, CPU/GPU) \- GitHub Gist, [https\://gist.github.com/efemaer/23d9a3b949b751dde315192b4dcf0653](https://gist.github.com/efemaer/23d9a3b949b751dde315192b4dcf0653)  
> 2. TTS Latency Benchmarks \- GIGAGPU, [https\://gigagpu.com/tts-latency-benchmarks/](https://gigagpu.com/tts-latency-benchmarks/)  
> 3. Groq pricing in 2026: every model, free tier, and hidden discounts, [https\://www\.eesel.ai/blog/groq-pricing](https://www.eesel.ai/blog/groq-pricing)  
> 4. Groq Free Tier 2026 — Free Models, Credits & Limits | Price Per Token, [https\://pricepertoken.com/endpoints/groq/free](https://pricepertoken.com/endpoints/groq/free)  
> 5. LiveKit Agents vs Pipecat \- Meetrix, [https\://meetrix.io/blogs/livekit-agents-vs-pipecat/](https://meetrix.io/blogs/livekit-agents-vs-pipecat/)  
> 6. Pipecat vs LiveKit Agents: Which Voice Framework to Build On, [https\://www\.dograh.com/feeds/blog/pipecat-livekit-agents](https://www.dograh.com/feeds/blog/pipecat-livekit-agents)  
> 7. Javascript modules for conversational state management \- Medium, [https\://medium.com/@kaikok/javascript-modules-for-conversational-state-management-9df8c55eae90](https://medium.com/@kaikok/javascript-modules-for-conversational-state-management-9df8c55eae90)  
> 8. IELTS Speaking Band Descriptors: Full Band 6–8 Criteria Table, [https\://speechful.ai/blog/blog-ielts-speaking-band-descriptors-criteria-table](https://speechful.ai/blog/blog-ielts-speaking-band-descriptors-criteria-table)  
> 9. ACTFL Proficiency Guidelines 2024 \- Edlio, [https\://media.edlio.net/7b66857f/6f59502d/ec8d9821/c1bf22b40f7d494892120a348722d29b?\_=ACTFL%20Proficiency%20Guidelines%202024.pdf](https://media.edlio.net/7b66857f/6f59502d/ec8d9821/c1bf22b40f7d494892120a348722d29b?_=ACTFL+Proficiency+Guidelines+2024.pdf)  
> 10. What Is the Shadowing Method? Is It Effective for Speaking? \- idp ielts, [https\://ielts.idp.com/vietnam/about/news-and-articles/article-what-is-shadowing/en-gb](https://ielts.idp.com/vietnam/about/news-and-articles/article-what-is-shadowing/en-gb)  
> 11. XState examples \- Stately, [https\://stately.ai/docs/examples](https://stately.ai/docs/examples)  
> 12. Introduction to State Machines in React with XState \- GeekyAnts, [https\://geekyants.com/en-in/blog/introduction-to-state-machines-in-react-with-xstate](https://geekyants.com/en-in/blog/introduction-to-state-machines-in-react-with-xstate)  
> 13. Spaced Repetition Systems Have Gotten Way Better, [https\://domenic.me/fsrs/](https://domenic.me/fsrs/)  
> 14. FSRS is a really clever iteration on Anki's SM2 algorithm. I've been, [https\://news.ycombinator.com/item?id=42908863](https://news.ycombinator.com/item?id=42908863)  
> 15. Ai English Speaking Apps | EngVarta, [https\://engvarta.com/tag/ai-english-speaking-apps/](https://engvarta.com/tag/ai-english-speaking-apps/)  
> 16. Best English Speaking Apps in India in 2026 \- SpeakX, [https\://speakx.ai/blog/best-english-speaking-apps-india-speakx-vs-competitors](https://speakx.ai/blog/best-english-speaking-apps-india-speakx-vs-competitors)  
> 17. 18 Best AI English Speaking Apps Compared (2026) \- TalkEasy, [https\://www\.talk-easy.com/compare](https://www.talk-easy.com/compare)  
> 18. Best AI speaking practice app: an honest comparison \- Speakeroo, [https\://speakeroo.app/best-ai-speaking-practice-app](https://speakeroo.app/best-ai-speaking-practice-app)  
> 19. 7 Best AI Language Learning Apps Worth Checking Out \- Yoodli, [https\://yoodli.ai/blog/ai-language-learning-apps](https://yoodli.ai/blog/ai-language-learning-apps)  
> 20. Anki FSRS vs SM-2: Which Algorithm Should You Use? \- KaChiKa, [https\://kachika.app/en/blog/spaced-repetition-algorithms/](https://kachika.app/en/blog/spaced-repetition-algorithms/)  
> 21. Best Spaced Repetition Apps 2026: FSRS vs SM-2 Ranked, [https\://studyglen.com/guides/best-spaced-repetition-apps](https://studyglen.com/guides/best-spaced-repetition-apps)  
> 22. Difference Between LiveKit vs PipeCat Voice AI Platforms \- F22 Labs, [https\://www\.f22labs.com/blogs/difference-between-livekit-vs-pipecat-voice-ai-platforms/](https://www.f22labs.com/blogs/difference-between-livekit-vs-pipecat-voice-ai-platforms/)  
> 23. LiveKit vs Pipecat for AI Voice Agents: Complete Guide \- rtc league, [https\://rtcleague.com/blogs/livekit-vs-pipecat-ai-voice-agents](https://rtcleague.com/blogs/livekit-vs-pipecat-ai-voice-agents)  
> 24. Pipecat vs LiveKit Agents vs OpenAI Agents SDK (2026) \- Fora Soft, [https\://www\.forasoft.com/blog/article/pipecat-vs-livekit-agents](https://www.forasoft.com/blog/article/pipecat-vs-livekit-agents)  
> 25. Kokoro TTS Latency by GPU \- GIGAGPU, [https\://gigagpu.com/kokoro-tts-latency-by-gpu/](https://gigagpu.com/kokoro-tts-latency-by-gpu/)  
> 26. Open Spaced Repetition \- GitHub, [https\://github.com/open-spaced-repetition](https://github.com/open-spaced-repetition)  
> 27. Agents and State machines \- technical deep dive \- YouTube, [https\://www\.youtube.com/watch?v=7ydz27rZyxs](https://www.youtube.com/watch?v=7ydz27rZyxs)  
> 28. Benefits of Shadowing in English Learning | PDF | Fluency \- Scribd, [https\://www\.scribd.com/document/839460268/The-Effect-of-Shadowing-in-Learning-English](https://www.scribd.com/document/839460268/The-Effect-of-Shadowing-in-Learning-English)  
> 29. Automatic Analysis of Pronunciations for Children with Speech, [https\://pmc.ncbi.nlm.nih.gov/articles/PMC5884147/](https://pmc.ncbi.nlm.nih.gov/articles/PMC5884147/)  
> 30. Speech Scoring Glossary: GOP, Forced Alignment, Phoneme Scoring, [https\://speechtherapymagic.com/articscore/glossary](https://speechtherapymagic.com/articscore/glossary)  
> 31. Children's Data Under DPDP Act: Parental Consent Rules, [https\://ksandk.com/data-protection-and-data-privacy/child-data-protection-under-dpdp-act-parental-consent-rules/](https://ksandk.com/data-protection-and-data-privacy/child-data-protection-under-dpdp-act-parental-consent-rules/)  
> 32. Digital Personal Data Protection Act, 2023 DPDPA SECTION 9, [https\://www\.dpdpa.com/dpdpa2023/chapter-2/section9.html](https://www.dpdpa.com/dpdpa2023/chapter-2/section9.html)  
> 33. FSRS vs SM2 Spaced Repetition Algorithm \- Mindomax, [https\://www\.mindomax.com/fsrs-vs-sm2-spaced-repetition-algorithm](https://www.mindomax.com/fsrs-vs-sm2-spaced-repetition-algorithm)  
> 34. How Pronunciation Assessment Works (and How Accurate It Is), [https\://www\.taalhammer.com/how-pronunciation-assessment-works/](https://www.taalhammer.com/how-pronunciation-assessment-works/)  
> 35. Segmentation-free Goodness of Pronunciation \- arXiv, [https\://arxiv.org/html/2507.16838v1](https://arxiv.org/html/2507.16838v1)  
> 36. A Framework for Phoneme-Level Pronunciation Assessment Using, [https\://www\.isca-archive.org/interspeech\_2024/cao24b\_interspeech.html](https://www.isca-archive.org/interspeech_2024/cao24b_interspeech.html)  
> 37. THE EFFECTIVENESS OF USING SHADOWING TECHNIQUE, [https\://repository.radenintan.ac.id/31821/1/A%20Thesis%201-2.pdf](https://repository.radenintan.ac.id/31821/1/A%20Thesis%201-2.pdf)  
> 38. How effective is the shadowing technique to learn languages? \- Quora, [https\://www\.quora.com/How-effective-is-the-shadowing-technique-to-learn-languages](https://www.quora.com/How-effective-is-the-shadowing-technique-to-learn-languages)  
> 39. Shadowing as an effective method in language learning: theory, [https\://integrumpublication.org/index.php/ajste/article/view/31](https://integrumpublication.org/index.php/ajste/article/view/31)  
> 40. A Systematic Review of Research on the use of Shadowing for, [https\://www\.tandfonline.com/doi/full/10.1080/29984475.2025.2546827](https://www.tandfonline.com/doi/full/10.1080/29984475.2025.2546827)  
> 41. (PDF) The Effectiveness of Using Shadowing Technique Towards, [https\://www\.researchgate.net/publication/385511707\_The\_Effectiveness\_of\_Using\_Shadowing\_Technique\_Towards\_Students'\_Pronunciation\_Skill](https://www.researchgate.net/publication/385511707_The_Effectiveness_of_Using_Shadowing_Technique_Towards_Students'_Pronunciation_Skill)  
> 42. IELTS Speaking Band Descriptors 2026 | Criteria & Calculator, [https\://edubenchmark.com/blog/ielts-speaking-band-descriptors/](https://edubenchmark.com/blog/ielts-speaking-band-descriptors/)  
> 43. How are your IELTS Speaking scores calculated?, [https\://ielts.idp.com/results/scores/speaking](https://ielts.idp.com/results/scores/speaking)  
> 44. IELTS Speaking Band Descriptors, [https\://ielts.org/cdn/ielts-guides/ielts-speaking-band-descriptors.pdf](https://ielts.org/cdn/ielts-guides/ielts-speaking-band-descriptors.pdf)  
> 45. ACTFL Proficiency Scale \- Language Testing International, [https\://www\.languagetesting.com/actfl-proficiency-scale](https://www.languagetesting.com/actfl-proficiency-scale)  
> 46. ACTFL Proficiency Guidelines: Comprehensive Overview & Guide, [https\://www\.busuu.com/en/english/actfl-proficiency-guidelines](https://www.busuu.com/en/english/actfl-proficiency-guidelines)  
> 47. Oral Proficiency Levels in the Workplace \- ACTFL, [https\://www\.actfl.org/uploads/files/general/OralProficiencyWorkplacePoster\_2022-10-13-062609\_ocga.pdf](https://www.actfl.org/uploads/files/general/OralProficiencyWorkplacePoster_2022-10-13-062609_ocga.pdf)  
> 48. Understand and improve voice agent latency \- LiveKit, [https\://livekit.com/blog/understand-and-improve-agent-latency](https://livekit.com/blog/understand-and-improve-agent-latency)  
> 49. Kokoro TTS | Guides \- Clore.ai, [https\://docs.clore.ai/guides/audio-and-voice/kokoro-tts](https://docs.clore.ai/guides/audio-and-voice/kokoro-tts)  
> 50. Groq API Pricing 2026: Per-Token Cost Compared \- Activepieces, [https\://www\.activepieces.com/blog/groq-api-pricing-2026-per-token-cost-compared](https://www.activepieces.com/blog/groq-api-pricing-2026-per-token-cost-compared)  
> 51. Groq API Pricing 2026: Cost Per Token vs GPU Rental | Spheron Blog, [https\://www\.spheron.network/blog/groq-api-pricing-2026-cost-per-token-vs-gpu-rental/](https://www.spheron.network/blog/groq-api-pricing-2026-cost-per-token-vs-gpu-rental/)  
> 52. Groq Free Tier 2026: Fastest LLM Inference API (No Credit Card), [https\://www\.getaiperks.com/en/ai/groq-free-tier-2026](https://www.getaiperks.com/en/ai/groq-free-tier-2026)  
> 53. Groq API Free Tier Limits in 2026: What You Actually Get, [https\://www\.grizzlypeaksoftware.com/articles/p/groq-api-free-tier-limits-in-2026-what-you-actually-get-uwysd6mb](https://www.grizzlypeaksoftware.com/articles/p/groq-api-free-tier-limits-in-2026-what-you-actually-get-uwysd6mb)  
> 54. Voice agent frameworks: Pipecat, LiveKit Agents, and friends \- Soniox, [https\://soniox.com/wiki/voice-agent-frameworks](https://soniox.com/wiki/voice-agent-frameworks)  
> 55. Verifiable Parental Consent Under DPDP: What Section 9 Demands, [https\://www\.consently.in/blog/verifiable-parental-consent-dpdp-section-9](https://www.consently.in/blog/verifiable-parental-consent-dpdp-section-9)  
> 56. Indian perspective on protecting children's personal data | India, [https\://law.asia/childrens-data-protection-dpdp-act/](https://law.asia/childrens-data-protection-dpdp-act/)  
> 57. Groq API Guide 2026: Setup, Pricing, Endpoints & Code Examples, [https\://www\.ampcome.com/post/how-to-use-groq-api-the-comprehensive-guide-you-need](https://www.ampcome.com/post/how-to-use-groq-api-the-comprehensive-guide-you-need)