# FindMyScheme

An AI-assisted government scheme eligibility finder built with Django.
Eligibility is decided by a verified rule engine; LLMs are used only for
understanding user input and explaining results.

---

## Status
Unit 0: project setup (work in progress)

---

## Setup
1. Clone the repo
`git clone https://github.com/shivashishyadav/FindMyScheme.git`

2. Create a virtual env and activate it `python -m venv .venv`
3. Install Dependencies `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in values
5. `python manage.py migrate`
6. `python manage.py createsuperuser`
7. `python manage.py runserver`

---

## Docs
See `docs/design.md` for the architecture and build plan.