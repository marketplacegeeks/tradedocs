I just implemented a feature. Help me verify it works.

Step 1 — Automated tests:
1. Run `pytest apps/{app}/tests/ -v` and show me the output. If any tests fail, diagnose the root cause before suggesting a fix.
2. Run `pytest apps/{app}/tests/ --cov=apps/{app} --cov-report=term-missing` and identify any untested critical paths.

Step 2 — Manual spot-check:
3. Tell me what `curl` commands or browser URLs I should hit to confirm each endpoint works end-to-end.
4. Tell me what database query I can run (via the postgres MCP) to confirm data was saved correctly.
5. Tell me what visual check to do in the React UI to confirm the feature renders correctly.
6. List the three most likely things that could be broken that the automated tests may not have caught.

Give me a checklist in order: run tests → fix any failures → manual spot-check → confirm done.