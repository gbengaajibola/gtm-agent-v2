# GTM Agent v2

Every week, a handful of cool projects get built inside the [LearnToEarn Fellowship](https://l2e.lovable.app) — an AI-native engineering fellowship. Somebody has to tell everyone else about them. This is the robot that does that job.

It's a small assistant that runs on its own every Friday. It visits the fellowship's leaderboard site, picks out the projects worth talking about that week, writes a short message about each one (the way a friend would, not the way a press release would), and sends a draft to a private channel for a quick human look. One click of approval later, the message goes out to the community on Discord — with a WhatsApp version saved for copy-pasting, since WhatsApp has no way for robots to post directly.

Nobody on the team spends their Friday writing community updates anymore.

## Why it's built this way

**A human always gets the last word.** The robot never posts anything straight to the public channel. It writes the draft, drops it in a private review channel, and waits. If nobody says yes or no within 3 days, it quietly gives up and nothing gets posted. No surprises, no embarrassing posts at 2am.

**No project gets featured twice "for no reason."** The robot keeps a little memory — a history of everything it's ever featured. New projects always get first dibs. Once everyone's had a turn, it switches to highlighting the ones that gained the most ground that week. And each project only gets one "most improved" moment ever, so the same thing can't keep coming back.

**It never makes things up.** The writing brain is only allowed to use facts from the leaderboard and the projects' own pages. No invented numbers, no fake testimonials, no made-up deadlines. If it can't find enough to say about a project, it says less rather than making something up.

**Everything it does is written down.** Every pick, every draft, every decision is saved and time-stamped in the repo, so you can always look back and see exactly what happened and why.

## What's in the box

| File | What it does |
|---|---|
| `run_weekly.py` | The main weekly run — gathers projects, writes the drafts, asks for approval |
| `approve_run.py` | The "yes" or "no" button (run it yourself, or approve from GitHub's UI) |
| `check_pending.py` | The nag — reminds you if a draft is waiting too long, cancels it after 3 days |
| `lib/` | The robot's brain: reading the leaderboard, visiting projects, writing, posting, remembering |
| `assets/system_prompt.txt` | Its "personality" — how the weekly message should sound. Edit this file to change the tone, no coding needed |
| `.github/workflows/weekly_showcase.yml` | The alarm clock — runs everything automatically on GitHub, every Friday |

## Want to run your own?

You'll need Python, a Discord server you control, and an API key for the AI that does the writing (OpenCode Go subscription via Zen console (https://opencode.ai/auth)).

1. **Get the code and install what it needs:**
   ```
   pip install -r requirements.txt
   python setup_check.py
   ```
   The setup check tells you plainly what's missing — it won't fail just because you're not done yet.

2. **Copy `.env.example` to `.env`** and fill in your four keys: the Discord bot token, your two channel IDs (one private for review, one public for posting), and the OpenCode Go key.

3. **Try one run:**
   ```
   python run_weekly.py
   ```
   A draft appears in your review channel. Read it. If you like it:
   ```
   python approve_run.py 2026-W38 approve
   ```
   (use whatever run ID it printed — one per week). If you don't like it, say `reject` and nothing gets posted.

4. **Let it run itself.** Add the same four keys as repo secrets on GitHub (Settings → Secrets and variables → Actions: DISCORD_BOT_TOKEN, DISCORD_REVIEW_CHANNEL_ID, DISCORD_PUBLIC_CHANNEL_ID, OPENCODE_GO_API_KEY (+ optional OPENCODE_GO_MODEL)), and switch on "Read and write permissions" under Settings → Actions → General. From then on, GitHub runs it every Friday morning, and you can approve or reject drafts right from the GitHub app on your phone.

## The honest state of things

- The weekly schedule works, the writing works, the approval flow works.
- One situation is handled a bit bluntly: some project sites can't be read automatically (fancy splash screens and the like). The robot just writes around it using the project's own description instead. It works, it's just less clever than it could be.
- It posts to Discord and writes WhatsApp drafts. LinkedIn and X versions don't exist yet.

Questions or ideas? Open an issue — happy to hear them.
