# Maintaining Separate Git Branches/Repos for AI Tools

## Overview
This guide explains how to maintain separate git branches or repositories for AI tools, including a version with semi-adult content and a 'public' version without such content.

## Steps

### 1. Create Two Repositories
- Main repository (SFW)
- Adult repository (NSFW)

### 2. Main Repository (SFW)
- Develop SFW content
- Commit and push regularly

### 3. Adult Repository (NSFW)
- Add main repo as a remote:
  ```
  git remote add sfw <main-repo-url>
  ```
- Fetch main repo:
  ```
  git fetch sfw
  ```
- Create a branch from main:
  ```
  git checkout -b adult sfw/main
  ```
- Add adult content
- Commit and push to adult repo

### 4. Updating Adult Repository
- Fetch main:
  ```
  git fetch sfw
  ```
- Merge changes:
  ```
  git merge sfw/main
  ```
- Resolve conflicts if any
- Add adult-specific changes
- Commit and push

This approach keeps SFW content separate while allowing easy updates to the adult version.

## Merging SFW Changes from Adult Repo to Main Repo

If you accidentally do SFW work on the adult repo and want to merge it back into the SFW repo:

1. In the main repo, add the adult repo as a remote:
   ```
   git remote add adult <adult-repo-url>
   ```

2. Fetch the adult repo:
   ```
   git fetch adult
   ```

3. Create a branch from the adult repo's main branch:
   ```
   git checkout -b merge-sfw adult/main
   ```

4. Cherry-pick the SFW commits you want to merge:
   ```
   git cherry-pick <commit-hash>
   ```

5. Review changes, resolve any conflicts, and commit

6. Merge the branch into your main branch:
   ```
   git checkout main
   git merge merge-sfw
   ```

7. Push the changes to the main repo

This method allows you to selectively merge SFW changes while keeping repositories separate.
