- [x] Branch created: feature/protected-hello-endpoint
- [ ] Run tests: `python manage.py test` (or ensure CI passes)
- [ ] Lint/format: run flake8/black (or ensure CI lint step passes)
- [ ] Migrations: run `python manage.py makemigrations` and `python manage.py migrate` if models changed
- [ ] Environment: confirm `.env` has SECRET_KEY and DATABASE_URL set for testing
- [ ] Manual auth test (happy path):
  - Obtain tokens:
    curl -X POST http://127.0.0.1:8000/api/token/ -H "Content-Type: application/json" -d '{"username":"<user>","password":"<pass>"}'
  - Call protected endpoint:
    curl -H "Authorization: Bearer <ACCESS_TOKEN>" http://127.0.0.1:8000/api/hello/
  - Expect: `{"message":"Hello, <username>!"}`
- [ ] Documentation: confirm README includes the new endpoint and test instructions
- [ ] Security/CORS: verify CORS and DEBUG settings appropriate for environment (do not merge with DEBUG=True for production)
- [ ] API contract: verify URL/path and response shape meet expectations
- [ ] Add reviewers/assignees and appropriate labels (suggested labels: enhancement, needs-review, tests-passing)
- [ ] Merge strategy: choose squash/merge or rebase as preferred

---

(Provided by Copilot)