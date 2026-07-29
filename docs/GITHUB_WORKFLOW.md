# GitHub Submission Workflow

Use this checklist while creating your own visible development history.

## Pull-request process

1. Start from `develop`.
2. Create a named feature branch.
3. Implement one coherent feature.
4. Run `pytest -q` and the app locally.
5. Commit with `feat:`, `fix:`, `docs:`, `refactor:` or `test:`.
6. Push the branch.
7. Open a Pull Request into `develop` with:
   - what changed;
   - why the design was selected;
   - screenshots or test evidence;
   - known issues.
8. Merge after review.
9. Open a final release Pull Request from `develop` to `main`.

## Recommended GitHub Issues

- Set up repository, environment and secrets
- Define agent communication schemas
- Implement router model
- Build RAG document loader and chunker
- Add embedding model and FAISS index
- Implement Curriculum Agent
- Implement Lesson Planning Agent
- Implement Review Agent and revision loop
- Build Streamlit interface
- Evaluate five retrieval queries
- Add tests and CI
- Deploy to Streamlit Cloud
- Complete README and demo video
