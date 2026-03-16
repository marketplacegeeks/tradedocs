I just implemented a feature. Now write the automated tests for it.

1. Read the feature code I just wrote (I will tell you which files).
2. Create or update `tests/factories.py` in the app — add a factory-boy factory for every new model, using SubFactory for any related models.
3. Write `tests/test_models.py` — test any model validation, custom save logic, or property methods.
4. Write `tests/test_views.py` — for each API endpoint, write:
  - One happy-path test (correct role, correct data → expected response)
  - One permission-denial test (wrong role → 403 or unauthenticated → 401)
  - One validation test (missing required field → 400 with an error message)
5. Show me only the test files. Do not touch any other file.
6. After writing the tests, tell me the exact command to run them.