# Inclusive Language Guide

Owner: People Ops (Ana Torres, @anat), with the Engineering guilds. Applies to code,
docs, UI copy, and everyday communication. The `inclusive-lint` CI check enforces the
code-facing terms; humans enforce the rest, kindly.

## Why we bother

Half the company reads English as a second language, and our words end up in code
reviews, customer docs, and interview transcripts. Precise, inclusive language is
mostly just *better writing*: "blocklist" says what it does; "blacklist" makes a new
teammate look up an idiom with baggage.

## Terms we use in code and docs

| Instead of | Use | Notes |
|---|---|---|
| whitelist / blacklist | allowlist / blocklist | enforced by `inclusive-lint` |
| master / slave | primary / replica, leader / follower | DB and queue configs |
| master (branch) | main | already our default branch |
| sanity check | quick check, smoke test, confidence check | |
| grandfathered | legacy status, exempted | |
| dummy value | placeholder, sample value | |
| man-hours | person-hours, engineering time | |
| crazy / insane (for "very") | wild, unexpected, huge | |
| "guys" (mixed group) | folks, team, everyone | Spanish: "equipo" beats "chicos" |

Renaming existing APIs is scheduled work, not drive-by work — file it, don't break contracts.

## People and pronouns

- Use a person's stated name and pronouns; if you don't know, use their name or they/them —
  never guess from a name or a face. Pronouns in Slack profiles are encouraged, never required.
- Describe people by relevant facts, not demographics: "Hana, who owns web performance" —
  not "the Korean engineer".
- Disability language: person-first or identity-first per the person's own usage; when unknown,
  "person using a screen reader" beats labels.

## Writing for a global team

- Idioms, sports metaphors, and pop-culture references exclude someone in every meeting —
  "let's touch base and circle back" translates to nothing in three of our offices.
- Humor is welcome; humor that needs cultural context to land goes in #random, not in specs.
- Names are spelled the way their owners spell them: Tomáš, Sofía, María — our systems
  support diacritics on purpose; getting a teammate's name right is a feature.

## When you get it wrong (you will)

Correct yourself briefly and move on — no three-paragraph apology, which makes it about you.
If you're corrected: "thanks", fix it, done. If you see a pattern worth addressing,
a private "hey, heads-up" beats a public callout the first time. Persistent issues go to Ana.
