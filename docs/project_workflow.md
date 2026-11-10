# Project workflow (Git + GitHub)

## Branches
| Branch | Owner |
|--------|-------|
| `main` | always working code (only merged via Pull Request) |
| `backend-member1` | Member 1 |
| `database-member2` | Member 2 |
| `analysis-member3` | Member 3 |
| `dashboard-member4` | Member 4 |

## One-time setup (Member 1)
1. Create an empty GitHub repository, add the project files and push to `main`:
   ```bash
   git init
   git add .
   git commit -m "Initial project structure"
   git branch -M main
   git remote add origin https://github.com/<user>/banking-transaction-analysis.git
   git push -u origin main
   ```
2. Add Members 2-4 as collaborators (Settings -> Collaborators).
3. Optional: protect `main` (Settings -> Branches) so changes need a Pull Request.

## Everyone else
```bash
git clone https://github.com/<user>/banking-transaction-analysis.git
cd banking-transaction-analysis
git checkout -b analysis-member3        # use your own branch name
```
Work only in your own folder, then:
```bash
git add .
git commit -m "Add monthly analysis functions"
git push -u origin analysis-member3
```
Open GitHub -> **Compare & pull request** -> ask Member 1 to review -> **Merge**.

Never commit `.env` (it is in `.gitignore`).

## Keeping your branch up to date
```bash
git checkout main
git pull origin main
git checkout analysis-member3
git merge main
```

## How Member 1 integrates the branches
Merge in this order, because each layer depends on the one before it:
1. `database-member2` (tables) -> run `schema.sql` + `sample_data.sql` in SQLyog
2. `backend-member1`
3. `analysis-member3`
4. `dashboard-member4`

```bash
git checkout main
git pull origin main
git merge database-member2
git merge backend-member1
git merge analysis-member3
git merge dashboard-member4
pytest -v
streamlit run dashboard/app.py
git push origin main
```
If Git reports a conflict, open the file, keep the correct lines, remove the `<<<<<<<`, `=======`, `>>>>>>>`
markers, then `git add <file>` and `git commit`.
Final checks: tests pass, every dashboard page opens, charts render, CSV download works.
