# Habit Tracking App

## Development Phase Contiinous Integration Workflow and Future Contribution Process
There will be three Git repositories involved:

1.  *upstream* - the habit-tracker repository on GitHub.
2.  *origin* - your GitHub fork of `upstream`. This repository
    will typically be at a URL that looks like `https://github.com/paul-offei/habit-tracker`
3.  *local* - your local clone of `origin`

### First time setup

Follow these steps to get ready for making changes to habit-tracker-app.  These
steps are only needed once and not for subsequent changes you might want to
make:

1.  Fork the `habit-tracker` repository on GitHub to create `origin`.
    Visit [habit-tracker](https://github.com/paul-offei/habit-tracker) GitHub repository and click the `Fork` button.

2.  Make a `local` clone of your fork.

    ```shell
    git clone git@github.com:_your_user_name_/habit-tracker.git
    ```

3.  Add a remote pointing from `local` to `upstream`.

    ```shell
    cd habit-tracker
    git remote add upstream git@github.com:paul-offei/habit-tracker.git
    ```
### Making changes

Here is a detailed outline of the steps needed to make changes to habit-tracker.


1. Make a local branch in your clone and pull any recent changes into it.

   ```shell
   git switch -c dev_branch  # Pick a name appropriate to your work
   git pull upstream main
   ```

2. Make changes and commit to local branch.

   ```shell
   # ... editing, testing, ... 
   git commit ...
   ```

3. Pull any changes that may have been made in the upstream repository
   main branch.

   ```shell
   git switch dev_branch
   git pull --rebase upstream main
   ```

   Note that this command may result in merge conflicts. Fix those if
   needed.

4. Push your branch to the corresponding branch in your fork (the `origin` repository).

   ```shell
   git switch dev_branch
   git push origin dev_branch
   ```

5. Select the branch you are working on in the drop-down menu of branches on
   https://github.com/paul-offei/habit-tracker. Then hit the `Compare and pull
   request` button.

   Note: Since for now I'm a solo developer on this project, I basically reject merge request if the CI fails and acept it if it passes manually to keep the main source code clean.  

7. Respond to feedback, which may involve making new commits.
   If you made any changes, push them to github again.

   ```shell
   git switch dev_branch
   git push origin dev_branch
   ```

   Repeat as necessary until all feedback has been handled.

   Note: the preceding approach will cause the pull request to become a sequence
   of commits. Some people like to keep just a single commit that is amended as
   changes are made. If you are amending commits that had already been pushed,
   you will have to add `--force` to the `git push` command above.

8. Once reviewers are happy, pull any main branch changes that may
   have happened since step 3.
   
    ```shell
    git switch dev_branch
    git pull --rebase upstream main
    ```

    If some changes were pulled, push again to the PR, but this time you will
    need to force push since the rebase above will have rewritten your commits.

    ```shell
    git switch dev_branch
    git push --force origin dev_branch
    ```


9.  Ask somebody who has permissions (or do it yourself if you
    have permissions) to merge your branch into the main branch
    of the `upstream` repository. The reviewer may do this without
    being asked.

    Select the `Squash and merge` option on https://github.com/paul-offei/habit-tracker
    or use the command line instructions found on that page. Edit the commit message
    as appropriate for the squashed commit.


10.  Delete the branch from `origin`:

    ```
    git push origin --delete dev_branch
    ```

11. Delete the branch from `local`

    ```
    git switch main
    git branch -D dev_branch
    ```
