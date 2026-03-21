# Aniket's Suggested Workflow Notes

## Background
Aniket is a product manager, not a coder. He does not read code files directly.
His feedback loop is: build → test in browser → react → decide next step.
This is how he worked in Cline and it felt natural. Claude Code felt blank because
there was no UI to test — just backend APIs and test numbers.

---

## The Problem With Pure Backend-First

The original end-to-end-workflow.md builds all backend layers first, then all
frontend pages. This means 5–6 sessions with nothing visible in the browser.
For a PM, this kills the feedback loop entirely.

---

## The Adjusted Approach

**Pair each backend feature with its frontend page before moving to the next feature.**

Instead of:
- accounts backend → master_data backend → org backend → [all frontend later]

Do this:
- accounts backend → login page (React) ← Aniket tests in browser
- reference data backend → reference data page ← Aniket tests
- organisation backend → organisation page ← Aniket tests
- and so on

The requirements.md and technical_architecture.md do not change.
Only the session order changes.

---

## What Claude Should Do Differently

After finishing any feature, always end with a concrete browser test instruction:

> "Start the server and go to http://localhost:5173.
> You should see [X]. Do [Y]. You should get [Z]."

Never just say "N tests passing." That means nothing to a PM.
Give Aniket something to open, click, and feel.

---

## Aniket's Role in Each Session

- Review the plan before saying "go ahead"
- Test the feature in the browser after it is built
- Give feedback on what looks wrong or what is missing
- Decide what to build next

He does not need to read code files. He does not need to understand syntax.
His job is product decisions and browser testing.

---

## Session Structure Going Forward

1. Build backend (model → serializer → view → URL → tests)
2. Build frontend page for the same feature (API file → page component → route)
3. Tell Aniket exactly what to run and what to test in the browser
4. Aniket tests, gives feedback
5. Fix anything broken
6. Commit
7. Move to the next feature

The test cases have to be written in plain English because I do not understand the test cases which you are technically writing. 
Create git branch after every workflow and test is finished, commit it, when I go to next step first comit to git etc.
 by default, we should never push any PDF file to Git
If you are doing any changes which is not mentioned in requirement.md, first mention the update in requirement.md, then only do the change. 

All models should have exact description of error not random errors.H