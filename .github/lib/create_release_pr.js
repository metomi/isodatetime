/* THIS FILE IS PART OF THE CYLC SUITE ENGINE.
Copyright (C) NIWA & British Crown (Met Office) & Contributors.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>. */

// Create release PR, assigns the dispatcher of the workflow, and attaches milestone if possible

const {execSync, stringify, curlOpts} = require('./util');
const {env} = process;

const milestone = getMilestone();

const milestoneText = () => {
    let checkbox = "[ ]";
    let note = `⚠️ Couldn't find milestone matching \`${env.VERSION}\` `;
    if (milestone) {
        if (parseInt(milestone.open_issues) === 0) {
            checkbox = "[x]";
        }
        note = `\`${milestone.open_issues}\` other open issues/PRs on [milestone ${milestone.title}](https://github.com/${env.REPOSITORY}/milestone/${milestone.number}) at time of PR creation`;
    }
    return `${checkbox} Milestone complete?\n  ${note}`;
};

const bodyText = `
### ⚡ Merging this PR will automatically create a GitHub Release & publish to PyPI ⚡

This PR was created by the \`${env.WORKFLOW}\` workflow, run \`${env.RUN_NUMBER}\`, triggered by @${env.AUTHOR}

#### Tests:
✔️ \`setup.py\` bdist build test
✔️ Version number valid for PyPI.org

#### Checklist:
- ${milestoneText()}

- [ ] Changelog up-to-date?
  Examine pull requests made since the last release
  "Released on" date updated? ${env.CHANGELOG_DATE ? `✔️ \`${env.CHANGELOG_DATE}\`` : `⚠️ couldn't automatically set date`}

- [ ] All contributors listed?

- [ ] \`.mailmap\` file correct?
  In particular, check for duplication

#### Next steps:
- @${env.AUTHOR} should request 1 or 2 reviews
- If any further changes are needed, push to this PR branch
- After merging, the bot will comment below with a link to the release (if not, look at the PR checks tab)
`;

const payload = {
    title: `Prepare release: ${env.VERSION}`,
    head: env.HEAD_REF,
    base: env.BASE_REF,
    body: bodyText
};

const request = `curl -X POST \
    https://api.github.com/repos/${env.REPOSITORY}/pulls \
    -H "authorization: Bearer $GITHUB_TOKEN" \
    -H "content-type: application/json" \
    --data '${stringify(payload)}' \
    ${curlOpts}`;
    // Don't use env.GITHUB_TOKEN above as that might print in log.

const pr = JSON.parse(execSync(request));
setMilestoneAndAssignee(pr.number);



function getMilestone() {
    const request = `curl -X GET \
        https://api.github.com/repos/${env.REPOSITORY}/milestones \
        -H "authorization: Bearer $GITHUB_TOKEN" \
        ${curlOpts}`;

    let response;
    try {
        response = JSON.parse(execSync(request));
    } catch (err) {
        console.log(`::warning:: Error getting milestones`);
        console.log(err, '\n');
        return;
    }
    for (const milestone of response) {
        if (milestone.title.includes(env.VERSION)) {
            console.log('Found milestone:', milestone.title, '\n');
            return milestone;
        }
    }
    console.log(`::warning:: Could not find milestone matching "${env.VERSION}"`);
    return;
}

function setMilestoneAndAssignee(prNumber) {
    // Cannot set them when creating the PR unfortunately
    const payload = {
        milestone: milestone ? milestone.number : undefined,
        assignees: [env.AUTHOR]
    };

    execSync(`curl -X PATCH \
        https://api.github.com/repos/${env.REPOSITORY}/issues/${prNumber} \
        -H "authorization: Bearer $GITHUB_TOKEN" \
        -H "content-type: application/json" \
        --data '${stringify(payload)}' \
        ${curlOpts}`
    );
}
