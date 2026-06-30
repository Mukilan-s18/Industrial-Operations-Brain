"""Generate a small, text-based demo PDF about Azure Test Plans."""
from fpdf import FPDF

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

content = [
    ("What is Azure Test Plans?",
     """Azure Test Plans is a comprehensive test management tool within Azure DevOps that provides \
all the capabilities needed for planned manual testing, user acceptance testing, exploratory \
testing, and gathering stakeholder feedback.

Azure Test Plans offers powerful tools for driving quality and collaboration throughout the \
development process. This browser-based test management solution supports both manual and \
automated testing workflows, enabling teams to ensure software quality at every stage of delivery.

Key benefits include end-to-end traceability from requirements to test cases, seamless \
integration with CI/CD pipelines through Azure Pipelines, and rich reporting dashboards \
that provide visibility into testing progress and quality metrics."""),

    ("Manual and Exploratory Testing",
     """Planned Manual Testing allows teams to organize tests into test plans and test suites by \
areas of ownership. Testers can run manual test cases using the web-based test runner, which \
captures detailed results including pass/fail status, comments, and attachments.

Exploratory Testing enables testers to explore the application without predefined test cases. \
Using the Test & Feedback browser extension, testers can capture screenshots, screen recordings, \
and notes during their testing sessions. All findings are automatically linked to work items.

User Acceptance Testing (UAT) provides mechanisms for stakeholders and end users to validate \
that the software meets business requirements. UAT test plans can be assigned to specific users \
who may not be part of the development team.

Stakeholder Feedback allows product owners and other stakeholders to provide structured feedback \
on applications through the feedback extension, capturing rich data including images and annotations."""),

    ("Automated Testing Integration",
     """Azure Test Plans integrates with Azure Pipelines to support automated testing as part of \
CI/CD workflows. Test cases can be associated with automated test methods, allowing them to be \
executed automatically during build and release pipelines.

Key automation capabilities include:
- Associate test plans with build or release pipelines for continuous testing
- Run automated tests as part of the deployment process
- Capture and publish test results from various test frameworks
- Review test results through built-in pipeline reports and dashboards

Supported test frameworks include NUnit, xUnit, MSTest, JUnit, and many others through \
the Visual Studio Test task and Publish Test Results task in Azure Pipelines.

Test Impact Analysis helps identify which tests need to run based on code changes, \
reducing the time needed for regression testing while maintaining quality coverage."""),

    ("Traceability and Reporting",
     """Azure Test Plans provides end-to-end traceability by linking test cases and test suites \
to user stories, features, or requirements. This ensures complete visibility into what has \
been tested and what gaps remain.

Traceability features include:
- Link test cases to requirements for bidirectional traceability
- Automatically associate tests with builds and releases
- Track defects found during testing back to requirements
- View requirement-based test coverage reports

Reporting and Analytics capabilities include configurable tracking charts that can be \
pinned to dashboards, test-specific dashboard widgets showing pass rates and trends, \
built-in reports for tracking testing progress across sprints, and integration with \
Power BI for advanced custom analytics.

Progress reports show test execution status across test plans, highlighting areas that \
need attention and providing confidence metrics for release readiness decisions."""),
]

for title, body in content:
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, body)

pdf.output("data/demo.pdf")
print("[OK] Created data/demo.pdf (4 pages, text-based)")
print(f"  Size: {__import__('os').path.getsize('data/demo.pdf'):,} bytes")
