#!/usr/bin/env zsh

# html-git-workflow.sh - Script to manage HTML file changes in git with pauses

# Function to pause execution until user presses Enter
pause() {
  echo ""
  echo "Press Enter to continue or Ctrl+C to abort..."
  read
}

# Step 1: List all modified and new HTML files
echo "=== STEP 1: Listing modified and new HTML files ==="
echo "Modified HTML files:"
git diff --name-only | grep '\.html$'
echo ""
echo "New (untracked) HTML files:"
git ls-files --others --exclude-standard | grep '\.html$'
pause

# Step 2: Add HTML files to staging
echo "=== STEP 2: Adding HTML files to staging ==="
echo "Adding modified HTML files to staging area..."
git diff --name-only | grep '\.html$' | xargs git add
echo "Adding new HTML files to staging area..."
git ls-files --others --exclude-standard | grep '\.html$' | xargs -r git add
echo "Files now staged:"
git diff --staged --name-only
pause

# Step 3: Commit with custom message
echo "=== STEP 3: Committing changes ==="
echo "Enter your commit message:"
read commit_message
echo "Committing with message: \"$commit_message\""
git commit -m "$commit_message"
pause

# Step 4: Push to remote repository
echo "=== STEP 4: Pushing to remote repository ==="
echo "Pushing to origin main..."
git push origin main
echo "Push complete."
pause

# Step 5: Verify final status
echo "=== STEP 5: Final status check ==="
echo "Current repository status:"
git status
echo "Workflow complete!"