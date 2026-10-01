# Present Task 3 in five minutes

## Opening explanation

“My pipeline checks a remote code push, runs linting and tests, builds Docker images, deploys those exact images, verifies the application, and publishes execution results. Failed checks prevent deployment.”

## Demonstration order

1. Open the README and explain the pipeline diagram.
2. Open `.github/workflows/task3-ci-cd.yml`: point to the push trigger, jobs, and `needs` dependencies.
3. Open the successful run linked in `docs/evidence/README.md`.
4. Show 28 backend tests, 12 frontend tests, and the build/deployment jobs.
5. Show the deployment summary: commit, startup duration, readiness, API checks, and cleanup.
6. Open the recorded intentional failure run. Show that lint passes, one test fails, and build/deployment are skipped.
7. Explain that the intentional failure was reverted; it is not present on main.
8. If a live app demonstration is useful, open the separate local Task 3 demo at http://localhost:8083.
9. Open the PDF and explain how its evidence maps to the assignment requirements.

## Files worth opening

- `.github/workflows/task3-ci-cd.yml`: automation and stage dependencies.
- `scripts/ci/images.py`: exact image identity verification.
- `scripts/ci/deploy.py`: real deployment and commit/health checks.
- `scripts/ci/report.py`: execution summaries and saved metrics.
- `docs/Task-3-CICD-Report.pdf`: submission-ready Task 3 section.

## Likely questions

**CI versus CD?** CI checks code and tests integration; this CD stage deploys successful builds into a temporary test environment.

**Where is deployment?** On a GitHub-hosted Ubuntu runner during the job. It is removed afterward; it is not a permanent public website.

**How do you know the right code ran?** The pipeline checks the image IDs, commit labels, and revision returned by the API.

**What happens if tests fail?** The workflow fails and dependent build/deployment jobs are skipped. Reporting still runs.

**Why include Docker files here?** This repo must build and deploy independently. The separate Task 2 repo explains containerization in detail.
