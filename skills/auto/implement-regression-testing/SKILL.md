---
name: implement-regression-testing
description: Use when fixing bugs to ensure the fix is verified and does not regress.
---
1. Create a dedicated test file (e.g., `tests/test_regressions.py`) for the current task.
2. Write a test case that reproduces the reported bug (the test should fail before the fix).
3. Write at least two additional test cases covering edge cases related to the fix.
4. Run the test suite to confirm the bug is fixed and no existing functionality is broken.
5. Ensure the test file is preserved in the workspace for future validation.