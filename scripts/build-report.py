#!/usr/bin/env python3
"""Build the Task 3 report from saved GitHub run evidence (requires reportlab)."""
from datetime import datetime
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted

root = Path(__file__).resolve().parents[1]
folder = root / 'docs'
evidence = folder / 'evidence'
def load(name): return json.loads((evidence / name).read_text())
success = load('successful-run.json')
failed = load('failed-run.json')
deployment = load('deployment/deployment.json')
backend = load('backend-tests.json')
frontend = load('frontend-tests.json')
assert success['conclusion'] == 'success'
assert failed['conclusion'] == 'failure'
assert deployment['result'] == 'success'
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='SmallText', parent=styles['BodyText'], fontSize=9, leading=12))
styles.add(ParagraphStyle(name='CodeSmall', fontName='Courier', fontSize=8, leading=11))
story = []
def title(text): story.append(Paragraph(escape(text), styles['Title'])); story.append(Spacer(1,3*mm))
def heading(text): story.append(Paragraph(escape(text), styles['Heading2']))
def para(text): story.append(Paragraph(text, styles['BodyText'])); story.append(Spacer(1,3*mm))
def code(text): story.append(Preformatted(text, styles['CodeSmall'])); story.append(Spacer(1,3*mm))
def table(rows, widths):
    cells = [[Paragraph(escape(str(c)), styles['SmallText']) for c in row] for row in rows]
    t = Table(cells, colWidths=widths, hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eef8')),
                          ('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.4,colors.lightgrey),
                          ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
                          ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.append(t);story.append(Spacer(1,4*mm))
def run_link(record, label):
    para(f'<link href="{record["url"]}" color="blue">{label}: GitHub run {record["databaseId"]}</link>')

title('Progree DevOps Internship')
heading('Task 3: Multi-Stage Automated CI/CD Deployment Pipeline')
para('<b>Intern:</b> Haseeb Ullah<br/><b>Application:</b> Wanderlust frontend, backend, MongoDB, and Redis<br/><b>Platform:</b> GitHub Actions, Ubuntu runners, Docker Compose')
para('The objective is to automate testing and integration on remote code pushes and show deployment results on an execution board. This project checks application quality, builds the images, deploys the real stack, verifies it, and records the outcome without manual deployment commands.')
heading('Requirement coverage')
table([
    ['Internship requirement', 'Delivered implementation'],
    ['Run on remote pushes', 'GitHub push trigger; actual successful and deliberately failed runs recorded.'],
    ['Automatically pull code', 'Pinned checkout action in every job; each stage uses the triggering revision.'],
    ['Static application linting', 'ESLint for backend/frontend; separate frontend TypeScript check.'],
    ['Unit-testing suites', f"{backend['numPassedTests']} backend unit tests and {frontend['numPassedTests']} frontend unit/component tests."],
    ['Multi-stage deployment', 'Quality checks gate image builds. A separate job loads the built image archive and deploys the four-service application.'],
    ['Deployment status metrics', 'Actions job graph, summaries, test counts/coverage, startup duration, commit identity, health, logs, and saved artifacts.'],
], [155,340])
heading('Execution flow')
code('Remote push\n    -> Lint + type checks + unit/component tests\n    -> Build images tagged with the commit SHA\n    -> Transfer image archive + checksum + manifest\n    -> Deploy Compose stack on a fresh runner\n    -> Verify image IDs, commit, readiness, and API\n    -> Save results and remove test environment')
para('<b>Deployment scope:</b> a temporary GitHub-hosted test environment, not a persistent public website. The application runs during verification and is removed afterward. The Ubuntu Task 2 demo is separate.')
para('Application attribution: Wanderlust by Krishna R Acharya and contributors, MIT license. The portfolio contribution is the DevOps configuration, verification, and documentation.')
story.append(PageBreak())

title('Successful deployment evidence')
run_link(success, 'Successful push-triggered pipeline')
para('<b>Commit:</b> '+success['headSha']+'<br/><b>Recorded:</b> '+success['createdAt']+'<br/><b>Conclusion:</b> '+success['conclusion'])
table([['Job','Outcome']]+[[job['name'],job['conclusion']] for job in success['jobs']], [350,145])
heading('Measured results')
table([
    ['Metric','Recorded result'],
    ['Unit/component tests',f"{backend['numPassedTests']} backend + {frontend['numPassedTests']} frontend passed; 0 failed"],
    ['Deployment startup + revision verification',f"{deployment['startup_seconds']} seconds"],
    ['Backend / MongoDB / Redis', 'All ready'],
    ['Live application verification',deployment['smoke_tests']],
    ['Environment cleanup',deployment['cleanup']],
], [285,210])
heading('Checks against the running application')
for line in (evidence/'deployment/smoke-tests.txt').read_text().splitlines():
    if line.startswith('PASS:'):
        story.append(Paragraph(escape(line),styles['SmallText']));story.append(Spacer(1,2*mm))
para('The image checksum is verified before loading. Running container image IDs and revision labels must match the build manifest. The API health endpoint must report the same commit SHA as the push. Deployment uses --no-build, so the tested images are reused.')
story.append(PageBreak())

title('Failure gate and recovery')
run_link(failed, 'Controlled failed-test demonstration')
para('<b>Commit:</b> '+failed['headSha']+'<br/><b>Demonstration:</b> a test deliberately expected an invalid category to be accepted. The backend test failed while linting and the frontend checks passed.')
table([['Job','Outcome']]+[[job['name'],job['conclusion']] for job in failed['jobs']], [350,145])
para('The failed branch was eligible for deployment under the same push trigger. Build and deployment were skipped because the quality job failed. The reporting job still ran, while the overall workflow remained failed. The deliberately failing test was reverted and was never merged into main.')
if (evidence/'recovery-run.json').exists():
    recovery = load('recovery-run.json')
    assert recovery['conclusion'] == 'success'
    run_link(recovery, 'Successful rerun after reverting the deliberate failure')
heading('Why the checks can be trusted')
para('The inherited backend teardown called process.exit(0); it was removed so Jest returns a failure status for failed tests. Frontend API fixtures make component tests independent of a preloaded local database. Lint and type-check errors also fail the workflow. No quality stage uses continue-on-error.')
heading('Coverage reporting')
table([
    ['Selected-module coverage','Backend','Frontend'],
    *[[metric.capitalize(),str(backend['coverage_selected_modules'][metric]['pct'])+'%',str(frontend['coverage_selected_modules'][metric]['pct'])+'%'] for metric in ['lines','branches','functions','statements']],
], [235,130,130])
para('Coverage applies only to the selected modules declared in the Jest configurations. It is reported as a metric, not presented as whole-application coverage. Real database/cache behavior is also checked after deployment.')
story.append(PageBreak())

title('Operation and submission handoff')
heading('Where to review the pipeline')
para('<link href="https://github.com/haseeb9876/progree-task-3-cicd/actions/workflows/task3-ci-cd.yml" color="blue">Open the Task 3 GitHub Actions workflow</link><br/>Choose a run to see job outcomes, test summaries, deployment metrics, logs, and artifacts.')
table([
    ['Artifact','Contents / retention'],
    ['tests-backend-* / tests-frontend-*','Test JSON and selected-module coverage; 14 days.'],
    ['build-output-*','Docker build logs; 14 days.'],
    ['application-images-*','Image archive, checksum, and manifest; 3 days.'],
    ['deployment-evidence-*','Commit, startup time, health, API checks, service status, and redacted logs; 14 days.'],
], [245,250])
para('The repository also retains compact evidence under docs/evidence so the report remains useful after downloadable artifacts expire. GitHub run links provide the original execution history.')
heading('Important operational behavior')
para('Pushes and manual runs deploy temporary test environments. Pull requests run quality and build checks without deployment. Each deployment has its own Compose project name and temporary credentials. Runner credentials are masked in logs; uploaded paths exclude secret files. The GitHub token has read-only repository-content permission, and action versions are pinned to commit hashes.')
heading('Run the same quality checks locally')
code('npm ci --prefix backend\nnpm ci --prefix frontend\nnpm run lint --prefix backend\nnpm run lint --prefix frontend\nnpm run typecheck --prefix frontend\nnpm run test:ci --prefix backend\nnpm run test:ci --prefix frontend')
heading('Submission status')
para('Task 3 satisfies the stated automation objective based on the linked successful deployment and failed-test gate demonstration. This report is a component for the final combined internship PDF. It has not been submitted to the Google Form. The stated deadline is 5 October 2026. Task 4 remains separate infrastructure/Kubernetes work.')
heading('References')
para('<link href="https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax" color="blue">GitHub workflow syntax</link><br/><link href="https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands" color="blue">GitHub workflow commands and job summaries</link>')

def footer(canvas, doc):
    canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.grey)
    canvas.drawString(18*mm,12*mm,'Haseeb Ullah | Progree DevOps Internship | Task 3')
    canvas.drawRightString(A4[0]-18*mm,12*mm,str(doc.page));canvas.restoreState()
output=folder/'Task-3-CICD-Report.pdf'
SimpleDocTemplate(str(output),pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,
                  topMargin=16*mm,bottomMargin=20*mm,title='Task 3 - Automated CI/CD Pipeline',
                  author='Haseeb Ullah').build(story,onFirstPage=footer,onLaterPages=footer)
print(output)
